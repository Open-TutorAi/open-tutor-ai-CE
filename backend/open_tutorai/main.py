import os

from dotenv import load_dotenv

load_dotenv()
os.environ["SUPPRESS_WEBUI_BANNER"] = "true"
import open_tutorai.patches
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from open_webui.main import app as webui_app
from open_webui.models.users import Users
from open_tutorai.config import AppConfig
from open_tutorai.models.database import init_database

from open_tutorai.routers import response_feedbacks, auths, supports

from open_tutorai.env import (
    CHANGELOG,
)

# Version info
VERSION = "1.0.0"
TUTORAI_BUILD_HASH = os.getenv("TUTORAI_BUILD_HASH", "dev-build")
os.environ["SUPPRESS_WEBUI_BANNER"] = "true"
CORS_ALLOW_ORIGIN = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOW_ORIGIN", "*").replace(",", ";").split(";")
    if origin.strip()
]

print(rf"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ████████╗██╗   ██╗████████╗ ██████╗ ██████╗    █████╗ ██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ╚══██╔══╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗  ██╔══██╗██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║       ██║   ██║   ██║   ██║   ██║   ██║██████╔╝  ███████║██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║       ██║   ██║   ██║   ██║   ██║   ██║██╔══██║  ██╔══██║██║
╚██████╔╝██║     ███████╗██║ ╚████║       ██║   ╚██████╔╝   ██║   ╚██████╔╝██║  ██║  ██║  ██║██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝       ╚═╝    ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝  ╚═╝  ╚═╝╚═╝
v{VERSION} - empowering education through open-source AI tutoring.
{f"Commit: {TUTORAI_BUILD_HASH}" if TUTORAI_BUILD_HASH != "dev-build" else ""}
https://github.com/Open-TutorAi/open-tutor-ai-CE
""")


# Create main FastAPI app
app = FastAPI(
    title="Open TutorAI",
    version=VERSION,
)

# Do not combine wildcard origins with credentialed CORS.
origins = CORS_ALLOW_ORIGIN
allow_origin_regex = None
allow_credentials = True
if "*" in origins:
    origins = ["*"]
    allow_credentials = False
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.config = AppConfig()
# app.state.USER_COUNT = 10


# Initialize the database tables on startup
@app.on_event("startup")
async def startup_db_client():
    """Initialize the database tables when the app starts"""
    try:
        init_database()
        print("Support database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database tables: {str(e)}")


# Health check endpoint
@app.post("/tutorai/health")
async def health_check():
    return {"status": "okay"}


# Include routers of open_tutorai
app.include_router(
    response_feedbacks.router, prefix="/api/v1", tags=["response-feedbacks"]
)
app.include_router(auths.router, prefix="/auths", tags=["auths"])
app.include_router(supports.router, prefix="/api/v1", tags=["supports"])


@app.get("/api/changelog")
async def get_app_changelog():
    return {key: CHANGELOG[key] for idx, key in enumerate(CHANGELOG) if idx < 5}


# Mount the entire OpenWebUI app
app.mount("/", webui_app)
