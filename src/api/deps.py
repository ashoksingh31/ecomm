"""
Shared FastAPI dependencies.

Two categories:

1. Auth dependencies (get_current_user / require_admin) - pull the JWT
   out of the Authorization header and decode it via src.core.security.
   Per ASSUMPTIONS.md, we trust the claims once the signature checks out;
   there's no session/db lookup.

2. Singleton repository/service providers - repositories are created
   ONCE per process (module-level singletons below) so that in-memory
   state actually persists across requests within the app's lifetime,
   matching Assumption 5 (in-memory persistence, cleared on restart).
   Services are cheap, so we construct them fresh per request, wired to
   the shared repository singletons.
"""

from fastapi import Depends, Header, HTTPException, status

from src.core.exceptions import InvalidTokenError, NotAuthorizedError
from src.core.security import TokenPayload, decode_access_token
from src.repositories.cart_repository import CartRepository
from src.repositories.coupon_repository import CouponRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.services.admin_service import AdminService
from src.services.cart_service import CartService
from src.services.checkout_service import CheckoutService
from src.services.coupon_service import CouponService
from src.services.product_service import ProductService

# --- Process-wide singleton storage (Assumption 4 & 5) ---
_product_repository = ProductRepository()
_cart_repository = CartRepository()
_order_repository = OrderRepository()
_coupon_repository = CouponRepository()


def reset_state() -> None:
    """
    Recreate all in-memory repositories from scratch. Only used by the
    test suite (tests/conftest.py) so each test starts from a clean
    slate instead of leaking cart/order/coupon state into the next test.
    Never called from application code.
    """
    global _product_repository, _cart_repository, _order_repository, _coupon_repository
    _product_repository = ProductRepository()
    _cart_repository = CartRepository()
    _order_repository = OrderRepository()
    _coupon_repository = CouponRepository()


# --- Auth dependencies ---

def get_current_user(authorization: str | None = Header(default=None)) -> TokenPayload:
    """
    Expects `Authorization: Bearer <jwt>`. Every route except the health
    check depends on this - authentication itself is out of scope, but
    authorization based on the token's claims is fully in scope.
    """
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected 'Bearer <token>'.",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        return decode_access_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_admin(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """
    Wrap in a real dependency so FastAPI resolves get_current_user first,
    then this simply re-checks the is_admin claim.
    """
    if not user.is_admin:
        raise NotAuthorizedError("Admin privileges required")
    return user


# --- Repository providers (return the shared singletons) ---

def get_product_repository() -> ProductRepository:
    return _product_repository


def get_cart_repository() -> CartRepository:
    return _cart_repository


def get_order_repository() -> OrderRepository:
    return _order_repository


def get_coupon_repository() -> CouponRepository:
    return _coupon_repository


# --- Service providers (constructed per-request, wired to singletons) ---

def get_product_service() -> ProductService:
    return ProductService(_product_repository)


def get_cart_service() -> CartService:
    return CartService(_cart_repository, _product_repository)


def get_coupon_service() -> CouponService:
    return CouponService(_coupon_repository, _order_repository)


def get_checkout_service() -> CheckoutService:
    return CheckoutService(
        cart_repository=_cart_repository,
        product_repository=_product_repository,
        order_repository=_order_repository,
        coupon_service=get_coupon_service(),
    )


def get_admin_service() -> AdminService:
    return AdminService(_order_repository, _coupon_repository)
