from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from open_webui.main import app as webui_app
from open_webui.config import CORS_ALLOW_ORIGIN
from open_webui.models.users import UserModel, Users
from open_webui.models.users import Users


from open_tutorai.routers import (
    response_feedbacks,
    auths,
)
from open_tutorai.config import (AppConfig)
# Version info
VERSION = "1.0.0"
TUTORAI_BUILD_HASH = os.getenv("TUTORAI_BUILD_HASH", "dev-build")

print(
    rf"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ████████╗██╗   ██╗████████╗ ██████╗ ██████╗    █████╗ ██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ╚══██╔══╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗  ██╔══██╗██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║       ██║   ██║   ██║   ██║   ██║   ██║██████╔╝  ███████║██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║       ██║   ██║   ██║   ██║   ██║   ██║██╔══██║  ██╔══██║██║
╚██████╔╝██║     ███████╗██║ ╚████║       ██║   ╚██████╔╝   ██║   ╚██████╔╝██║  ██║  ██║  ██║██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝       ╚═╝    ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝  ╚═╝  ╚═╝╚═╝
v{VERSION} - building the best open-source AI user interface.

{f"Commit: {TUTORAI_BUILD_HASH}" if TUTORAI_BUILD_HASH != "dev-build" else ""}
https://github.com/open-tutor-ai/open-tutor-ai
"""
)

# Create main FastAPI app
app = FastAPI(
    title="Open TutorAI",
    version=VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.config = AppConfig()
app.state.USER_COUNT = 100  # or whatever user cap you want



# Health check endpoint
@app.post("/tutorai/health")
async def health_check():
    return {"status": "okkady"}

# Include routers of open_tutorai
app.include_router(response_feedbacks.router, prefix="/api/v1", tags=["response-feedbacks"])
app.include_router(auths.router, prefix="/auths", tags=["auths"])


# Mount the entire OpenWebUI app
app.mount("/", webui_app)





