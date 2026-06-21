"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from config import settings
from data.database import init_database

from .routers import (
    health,
    auth,
    supports,
    guardians as guardians_router,
    classrooms as classrooms_router,
    assignments as assignments_router,
    self_regulation,
    files,
    app_info,
    users,
    configs as configs_router,
    models as models_router,
    providers as providers_router,
    chats as chats_router,
    knowledge as knowledge_router,
    retrieval as retrieval_router,
    audio as audio_router,
    images as images_router,
    tools as tools_router,
    functions as functions_router,
    memories as memories_router,
    prompts as prompts_router,
    channels as channels_router,
    groups as groups_router,
    folders as folders_router,
    tasks as tasks_router,
)
from gateway.http.api_routes import register_api_routes
from gateway.realtime.socket import socket_app

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
    app.include_router(guardians_router.router, prefix="/api/v1")
    app.include_router(classrooms_router.router, prefix="/api/v1")
    app.include_router(assignments_router.router, prefix="/api/v1")

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
