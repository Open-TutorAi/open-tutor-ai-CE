"""OpenTutorAI application entrypoint."""

import os
from gateway.http.app import create_app
from learning.blockly.router import router as blockly_router
# Create FastAPI app
app = create_app()

# ASCII art logo
BANNER = r"""
 ██████╗ ██████╗ ███████╗███╗   ██╗    ████████╗██╗   ██╗████████╗ ██████╗ ██████╗    █████╗ ██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ╚══██╔══╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗  ██╔══██╗██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║       ██║   ██║   ██║   ██║   ██║   ██║██████╔╝  ███████║██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║       ██║   ██║   ██║   ██║   ██║   ██║██╔══██║  ██╔══██║██║
╚██████╔╝██║     ███████╗██║ ╚████║       ██║   ╚██████╔╝   ██║   ╚██████╔╝██║  ██║  ██║  ██║██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝       ╚═╝    ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝  ╚═╝  ╚═╝╚═╝
"""


def main():
    """Console-script entry point — called by `open-tutorai` after pip install."""
    import uvicorn
    from config import settings

    print(BANNER)
    print(
        f"v{settings.APP_VERSION} - empowering education through open-source AI tutoring"
    )
    if settings.BUILD_HASH != "dev-build":
        print(f"Commit: {settings.BUILD_HASH}")
    print("https://github.com/R2D-dev/open-tutor-ai-CE")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
app.include_router(blockly_router)