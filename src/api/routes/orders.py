"""
GET /orders, GET /orders/{id} - order history for the current user.

Note: get_order intentionally checks ownership (a user can't view
someone else's order by guessing an ID) since that's an authorization
concern squarely in scope even though auth itself is not.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_current_user, get_order_repository
from src.core.security import TokenPayload
from src.repositories.order_repository import OrderRepository
from src.schemas.order import OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderOut])
def list_orders(
    repo: OrderRepository = Depends(get_order_repository),
    user: TokenPayload = Depends(get_current_user),
):
    return repo.list_for_user(user.user_id)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    repo: OrderRepository = Depends(get_order_repository),
    user: TokenPayload = Depends(get_current_user),
):
    order = repo.get(order_id)  # raises OrderNotFoundError -> 404
    if order.user_id != user.user_id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
    return order
