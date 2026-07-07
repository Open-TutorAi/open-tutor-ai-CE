"""Ollama model-management adapter — isolated native API operations.

These operations (pull/create/delete/download/upload) are Ollama-native and
admin-only. Kept separate so the unified proxy core is not polluted by
model-management concerns.
"""

import hashlib
import logging
import os
from typing import AsyncIterator

import httpx

log = logging.getLogger(__name__)

UPLOAD_DIR = "var/uploads"
CHUNK_SIZE = 2 * 1024 * 1024  # 2 MiB


def calculate_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


async def pull_model_stream(url: str, payload: dict) -> AsyncIterator[bytes]:
    """Stream pull progress from Ollama /api/pull."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=5.0)
    ) as client:
        async with client.stream(
            "POST", f"{url}/api/pull", json={**payload, "stream": True}
        ) as r:
            r.raise_for_status()
            async for chunk in r.aiter_bytes():
                yield chunk


async def create_model_stream(url: str, payload: dict) -> AsyncIterator[bytes]:
    """Stream create progress from Ollama /api/create."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=5.0)
    ) as client:
        async with client.stream("POST", f"{url}/api/create", json=payload) as r:
            r.raise_for_status()
            async for chunk in r.aiter_bytes():
                yield chunk


async def delete_model(url: str, model: str) -> bool:
    """Delete model from Ollama backend."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.request("DELETE", f"{url}/api/delete", json={"model": model})
        r.raise_for_status()
    return True


async def upload_model_stream(
    url: str, file_path: str, filename: str
) -> AsyncIterator[bytes]:
    """Upload a local model file to Ollama: hash → push blob → create model.

    Yields SSE-style JSON progress events:
    - {"progress": float, "total": int, "completed": int}  during blob push
    - {"status": "done"}  when finished
    """
    import json as _json

    total_size = os.path.getsize(file_path)
    file_hash = calculate_sha256(file_path)

    # Push the blob
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=600.0, write=600.0, pool=5.0)
    ) as client:
        with open(file_path, "rb") as f:
            blob_data = f.read()
        blob_url = f"{url}/api/blobs/sha256:{file_hash}"
        r = await client.post(blob_url, content=blob_data)
        if not r.is_success:
            raise RuntimeError(f"Ollama blob push failed: {r.status_code} {r.text}")

    yield f'data: {_json.dumps({"progress": 100.0, "total": total_size, "completed": total_size})}\n\n'.encode()

    # Create the model
    model_name, _ = os.path.splitext(filename)
    create_payload = {"model": model_name, "files": {filename: f"sha256:{file_hash}"}}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=5.0)
    ) as client:
        async with client.stream("POST", f"{url}/api/create", json=create_payload) as r:
            r.raise_for_status()
            async for chunk in r.aiter_bytes():
                yield chunk

    try:
        os.remove(file_path)
    except OSError:
        pass
