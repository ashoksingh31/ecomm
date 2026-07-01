"""
Cart routes.

CartItem in the domain model only stores product_id + quantity (see
models/cart.py docstring); this module is responsible for enriching that
with live product name/price when building the API response, so the
domain layer never has to know about the API's shape.
"""

from fastapi import APIRouter, Depends

from src.api.deps import get_cart_service, get_current_user, get_product_service
from src.core.security import TokenPayload
from src.models.cart import Cart
from src.schemas.cart import AddCartItemRequest, CartItemOut, CartOut, UpdateCartItemRequest
from src.services.cart_service import CartService
from src.services.product_service import ProductService

router = APIRouter(prefix="/cart", tags=["Cart"])


def _to_cart_out(cart: Cart, product_service: ProductService) -> CartOut:
    items_out = []
    subtotal = 0.0
    for item in cart.items.values():
        product = product_service.get_product(item.product_id)
        line_total = round(product.price * item.quantity, 2)
        subtotal += line_total
        items_out.append(
            CartItemOut(
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=item.quantity,
                line_total=line_total,
            )
        )
    return CartOut(user_id=cart.user_id, items=items_out, subtotal=round(subtotal, 2))


@router.get("", response_model=CartOut)
def get_cart(
    cart_service: CartService = Depends(get_cart_service),
    product_service: ProductService = Depends(get_product_service),
    user: TokenPayload = Depends(get_current_user),
):
    cart = cart_service.get_cart(user.user_id)
    return _to_cart_out(cart, product_service)


@router.post("/items", response_model=CartOut, status_code=201)
def add_item(
    payload: AddCartItemRequest,
    cart_service: CartService = Depends(get_cart_service),
    product_service: ProductService = Depends(get_product_service),
    user: TokenPayload = Depends(get_current_user),
):
    cart = cart_service.add_item(user.user_id, payload.product_id, payload.quantity)
    return _to_cart_out(cart, product_service)


@router.patch("/items/{product_id}", response_model=CartOut)
def update_item(
    product_id: int,
    payload: UpdateCartItemRequest,
    cart_service: CartService = Depends(get_cart_service),
    product_service: ProductService = Depends(get_product_service),
    user: TokenPayload = Depends(get_current_user),
):
    cart = cart_service.update_item(user.user_id, product_id, payload.quantity)
    return _to_cart_out(cart, product_service)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_item(
    product_id: int,
    cart_service: CartService = Depends(get_cart_service),
    product_service: ProductService = Depends(get_product_service),
    user: TokenPayload = Depends(get_current_user),
):
    cart = cart_service.remove_item(user.user_id, product_id)
    return _to_cart_out(cart, product_service)
