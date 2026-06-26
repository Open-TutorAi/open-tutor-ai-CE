"""Providers router — /api/v1/providers/*

Hermes-style provider core behind the OpenTutorAI provider API contract. This
module exposes the endpoints used by ui/src/lib/apis/{openai,ollama}/index.ts.

Task 1 scope: list + config/urls/keys/verify. Proxy/discovery endpoints are added in
later tasks (see markers below).
"""

import os
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ai.providers.ollama_native import (
    UPLOAD_DIR,
    create_model_stream,
    pull_model_stream,
    upload_model_stream,
)
from ai.providers.ollama_native import (
    delete_model as ollama_delete_model,
)
from ai.providers.proxy import (
    proxy_json,
    proxy_stream,
    resolve_ollama_url,
    resolve_url_key,
)
from ai.providers.service import ProvidersService
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/providers", tags=["providers"])


def get_providers_service(db: Session = Depends(get_db)) -> ProvidersService:
    return ProvidersService(db)


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.get("/")
async def list_providers(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return svc.list_providers()


# ── OpenAI config ──────────────────────────────────────────────────────────────


@router.get("/openai/config")
async def get_openai_config(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return svc.config.get_openai()


@router.post("/openai/config/update")
async def update_openai_config(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return svc.config.set_openai(body)


@router.get("/openai/urls")
async def get_openai_urls(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return {"OPENAI_API_BASE_URLS": svc.config.get_openai()["OPENAI_API_BASE_URLS"]}


@router.post("/openai/urls/update")
async def update_openai_urls(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    cfg = svc.config.set_openai_urls(body.get("urls", []))
    return {"OPENAI_API_BASE_URLS": cfg["OPENAI_API_BASE_URLS"]}


@router.get("/openai/keys")
async def get_openai_keys(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return {"OPENAI_API_KEYS": svc.config.get_openai()["OPENAI_API_KEYS"]}


@router.post("/openai/keys/update")
async def update_openai_keys(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    cfg = svc.config.set_openai_keys(body.get("keys", []))
    return {"OPENAI_API_KEYS": cfg["OPENAI_API_KEYS"]}


@router.post("/openai/verify")
async def verify_openai(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return await svc.verify_openai(body.get("url", ""), body.get("key", ""))


# >>> Task 2 adds here: GET /openai/models, GET /openai/models/{idx},
#     POST /openai/chat/completions, POST /openai/audio/speech

# ── OpenAI proxy ───────────────────────────────────────────────────────────────


@router.get("/openai/models")
async def get_openai_models(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    """Aggregate models from all configured OpenAI-compatible URLs."""
    cfg = svc.config.get_openai()
    if not cfg.get("ENABLE_OPENAI_API"):
        raise HTTPException(status_code=503, detail="OpenAI API is disabled")
    urls: list = cfg.get("OPENAI_API_BASE_URLS") or []
    keys: list = cfg.get("OPENAI_API_KEYS") or []
    all_models: list = []
    for idx, url in enumerate(urls):
        key = keys[idx] if idx < len(keys) else ""
        try:
            data = await proxy_json(url.rstrip("/"), key, "GET", "models")
            for m in data.get("data", []):
                m["urlIdx"] = idx
            all_models.extend(data.get("data", []))
        except HTTPException:
            pass  # skip unreachable upstreams
    return {"data": all_models, "object": "list"}


@router.get("/openai/models/{url_idx}")
async def get_openai_models_by_idx(
    url_idx: int,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_openai()
    if not cfg.get("ENABLE_OPENAI_API"):
        raise HTTPException(status_code=503, detail="OpenAI API is disabled")
    url, key = resolve_url_key(cfg, url_idx)
    return await proxy_json(url, key, "GET", "models")


@router.post("/openai/chat/completions")
async def openai_chat_completions(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_openai()
    if not cfg.get("ENABLE_OPENAI_API"):
        raise HTTPException(status_code=503, detail="OpenAI API is disabled")
    # Route to the URL that owns the requested model (TTL-cached map)
    model_id = body.get("model", "")
    models_map = await svc.openai_models_map()
    url_idx = models_map.get(model_id)  # None → resolve_url_key defaults to index 0
    url, key = resolve_url_key(cfg, url_idx)
    if body.get("stream"):
        return await proxy_stream(url, key, "POST", "chat/completions", body=body)
    return await proxy_json(url, key, "POST", "chat/completions", body=body)


@router.post("/openai/audio/speech")
async def openai_audio_speech(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_openai()
    if not cfg.get("ENABLE_OPENAI_API"):
        raise HTTPException(status_code=503, detail="OpenAI API is disabled")
    url, key = resolve_url_key(cfg)
    return await proxy_stream(url, key, "POST", "audio/speech", body=body)


# ── Ollama config ──────────────────────────────────────────────────────────────


@router.get("/ollama/config")
async def get_ollama_config(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return svc.config.get_ollama()


@router.post("/ollama/config/update")
async def update_ollama_config(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return svc.config.set_ollama(body)


@router.get("/ollama/urls")
async def get_ollama_urls(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return {"OLLAMA_BASE_URLS": svc.config.get_ollama()["OLLAMA_BASE_URLS"]}


@router.post("/ollama/urls/update")
async def update_ollama_urls(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    cfg = svc.config.set_ollama_urls(body.get("urls", []))
    return {"OLLAMA_BASE_URLS": cfg["OLLAMA_BASE_URLS"]}


@router.post("/ollama/verify")
async def verify_ollama(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    return await svc.verify_ollama(body.get("url", ""), body.get("key", ""))


# ── Ollama discovery + chat ────────────────────────────────────────────────────


@router.get("/ollama/api/version")
@router.get("/ollama/api/version/{url_idx}")
async def get_ollama_version(
    url_idx: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        return {"version": False}
    urls: list = cfg.get("OLLAMA_BASE_URLS") or []
    if not urls:
        raise HTTPException(status_code=503, detail="No Ollama URLs configured")
    if url_idx is not None:
        url = resolve_ollama_url(cfg, url_idx)
        return await proxy_json(url, "", "GET", "api/version")
    # Fan-out to all backends, return the lowest available version.
    results = []
    for url in urls:
        try:
            r = await proxy_json(url.rstrip("/"), "", "GET", "api/version")
            results.append(r)
        except Exception:
            pass
    if not results:
        raise HTTPException(status_code=503, detail="No Ollama backends reachable")

    def _ver_tuple(v):
        try:
            return tuple(
                map(int, re.sub(r"^v|-.*", "", v.get("version", "0")).split("."))
            )
        except Exception:
            return (0,)

    lowest = min(results, key=_ver_tuple)
    return {"version": lowest.get("version")}


@router.get("/ollama/api/tags")
@router.get("/ollama/api/tags/{url_idx}")
async def get_ollama_tags(
    url_idx: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        return {"models": []}
    urls: list = cfg.get("OLLAMA_BASE_URLS") or []
    if not urls:
        return {"models": []}
    if url_idx is not None:
        url = resolve_ollama_url(cfg, url_idx)
        return await proxy_json(url, "", "GET", "api/tags")
    # Aggregate across all backends; tag each model with urlIdx
    all_models: list = []
    for idx, url in enumerate(urls):
        try:
            data = await proxy_json(url.rstrip("/"), "", "GET", "api/tags")
            for m in data.get("models", []):
                m["urlIdx"] = idx
            all_models.extend(data.get("models", []))
        except Exception:
            pass
    return {"models": all_models}


@router.post("/ollama/api/generate")
async def ollama_generate(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    model = body.get("model", "")
    models_map = await svc.ollama_models_map()
    url_idx = models_map.get(model)
    url = resolve_ollama_url(cfg, url_idx)
    if body.get("stream", True):  # Ollama streams by default
        return await proxy_stream(url, "", "POST", "api/generate", body=body)
    return await proxy_json(url, "", "POST", "api/generate", body=body)


@router.post("/ollama/api/embeddings")
async def ollama_embeddings(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    model = body.get("model", "")
    models_map = await svc.ollama_models_map()
    url_idx = models_map.get(model)
    url = resolve_ollama_url(cfg, url_idx)
    return await proxy_json(url, "", "POST", "api/embeddings", body=body)


@router.post("/ollama/api/chat")
async def ollama_chat(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    model = body.get("model", "")
    models_map = await svc.ollama_models_map()
    url_idx = models_map.get(model)
    url = resolve_ollama_url(cfg, url_idx)
    if body.get("stream", True):
        return await proxy_stream(url, "", "POST", "api/chat", body=body)
    return await proxy_json(url, "", "POST", "api/chat", body=body)


# ── Ollama UI-friendly aliases ─────────────────────────────────────────────────
# The UI calls /ollama/models and /ollama/chat — these are thin wrappers over
# the native Ollama API endpoints above.


@router.get("/ollama/models")
async def get_ollama_models(
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    """Aggregate Ollama models across all configured backends (UI-friendly alias for /api/tags)."""
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        return {"models": []}
    urls: list = cfg.get("OLLAMA_BASE_URLS") or []
    if not urls:
        return {"models": []}
    all_models: list = []
    for idx, url in enumerate(urls):
        try:
            data = await proxy_json(url.rstrip("/"), "", "GET", "api/tags")
            for m in data.get("models", []):
                m["urlIdx"] = idx
            all_models.extend(data.get("models", []))
        except Exception:
            pass
    return {"models": all_models}


@router.post("/ollama/chat")
async def ollama_chat_alias(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    """UI-friendly chat alias — proxies to /api/chat on the appropriate Ollama backend."""
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    model = body.get("model", "")
    models_map = await svc.ollama_models_map()
    url_idx = models_map.get(model)
    url = resolve_ollama_url(cfg, url_idx)
    if body.get("stream", True):
        return await proxy_stream(url, "", "POST", "api/chat", body=body)
    return await proxy_json(url, "", "POST", "api/chat", body=body)


# >>> Task 4 adds here: /ollama/api/create[/{idx}], /ollama/api/delete[/{idx}],
#     /ollama/api/pull[/{idx}], /ollama/models/download[/{idx}], /ollama/models/upload[/{idx}]

# ── Ollama model management (admin-only isolated adapter) ──────────────────────


@router.post("/ollama/api/pull")
@router.post("/ollama/api/pull/{url_idx}")
async def ollama_pull(
    body: Dict[str, Any],
    url_idx: int = 0,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    url = resolve_ollama_url(cfg, url_idx)
    return StreamingResponse(
        pull_model_stream(url, body), media_type="application/x-ndjson"
    )


@router.post("/ollama/api/create")
@router.post("/ollama/api/create/{url_idx}")
async def ollama_create(
    body: Dict[str, Any],
    url_idx: int = 0,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    url = resolve_ollama_url(cfg, url_idx)
    return StreamingResponse(
        create_model_stream(url, body), media_type="application/x-ndjson"
    )


@router.delete("/ollama/api/delete")
@router.delete("/ollama/api/delete/{url_idx}")
async def ollama_delete(
    body: Dict[str, Any] = Body(...),
    url_idx: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    _require_admin(current_user)
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    model = body.get("model") or body.get("name")
    if not model:
        raise HTTPException(status_code=400, detail="model name required")
    if url_idx is None:
        # Route by model cache
        models_map = await svc.ollama_models_map()
        url_idx = models_map.get(model, 0)
    url = resolve_ollama_url(cfg, url_idx)
    try:
        await ollama_delete_model(url, model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return True


@router.post("/ollama/models/download")
@router.post("/ollama/models/download/{url_idx}")
async def ollama_download(
    body: Dict[str, Any],
    url_idx: int = 0,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    """Download a GGUF model from HuggingFace and register it with Ollama."""
    _require_admin(current_user)
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    file_url = body.get("url", "")
    allowed_hosts = ["https://huggingface.co/", "https://github.com/"]
    if not any(file_url.startswith(h) for h in allowed_hosts):
        raise HTTPException(
            status_code=400, detail="Only HuggingFace and GitHub URLs are allowed"
        )
    url = resolve_ollama_url(cfg, url_idx)
    # Simple pass-through to Ollama's pull with the HuggingFace URL
    return StreamingResponse(
        pull_model_stream(url, {"model": file_url}),
        media_type="application/x-ndjson",
    )


@router.post("/ollama/models/upload")
@router.post("/ollama/models/upload/{url_idx}")
async def ollama_upload(
    file: UploadFile = File(...),
    url_idx: int = 0,
    current_user: User = Depends(get_current_user),
    svc: ProvidersService = Depends(get_providers_service),
):
    """Upload a local GGUF model file and register it with Ollama."""
    _require_admin(current_user)
    cfg = svc.config.get_ollama()
    if not cfg.get("ENABLE_OLLAMA_API"):
        raise HTTPException(status_code=503, detail="Ollama API is disabled")
    url = resolve_ollama_url(cfg, url_idx)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = os.path.basename(file.filename or "model.gguf")
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        while chunk := await file.read(2 * 1024 * 1024):
            f.write(chunk)
    return StreamingResponse(
        upload_model_stream(url, file_path, filename),
        media_type="text/event-stream",
    )
