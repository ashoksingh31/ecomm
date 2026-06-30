"""
Domain-level exceptions.

Services raise these instead of raising HTTPException directly, which
keeps the service layer framework-agnostic (it doesn't know it's being
called from FastAPI). The API layer (src/api/routes/*) is responsible for
catching these and converting them into proper HTTP responses - see
src/api/error_handlers.py.
"""


class DomainError(Exception):
    """Base class for all predictable, business-logic-level errors."""


class NotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class ProductNotFoundError(NotFoundError):
    pass


class CartItemNotFoundError(NotFoundError):
    pass


class OrderNotFoundError(NotFoundError):
    pass


class DiscountCodeNotFoundError(NotFoundError):
    pass


class EmptyCartError(DomainError):
    """Raised when checkout is attempted with no items in the cart."""


class InvalidQuantityError(DomainError):
    """Raised when a requested quantity is <= 0."""


class DiscountCodeAlreadyUsedError(DomainError):
    """Raised when a single-use discount code is redeemed a second time."""


class DiscountCodeNotOwnedError(DomainError):
    """
    Raised when a user tries to redeem a discount code that was awarded
    to a different user (see DECISIONS.md - codes are non-transferable).
    """


class NoNewMilestoneReachedError(DomainError):
    """
    Raised by the admin "generate discount code" endpoint when no new
    Nth-order milestone has been reached since the last code was issued.
    """


class NotAuthorizedError(DomainError):
    """Raised when an authenticated user lacks the required role/claim."""


class InvalidTokenError(DomainError):
    """Raised when a JWT is missing, malformed, or fails verification."""
