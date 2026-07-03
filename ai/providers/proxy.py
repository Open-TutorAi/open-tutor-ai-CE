"""Unified async httpx proxy helpers for OpenAI-compatible providers."""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

log = logging.getLogger(__name__)

TIMEOUT_DEFAULT = 120.0
TIMEOUT_STREAM = 300.0


def _auth_headers(key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {key}"} if key else {}


def resolve_url_key(cfg: Dict[str, Any], idx: Optional[int] = None) -> Tuple[str, str]:
    """Return (base_url, api_key) for the given index, or index 0 if idx is None."""
    urls: List[str] = (
        cfg.get("OPENAI_API_BASE_URLS") or cfg.get("OLLAMA_BASE_URLS") or []
    )
    keys: List[str] = cfg.get("OPENAI_API_KEYS", [])
    if not urls:
        raise HTTPException(status_code=503, detail="No upstream URLs configured")
    i = idx if idx is not None else 0
    if i >= len(urls):
        raise HTTPException(status_code=404, detail=f"URL index {i} out of range")
    url = urls[i].rstrip("/")
    key = keys[i] if i < len(keys) else ""
    return url, key


def resolve_ollama_url(cfg: Dict[str, Any], idx: Optional[int] = None) -> str:
    """Return base_url for the given Ollama URL index (no API key for Ollama)."""
    urls: List[str] = cfg.get("OLLAMA_BASE_URLS") or []
    if not urls:
        raise HTTPException(status_code=503, detail="No Ollama URLs configured")
    i = idx if idx is not None else 0
    if i >= len(urls):
        raise HTTPException(status_code=404, detail=f"URL index {i} out of range")
    return urls[i].rstrip("/")


async def proxy_json(
    base_url: str,
    key: str,
    method: str,
    path: str,
    body: Optional[Any] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    timeout: float = TIMEOUT_DEFAULT,
) -> Any:
    """Proxy a JSON request. Returns parsed response body. Raises HTTPException on error."""
    headers = {**_auth_headers(key), **(extra_headers or {})}
    url = f"{base_url}/{path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.request(method, url, json=body, headers=headers)
            if r.status_code >= 400:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
                raise HTTPException(status_code=r.status_code, detail=detail)
            return r.json()
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("Proxy error %s %s: %s", method, url, exc)
        raise HTTPException(status_code=502, detail=f"Upstream unreachable: {exc}")


async def proxy_stream(
    base_url: str,
    key: str,
    method: str,
    path: str,
    body: Optional[Any] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> StreamingResponse:
    """Eagerly connect, check upstream status, then stream bytes.

    Opens the connection before returning to the router, so upstream 4xx/5xx
    raises HTTPException synchronously (before 200 is committed to the client).
    """
    headers = {**_auth_headers(key), **(extra_headers or {})}
    url = f"{base_url}/{path.lstrip('/')}"

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=TIMEOUT_STREAM, write=30.0, pool=5.0)
    )
    try:
        request = client.build_request(method, url, json=body, headers=headers)
        response = await client.send(request, stream=True)
        if response.status_code >= 400:
            await response.aread()
            error_text = response.text
            await client.aclose()
            raise HTTPException(status_code=response.status_code, detail=error_text)
    except HTTPException:
        raise
    except Exception as exc:
        await client.aclose()
        log.warning("Proxy stream error %s %s: %s", method, url, exc)
        raise HTTPException(status_code=502, detail=f"Upstream unreachable: {exc}")

    content_type = response.headers.get("content-type", "application/octet-stream")

    async def _stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        finally:
            await response.aclose()
            await client.aclose()

    return StreamingResponse(_stream(), media_type=content_type)
