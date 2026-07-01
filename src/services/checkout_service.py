"""
Checkout service.

Orchestrates: idempotency check -> cart validation -> price recomputation
-> optional discount validation -> order creation -> cart clearing ->
discount code burn. This is the one place where several decisions from
DECISIONS.md all intersect, so the order of operations matters:

  1. Idempotency check FIRST (Decision 7) - if this idempotency_key was
     already processed, return the original order immediately and touch
     nothing else. This is what makes retries safe.
  2. Recompute every line price from ProductRepository, never trust
     anything the client sent for price (Assumption 9).
  3. Validate the discount code (if any) but only MARK it used after the
     order is durably saved - so a crash between validation and save
     can't burn a code without producing an order.
"""

from src.core.exceptions import EmptyCartError
from src.models.order import Order, OrderLine
from src.repositories.cart_repository import CartRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.services.coupon_service import CouponService


class CheckoutService:
    def __init__(
        self,
        cart_repository: CartRepository,
        product_repository: ProductRepository,
        order_repository: OrderRepository,
        coupon_service: CouponService,
    ):
        self._carts = cart_repository
        self._products = product_repository
        self._orders = order_repository
        self._coupons = coupon_service

    def checkout(self, user_id: int, idempotency_key: str, discount_code: str | None) -> Order:
        # --- 1. Idempotency short-circuit ---
        existing_order = self._orders.get_by_idempotency_key(idempotency_key)
        if existing_order is not None:
            return existing_order

        # --- 2. Validate cart ---
        cart = self._carts.get_or_create(user_id)
        if cart.is_empty():
            raise EmptyCartError("Cannot checkout with an empty cart")

        # --- 3. Recompute prices server-side, build immutable order lines ---
        lines: list[OrderLine] = []
        subtotal = 0.0
        for item in cart.items.values():
            product = self._products.get(item.product_id)  # raises if deleted from catalog
            line = OrderLine(
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=item.quantity,
            )
            lines.append(line)
            subtotal += line.line_total
        subtotal = round(subtotal, 2)

        # --- 4. Validate discount code (does not mark it used yet) ---
        discount_amount = 0.0
        validated_code = None
        if discount_code:
            validated_code = self._coupons.validate_and_get(discount_code, user_id)
            discount_amount = round(subtotal * (validated_code.percentage / 100), 2)

        total = round(subtotal - discount_amount, 2)

        # --- 5. Persist the order ---
        order = Order(
            id=None,  # assigned by OrderRepository.save()
            user_id=user_id,
            sequence_number=self._orders.next_sequence_number(),
            lines=lines,
            subtotal=subtotal,
            discount_code=discount_code,
            discount_amount=discount_amount,
            total=total,
            idempotency_key=idempotency_key,
        )
        self._orders.save(order)

        # --- 6. Only now burn the discount code and clear the cart ---
        if validated_code is not None:
            self._coupons.mark_used(validated_code)
        self._carts.clear(user_id)

        return order
