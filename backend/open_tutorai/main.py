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
from open_tutorai.env import CHANGELOG

# ============ VERSION INFO ============
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
v{VERSION} - empowering education through open-source AI tutoring.

{f"Commit: {TUTORAI_BUILD_HASH}" if TUTORAI_BUILD_HASH != "dev-build" else ""}
https://github.com/R2D-dev/open-tutor-ai-CE
"""
)

# ============ CRÉER L'APP ============
app = FastAPI(
    title="Open TutorAI",
    version=VERSION,
)

# ============ AJOUTER LES MIDDLEWARES ============
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

# ============ STARTUP EVENT ============
@app.on_event("startup")
async def startup_db_client():
    """Initialize the database tables when the app starts"""
    try:
        init_database()
        print("Support database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database tables: {str(e)}")

# ============ HEALTH CHECK ============
@app.post("/tutorai/health")
async def health_check():
    return {"status": "okay"}

# ============ DEBUG — AFFICHER TOUTES LES ROUTES (AVANT MOUNT) ============
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "methods": list(getattr(route, "methods", ["GET"])),
        })
    return {"total_routes": len(routes), "routes": routes}

# ============ IMPORT ET AJOUTER LES ROUTERS ============
print("\n" + "="*60)
print("CHARGEMENT DES ROUTERS")
print("="*60 + "\n")

try:
    print("📥 Chargement de response_feedbacks...")
    from open_tutorai.routers.response_feedbacks import router as response_feedbacks_router
    app.include_router(response_feedbacks_router, prefix="/api/v1", tags=["response-feedbacks"])
    print("✅ response_feedbacks OK\n")
except Exception as e:
    print(f"❌ Erreur response_feedbacks: {e}\n")
    import traceback
    traceback.print_exc()

try:
    print("📥 Chargement de auths...")
    from open_tutorai.routers.auths import router as auths_router
    app.include_router(auths_router, prefix="/auths", tags=["auths"])
    print("✅ auths OK\n")
except Exception as e:
    print(f"❌ Erreur auths: {e}\n")
    import traceback
    traceback.print_exc()

try:
    print("📥 Chargement de supports...")
    from open_tutorai.routers.supports import router as supports_router
    app.include_router(supports_router, prefix="/api/v1", tags=["supports"])
    print("✅ supports OK\n")
except Exception as e:
    print(f"❌ Erreur supports: {e}\n")
    import traceback
    traceback.print_exc()

try:
    print("📥 Chargement de python_executor...")
    from open_tutorai.routers.python_executor import router as python_executor_router
    app.include_router(python_executor_router)
    print("✅ python_executor OK\n")
except Exception as e:
    print(f"❌ Erreur python_executor: {e}\n")
    import traceback
    traceback.print_exc()

print("="*60)
print("CHARGEMENT TERMINÉ")
print("="*60 + "\n")

# ============ CHANGELOG ENDPOINT ============
@app.get("/api/changelog")
async def get_app_changelog():
    return {key: CHANGELOG[key] for idx, key in enumerate(CHANGELOG) if idx < 5}

# ============ MOUNT WEBUI (EN DERNIER) ============
app.mount("/", webui_app)