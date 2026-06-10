"""Application settings loaded from environment variables.

Provides a centralized Settings class that loads configuration from environment
variables with sensible defaults. Handles CORS origin configuration with support
for wildcard patterns and concrete origins.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # Load .env before class body reads os.getenv — no-op in CI/Docker

from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    # App metadata
    APP_NAME: str = "OpenTutorAI"
    APP_VERSION: str = "1.0.0"
    BUILD_HASH: str = os.getenv("TUTORAI_BUILD_HASH", "dev-build")

    # API configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("GLOBAL_LOG_LEVEL", "INFO")

    # CORS configuration (no longer from open_webui)
    _cors_origins_str = os.getenv(
        "CORS_ALLOW_ORIGIN", "http://localhost:3000,http://localhost:5173"
    )
    CORS_ORIGINS: tuple = tuple(
        o.strip() for o in _cors_origins_str.split(",") if o.strip()
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: tuple = ("*",)
    CORS_ALLOW_HEADERS: tuple = ("*",)

    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./var/tutorai.db")
    DATABASE_ECHO: bool = DEBUG

    # Auth configuration
    JWT_SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # File upload configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./var/uploads")
    _upload_mb = os.getenv("MAX_UPLOAD_SIZE_MB", "100")
    try:
        MAX_UPLOAD_SIZE_MB: int = int(_upload_mb)
    except ValueError:
        raise ValueError(f"MAX_UPLOAD_SIZE_MB must be a number, got: {_upload_mb}")

    # Vector database / RAG configuration
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./var/vector_db")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Audio/TTS configuration
    AUDIO_TTS_ENGINE: str = os.getenv("AUDIO_TTS_ENGINE", "")
    AUDIO_STT_ENGINE: str = os.getenv("AUDIO_STT_ENGINE", "")

    # Images generation configuration
    IMAGES_ENGINE: str = os.getenv("IMAGES_ENGINE", "")

    @property
    def cors_origin_regex(self) -> Optional[str]:
        """Return regex pattern if using wildcard CORS.

        Returns ".*" if CORS_ORIGINS contains "*" (wildcard), None otherwise.
        Used by FastAPI CORSMiddleware for dynamic origin matching.
        """
        if "*" in self.CORS_ORIGINS:
            return ".*"
        return None

    @property
    def cors_origins_list(self) -> tuple:
        """Return concrete origins list.

        Returns empty tuple if using wildcard CORS (cors_origin_regex handles matching).
        Returns concrete origin list otherwise for FastAPI CORSMiddleware.
        """
        if "*" in self.CORS_ORIGINS:
            return ()
        return self.CORS_ORIGINS


# Validate JWT secret key before instantiation
_jwt_secret = os.getenv("SECRET_KEY", "")
if not _jwt_secret:
    _debug = os.getenv("DEBUG", "false").lower() == "true"
    if not _debug:
        raise ValueError(
            "SECRET_KEY environment variable is required in production. "
            "Do not use default development key in production environments."
        )
    _jwt_secret = "dev-secret-key-change-in-production"
    Settings.JWT_SECRET_KEY = _jwt_secret

# Create singleton instance with validation
settings = Settings()

# Validate production safety
if (
    not settings.DEBUG
    and settings.JWT_SECRET_KEY == "dev-secret-key-change-in-production"
):
    raise ValueError(
        "JWT_SECRET_KEY must be set via SECRET_KEY environment variable in production. "
        "Do not use default development key in production environments."
    )
