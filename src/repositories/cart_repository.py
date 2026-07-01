"""
Cart repository. One Cart per user_id (Decision 1).
"""

from src.models.cart import Cart


class CartRepository:
    def __init__(self):
        self._carts: dict[int, Cart] = {}

    def get_or_create(self, user_id: int) -> Cart:
        if user_id not in self._carts:
            self._carts[user_id] = Cart(user_id=user_id)
        return self._carts[user_id]

    def clear(self, user_id: int) -> None:
        """Empty a user's cart, e.g. right after a successful checkout."""
        if user_id in self._carts:
            self._carts[user_id].items.clear()
