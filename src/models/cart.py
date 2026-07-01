"""
Cart domain model.

Decision 1: one logical cart per authenticated user (not per session).
The cart only ever stores product_id + quantity - never a price. Prices
are looked up fresh from the ProductRepository whenever a total needs to
be computed, so the cart can never go stale on price (Assumption 9).
"""

from dataclasses import dataclass, field


@dataclass
class CartItem:
    product_id: int
    quantity: int


@dataclass
class Cart:
    user_id: int
    # Keyed by product_id for O(1) add/update/remove instead of scanning
    # a list on every mutation.
    items: dict[int, CartItem] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return len(self.items) == 0
