"""Top-level /api/* routes registered directly on the FastAPI app object.

These are called by the UI before authentication (getBackendConfig) and after
(getModels, getChangelog). They define the OpenTutorAI bootstrap contract used
by the SvelteKit frontend.

Usage:
    from gateway.http.api_routes import register_api_routes
    register_api_routes(app)
"""

import json
import logging
from typing import Any, Dict

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from ai.media.images import ImagesService
from ai.model_catalog.service import ModelsService
from ai.providers.proxy import proxy_json
from ai.providers.service import ProvidersService, build_llm_body
from config import settings
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from system.configs.service import ConfigsService

log = logging.getLogger(__name__)


# ── Private gateway-layer helper ─────────────────────────────────────────────


async def _stream_to_socket(
    llm_body: Dict[str, Any],
    base_url: str,
    api_key: str,
    path: str,
    user_id: str,
    chat_id: str,
    message_id: str,
) -> None:
    """Stream LLM SSE response as Socket.IO chat-events to the user's room.

    Imports emit_chat_event locally to keep the gateway layer import at
    call-time (avoids circular imports at module load).
    """
    from gateway.realtime.socket import emit_chat_event

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    url = f"{base_url}/{path.lstrip('/')}"

    async def _emit(data: dict) -> None:
        await emit_chat_event(
            user_id,
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "data": {"type": "chat:completion", "data": data},
            },
        )

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=5.0)
        ) as client:
            async with client.stream(
                "POST", url, json=llm_body, headers=headers
            ) as response:
                if response.status_code >= 400:
                    await response.aread()
                    await _emit({"error": {"message": response.text}, "done": True})
                    return
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except Exception:
                        log.debug("SSE parse error, skipping line: %r", payload)
                        continue
                    await _emit({**chunk, "done": False})

        await _emit({"done": True, "id": message_id})
    except Exception as exc:
        await _emit({"error": {"message": str(exc)}, "done": True})


async def _chat_completions_handler(
    body: Dict[str, Any],
    user: Any,
    db: Any,
    background_tasks: BackgroundTasks,
) -> Any:
    """Shared handler for both /api/chat/completions endpoints.

    Non-streaming: returns LLM JSON response directly.
    Streaming: fires a background task that delivers tokens via Socket.IO
    and returns an immediate acknowledgement to the client.
    """
    from gateway.realtime.socket import SESSION_POOL

    model_id: str = body.get("model", "")
    session_id: str = body.get("session_id", "")
    chat_id: str = body.get("chat_id", "")
    message_id: str = body.get("id", "")
    is_stream: bool = body.get("stream", True)

    base_url, api_key, path = await ProvidersService(db).resolve_provider(model_id)

    llm_body = build_llm_body(body)

    if not is_stream:
        return await proxy_json(base_url, api_key, "POST", path, body=llm_body)

    # Resolve socket target: prefer session_id lookup, fall back to user.id
    session_info = SESSION_POOL.get(session_id, {})
    target_user_id = session_info.get("user_id") or user.id

    background_tasks.add_task(
        _stream_to_socket,
        llm_body,
        base_url,
        api_key,
        path,
        target_user_id,
        chat_id,
        message_id,
    )

    return {"id": message_id, "object": "chat.completion.start", "model": model_id}


# ── Route registration ────────────────────────────────────────────────────────


def register_api_routes(app: FastAPI) -> None:
    """Register all /api/* routes directly on the FastAPI app instance."""

    # ── /api/config ───────────────────────────────────────────────────────────

    @app.get("/api/config")
    def get_backend_config(db: Session = Depends(get_db)):
        """Bootstrap config read by the UI before the user logs in."""
        images_cfg = ImagesService(db).get_config()
        models_cfg = ConfigsService(db).get("models") or {}
        return {
            "status": True,
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "default_locale": "en-US",
            "default_models": models_cfg.get("DEFAULT_MODELS", ""),
            "default_prompt_suggestions": [],
            "features": {
                "auth": True,
                "auth_trusted_header": False,
                "enable_api_key": True,
                "enable_signup": True,
                "enable_login_form": True,
                "enable_web_search": False,
                "enable_google_drive_integration": False,
                "enable_image_generation": bool(images_cfg.get("enabled")),
                "enable_admin_export": True,
                "enable_admin_chat_access": True,
                "enable_community_sharing": False,
                "enable_autocomplete_generation": False,
                "enable_websocket": True,
            },
            "oauth": {"providers": {}},
            "audio": {
                "stt": {
                    "engine": "",
                },
                "tts": {
                    "engine": "",
                    "voice": "",
                    "split_on": "punctuation",
                    "auto_playback": False,
                },
            },
        }

    # ── /api/models ───────────────────────────────────────────────────────────

    @app.get("/api/models")
    async def get_models(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        """Return merged models from all providers + DB custom models.

        The UI does `res?.data ?? []` so the {data:[...]} envelope is required.
        """
        models = await ProvidersService(db).get_merged_models()
        return {"data": models}

    @app.get("/api/models/base")
    def get_base_models(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        models = ModelsService(db).list_base()
        return {"data": models if isinstance(models, list) else []}

    # ── /api/chat/completions ─────────────────────────────────────────────────

    @app.post("/api/chat/completions")
    async def chat_completions(
        body: Dict[str, Any],
        background_tasks: BackgroundTasks,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        """Unified chat endpoint — routes to Ollama or OpenAI, streams via Socket.IO."""
        return await _chat_completions_handler(body, user, db, background_tasks)

    @app.post("/api/v1/chat/completions")
    async def chat_completions_v1(
        body: Dict[str, Any],
        background_tasks: BackgroundTasks,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        """Alias for /api/chat/completions with /v1 prefix."""
        return await _chat_completions_handler(body, user, db, background_tasks)

    # ── Stub routes ───────────────────────────────────────────────────────────

    @app.get("/api/changelog")
    def get_changelog():
        return {}

    @app.get("/api/version/updates")
    def get_version_updates():
        return {"current": settings.APP_VERSION, "latest": settings.APP_VERSION}

    @app.get("/api/config/model/filter")
    def get_model_filter(user: User = Depends(get_current_user)):
        return {"enabled": False, "models": []}

    @app.post("/api/config/model/filter")
    def update_model_filter(
        body: Dict[str, Any], user: User = Depends(get_current_user)
    ):
        raise HTTPException(status_code=501, detail="not implemented")

    @app.get("/api/config/models")
    def get_models_config(user: User = Depends(get_current_user)):
        return {"models": []}

    @app.post("/api/config/models")
    def update_models_config(
        body: Dict[str, Any], user: User = Depends(get_current_user)
    ):
        raise HTTPException(status_code=501, detail="not implemented")

    @app.get("/api/webhook")
    def get_webhook(user: User = Depends(get_current_user)):
        return {"url": ""}

    @app.post("/api/webhook")
    def update_webhook(body: Dict[str, Any], user: User = Depends(get_current_user)):
        return body

    @app.get("/api/community_sharing")
    def get_community_sharing(user: User = Depends(get_current_user)):
        return False

    @app.post("/api/community_sharing/toggle")
    def toggle_community_sharing(user: User = Depends(get_current_user)):
        return False

    @app.post("/api/tasks/stop/{task_id}")
    def stop_task(task_id: str, user: User = Depends(get_current_user)):
        return {"stopped": False, "detail": "not implemented"}
