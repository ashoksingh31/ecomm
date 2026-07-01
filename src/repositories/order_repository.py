"""
Order repository.

Two responsibilities beyond plain storage:

1. Assigning `sequence_number` - the store-wide "this was the Nth order
   ever placed" counter that CouponService uses for milestone detection.
   Derived from the current count rather than a separately-tracked
   counter variable, so there's only one source of truth to keep in sync.

2. Idempotency lookups (Decision 7) - `idempotency_key -> order_id`
   mapping so CheckoutService can detect a retried request and return the
   original order instead of creating a duplicate.
"""

from src.core.exceptions import OrderNotFoundError
from src.models.order import Order


class OrderRepository:
    def __init__(self):
        self._orders: dict[int, Order] = {}
        self._idempotency_index: dict[str, int] = {}  # idempotency_key -> order_id
        self._next_id = 1

    def next_sequence_number(self) -> int:
        """What sequence number the NEXT order to be created would get."""
        return len(self._orders) + 1

    def save(self, order: Order) -> Order:
        order.id = self._next_id
        self._next_id += 1
        self._orders[order.id] = order
        self._idempotency_index[order.idempotency_key] = order.id
        return order

    def get(self, order_id: int) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} does not exist")
        return order

    def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        order_id = self._idempotency_index.get(idempotency_key)
        return self._orders.get(order_id) if order_id is not None else None

    def list_for_user(self, user_id: int) -> list[Order]:
        return [o for o in self._orders.values() if o.user_id == user_id]

    def list_all(self) -> list[Order]:
        return list(self._orders.values())

    def count(self) -> int:
        return len(self._orders)

    def order_at_sequence(self, sequence_number: int) -> Order | None:
        """Used by CouponService to find who placed the Nth order."""
        for order in self._orders.values():
            if order.sequence_number == sequence_number:
                return order
        return None
