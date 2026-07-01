"""
Order domain model.

Decision 6 - Immutable Order Snapshots: an order line stores the product
NAME and PRICE at time of purchase, not just a product_id, so historical
orders stay accurate even if the catalog changes later.

Decision 7 - Idempotent Checkout: `idempotency_key` is stored on the
order so retried checkout requests can be detected and short-circuited
by OrderRepository.get_by_idempotency_key() instead of creating a
duplicate order.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class OrderLine:
    product_id: int
    product_name: str
    unit_price: float
    quantity: int

    @property
    def line_total(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class Order:
    id: int
    user_id: int
    # Store-wide position of this order (1st, 2nd, 3rd order ever placed).
    # This is what milestone detection is based on - see CouponService.
    sequence_number: int
    lines: list[OrderLine]
    subtotal: float
    discount_code: str | None
    discount_amount: float
    total: float
    idempotency_key: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
