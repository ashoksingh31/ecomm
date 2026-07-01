"""
Central mapping from domain exceptions (src.core.exceptions) to HTTP
status codes. Registered once in main.py so route handlers never need
their own try/except HTTPException boilerplate - they just call the
service layer and let domain errors bubble up.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    CartItemNotFoundError,
    DiscountCodeAlreadyUsedError,
    DiscountCodeNotOwnedError,
    DomainError,
    EmptyCartError,
    InvalidQuantityError,
    NoNewMilestoneReachedError,
    NotAuthorizedError,
    NotFoundError,
)

_STATUS_MAP = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    CartItemNotFoundError: status.HTTP_404_NOT_FOUND,
    EmptyCartError: status.HTTP_400_BAD_REQUEST,
    InvalidQuantityError: status.HTTP_400_BAD_REQUEST,
    DiscountCodeAlreadyUsedError: status.HTTP_400_BAD_REQUEST,
    DiscountCodeNotOwnedError: status.HTTP_403_FORBIDDEN,
    NoNewMilestoneReachedError: status.HTTP_409_CONFLICT,
    NotAuthorizedError: status.HTTP_403_FORBIDDEN,
}


def _resolve_status_code(exc: DomainError) -> int:
    for exc_type, code in _STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return code
    return status.HTTP_400_BAD_REQUEST  # sane default for any unmapped DomainError


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=_resolve_status_code(exc), content={"detail": str(exc)})


def register_error_handlers(app):
    app.add_exception_handler(DomainError, domain_error_handler)
