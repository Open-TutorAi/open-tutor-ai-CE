"""Lightweight server entrypoint used for local development.

Use this module with uvicorn to avoid importing third-party packages named
`main` from site-packages which can shadow the project's `main.py`.

Example:
    uvicorn run:app --reload --host 127.0.0.1 --port 8000

This file intentionally keeps a minimal surface so it's safe to import.
"""

from gateway.http.app import create_app


app = create_app()
