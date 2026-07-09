"""Domain-exception → HTTP-error translation for the transport boundary.

Routers catch domain exceptions and call `http_from_domain(exc)` to raise the
matching HTTPException, keeping the mapping in one place instead of copied into
every router.
"""

from fastapi import HTTPException, status

from common.exceptions import AuthorizationError, NotFoundError, ValidationError


def http_from_domain(exc: Exception) -> HTTPException:
    """Map a domain exception to the matching HTTP error.

    Anything unrecognised is re-raised unchanged so genuine bugs surface as 500s
    rather than being masked.
    """
    if isinstance(exc, NotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, AuthorizationError):
        return HTTPException(status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ValidationError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    raise exc
