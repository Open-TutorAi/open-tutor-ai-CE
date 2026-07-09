"""Safe file-download responses.

Attachments are stored under user-supplied filenames, so those names must never
be dropped raw into a `Content-Disposition` header: a name containing quotes,
CR/LF, or other control characters could corrupt the header or enable response
splitting. This module centralises the one correct way to serve a download so
every router (resources, assignments, messaging) behaves identically.
"""

import re

from fastapi import Response

# Anything not in this conservative set is stripped from the ASCII fallback name:
# control chars (incl. CR/LF), quotes and backslash — the header-breaking bytes.
_UNSAFE = re.compile(r'[\x00-\x1f\x7f"\\]')


def safe_filename(filename: str | None, default: str = "download") -> str:
    """Return a filename safe to interpolate into a Content-Disposition header."""
    if not filename:
        return default
    # Replace header-unsafe bytes with "_", then trim leading/trailing filler
    # (spaces, dots, and the underscores those unsafe bytes collapsed into) so a
    # trailing "\r\n" becomes a clean name rather than "name__".
    cleaned = _UNSAFE.sub("_", filename).strip(" ._")
    return cleaned or default


def attachment_response(
    data: bytes, content_type: str | None, filename: str | None
) -> Response:
    """A forced-download response (never rendered inline) with a sanitised name.

    `attachment` stops the browser from rendering user-uploaded content in the
    app's origin (stored-XSS defence); the filename is sanitised for the header.
    """
    safe = safe_filename(filename)
    return Response(
        content=data,
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe}"'},
    )
