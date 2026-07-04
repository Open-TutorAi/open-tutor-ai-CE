"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
from data.database import init_database
from gateway.http.api_routes import register_api_routes
from gateway.realtime.socket import socket_app

from .routers import (
    app_info,
    auth,
    files,
    health,
    self_regulation,
    supports,
    users,
)
from .routers import (
    audio as audio_router,
)
from .routers import (
    channels as channels_router,
)
from .routers import (
    chats as chats_router,
)
from .routers import (
    configs as configs_router,
)
from .routers import (
    folders as folders_router,
)
from .routers import (
    functions as functions_router,
)
from .routers import (
    groups as groups_router,
)
from .routers import (
    images as images_router,
)
from .routers import (
    knowledge as knowledge_router,
)
from .routers import (
    memories as memories_router,
)
from .routers import (
    models as models_router,
)
from .routers import (
    prompts as prompts_router,
)
from .routers import (
    providers as providers_router,
)
from .routers import (
    retrieval as retrieval_router,
)
from .routers import (
    tasks as tasks_router,
)
from .routers import (
    tools as tools_router,
)

FRONTEND_BUILD_DIR = os.getenv("FRONTEND_BUILD_DIR", "./ui/build")


class SPAStaticFiles(StaticFiles):
    """Serve SvelteKit SPA — fall back to index.html for unknown routes."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                if path.endswith(".js"):
                    raise ex
                return await super().get_response("index.html", scope)
            raise ex


@asynccontextmanager
async def _lifespan(app: FastAPI):
    try:
        init_database()
        print(f"{settings.APP_NAME} v{settings.APP_VERSION} started successfully")
        if settings.BUILD_HASH != "dev-build":
            print(f"Build: {settings.BUILD_HASH}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    @app.middleware("http")
    async def reject_legacy_realtime_path(request: Request, call_next):
        if request.url.path.startswith("/ws/socket.io"):
            return JSONResponse(
                status_code=404,
                content={"detail": "Legacy realtime path disabled"},
            )
        return await call_next(request)

    @app.middleware("http")
    async def csrf_origin_check(request: Request, call_next):
        """CSRF guard for cookie-authenticated state changes.

        The session cookie is attached by the browser automatically, so a
        malicious site could otherwise trigger authenticated mutations. This is
        the second line of defence behind SameSite=Lax on the cookie.

        Scope: only requests authenticated *solely* by the cookie. A request
        also carrying `Authorization: Bearer` is not a CSRF vector (a cross-site
        page cannot set that header without a CORS preflight we control), so
        tests/curl/SDKs are unaffected.

        For a cookie-only unsafe request the `Origin` (or `Referer`) MUST be
        present and match this host or a configured CORS origin — a *missing*
        origin is rejected too, closing the "no Origin header" bypass. The
        expected host honours `X-Forwarded-Proto`/`Host` so the same-origin
        check still works behind a TLS-terminating reverse proxy.

        Auth-establishment endpoints (signin/signup/login) are exempt: they
        don't act on an existing session, so cookie-CSRF doesn't apply.
        """
        is_auth_establish = request.url.path.endswith(("/signin", "/signup", "/login"))
        if (
            request.method not in ("GET", "HEAD", "OPTIONS")
            and not is_auth_establish
            and request.cookies.get(settings.AUTH_COOKIE_NAME)
        ):
            auth = request.headers.get("authorization", "")
            bearer = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
            has_bearer = bearer not in ("", "null", "undefined")
            if not has_bearer:
                origin = request.headers.get("origin")
                if not origin and (referer := request.headers.get("referer")):
                    parsed = urlsplit(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                proto = (
                    request.headers.get("x-forwarded-proto", request.url.scheme)
                    .split(",")[0]
                    .strip()
                )
                host = request.headers.get("x-forwarded-host", request.url.netloc)
                same_origin = f"{proto}://{host}"
                allowed = bool(origin) and (
                    origin in settings.cors_origins_list or origin == same_origin
                )
                if not allowed:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Origin check failed"},
                    )
        return await call_next(request)

    # Health — no version prefix, matches Docker healthcheck and compose
    app.include_router(health.router)

    # Top-level /api/* routes (no version prefix) — UI bootstrap contract
    register_api_routes(app)

    # Auth — mounted at BOTH paths:
    #   /auths/*        → TUTOR_BASE_URL calls (signup, user-count)
    #   /api/v1/auths/* → TUTOR_API_BASE_URL calls (signin, signout, session, …)
    app.include_router(auth.router)
    app.include_router(auth.router, prefix="/api/v1")

    # Supports, evaluations, files — only under /api/v1 (all UI calls use TUTOR_API_BASE_URL)
    app.include_router(supports.router, prefix="/api/v1")
    app.include_router(self_regulation.router, prefix="/api/v1")
    app.include_router(files.router, prefix="/api/v1")
    app.include_router(app_info.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(configs_router.router, prefix="/api/v1")
    app.include_router(models_router.router, prefix="/api/v1")
    app.include_router(providers_router.router, prefix="/api/v1")
    app.include_router(chats_router.router, prefix="/api/v1")
    app.include_router(knowledge_router.router, prefix="/api/v1")
    app.include_router(retrieval_router.router, prefix="/api/v1")
    app.include_router(audio_router.router, prefix="/api/v1")
    app.include_router(images_router.router, prefix="/api/v1")
    app.include_router(tools_router.router, prefix="/api/v1")
    app.include_router(functions_router.router, prefix="/api/v1")
    app.include_router(memories_router.router, prefix="/api/v1")
    app.include_router(prompts_router.router, prefix="/api/v1")
    app.include_router(channels_router.router, prefix="/api/v1")
    app.include_router(groups_router.router, prefix="/api/v1")
    app.include_router(folders_router.router, prefix="/api/v1")
    app.include_router(tasks_router.router, prefix="/api/v1")

    # Socket.IO — mounted at /realtime; client uses path='/realtime/socket.io'
    app.mount("/realtime", socket_app)

    # Serve built frontend last (SPA catch-all must be after all API routes)
    if os.path.exists(FRONTEND_BUILD_DIR):
        app.mount(
            "/",
            SPAStaticFiles(directory=FRONTEND_BUILD_DIR, html=True),
            name="spa-static-files",
        )

    return app
