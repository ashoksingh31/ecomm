"""POST /checkout - the one write operation that turns a cart into an order."""

from fastapi import APIRouter, Depends

from src.api.deps import get_checkout_service, get_current_user
from src.core.security import TokenPayload
from src.schemas.order import CheckoutRequest, OrderOut
from src.services.checkout_service import CheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post("", response_model=OrderOut, status_code=201)
def checkout(
    payload: CheckoutRequest,
    service: CheckoutService = Depends(get_checkout_service),
    user: TokenPayload = Depends(get_current_user),
):
    return service.checkout(
        user_id=user.user_id,
        idempotency_key=payload.idempotency_key,
        discount_code=payload.discount_code,
    )
