from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import response_feedbacks
import os
from open_webui.main import app as webui_app
from open_webui.config import CORS_ALLOW_ORIGIN


# Version info
VERSION = "1.0.0"
WEBUI_BUILD_HASH = os.getenv("WEBUI_BUILD_HASH", "dev-build")

print(
    rf"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ████████╗██╗   ██╗████████╗ ██████╗ ██████╗    █████╗ ██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ╚══██╔══╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗  ██╔══██╗██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║       ██║   ██║   ██║   ██║   ██║   ██║██████╔╝  ███████║██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║       ██║   ██║   ██║   ██║   ██║   ██║██╔══██║  ██╔══██║██║
╚██████╔╝██║     ███████╗██║ ╚████║       ██║   ╚██████╔╝   ██║   ╚██████╔╝██║  ██║  ██║  ██║██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝       ╚═╝    ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝  ╚═╝  ╚═╝╚═╝


v{VERSION} - building the best open-source AI user interface.
{f"Commit: {WEBUI_BUILD_HASH}" if WEBUI_BUILD_HASH != "dev-build" else ""}
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
    allow_origins=CORS_ALLOW_ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/tutorai/health")
async def health_check():
    return {"status": "okkay"}

# Mount the entire OpenWebUI app
app.mount("/", webui_app)

# Include routers of open_tutorai
app.include_router(response_feedbacks.router, prefix="/api/v1", tags=["response-feedbacks"])

