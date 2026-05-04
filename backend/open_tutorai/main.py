import os
os.environ["SUPPRESS_WEBUI_BANNER"] = "true"

import open_tutorai.patches
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from open_webui.main import app as webui_app
from open_webui.config import CORS_ALLOW_ORIGIN
from open_webui.models.users import Users

from open_tutorai.config import AppConfig
from open_tutorai.models.database import init_database

# ✅ routers (résolution du conflit ici)
from open_tutorai.routers import (
    response_feedbacks,
    auths,
    supports,
    blockly
)

from open_tutorai.env import CHANGELOG

# Version info
VERSION = "1.0.0"
TUTORAI_BUILD_HASH = os.getenv("TUTORAI_BUILD_HASH", "dev-build")

os.environ["SUPPRESS_WEBUI_BANNER"] = "true"

print(
rf"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ████████╗██╗   ██╗████████╗ ██████╗ ██████╗    █████╗ ██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ╚══██╔══╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗  ██╔══██╗██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║       ██║   ██║   ██║   ██║   ██║   ██║██████╔╝  ███████║██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║       ██║   ██║   ██║   ██║   ██║   ██║██╔══██║  ██╔══██║██║
╚██████╔╝██║     ███████╗██║ ╚████║       ██║   ╚██████╔╝   ██║   ╚██████╔╝██║  ██║  ██║  ██║██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝       ╚═╝    ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝  ╚═╝  ╚═╝╚═╝
v{VERSION} - empowering education through open-source AI tutoring.

{f"Commit: {TUTORAI_BUILD_HASH}" if TUTORAI_BUILD_HASH != "dev-build" else ""}
https://github.com/R2D-dev/open-tutor-ai-CE
"""
)

# Create FastAPI app
app = FastAPI(
    title="Open TutorAI",
    version=VERSION,
)

# CORS config
origins = CORS_ALLOW_ORIGIN
allow_origin_regex = None

if "*" in origins:
    origins = []
    allow_origin_regex = ".*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.config = AppConfig()

# Startup DB
@app.on_event("startup")
async def startup_db_client():
    try:
        init_database()
        print("Support database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database tables: {str(e)}")

# Health check
@app.post("/tutorai/health")
async def health_check():
    return {"status": "okay"}

# Routers
app.include_router(response_feedbacks.router, prefix="/api/v1", tags=["response-feedbacks"])
app.include_router(auths.router, prefix="/auths", tags=["auths"])
app.include_router(supports.router, prefix="/api/v1", tags=["supports"])
app.include_router(blockly.router)

# Changelog
@app.get("/api/changelog")
async def get_app_changelog():
    return {key: CHANGELOG[key] for idx, key in enumerate(CHANGELOG) if idx < 5}

# Mount frontend
app.mount("/", webui_app)