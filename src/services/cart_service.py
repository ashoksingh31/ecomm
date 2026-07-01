"""
Cart service.

Every mutation re-validates the product_id against ProductRepository
(so you can never add a nonexistent product) but deliberately never
checks stock levels - Assumption 3 says inventory is infinite for this
assignment, and Decision 4 says reservation only happens at checkout
time anyway, not at add-to-cart time.
"""

from src.core.exceptions import CartItemNotFoundError, InvalidQuantityError
from src.models.cart import Cart, CartItem
from src.repositories.cart_repository import CartRepository
from src.repositories.product_repository import ProductRepository


class CartService:
    def __init__(self, cart_repository: CartRepository, product_repository: ProductRepository):
        self._carts = cart_repository
        self._products = product_repository

    def get_cart(self, user_id: int) -> Cart:
        return self._carts.get_or_create(user_id)

    def add_item(self, user_id: int, product_id: int, quantity: int) -> Cart:
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be greater than zero")

        # Raises ProductNotFoundError if the product doesn't exist -
        # deliberately not caught here, it bubbles up to the API layer.
        self._products.get(product_id)

        cart = self._carts.get_or_create(user_id)
        if product_id in cart.items:
            # Adding an already-present product increments quantity
            # rather than overwriting it - matches typical "Add to Cart"
            # UX (clicking add twice = 2 units, not 1 unit twice).
            cart.items[product_id].quantity += quantity
        else:
            cart.items[product_id] = CartItem(product_id=product_id, quantity=quantity)
        return cart

    def update_item(self, user_id: int, product_id: int, quantity: int) -> Cart:
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be greater than zero")

        cart = self._carts.get_or_create(user_id)
        if product_id not in cart.items:
            raise CartItemNotFoundError(f"Product {product_id} is not in the cart")

        cart.items[product_id].quantity = quantity
        return cart

    def remove_item(self, user_id: int, product_id: int) -> Cart:
        cart = self._carts.get_or_create(user_id)
        if product_id not in cart.items:
            raise CartItemNotFoundError(f"Product {product_id} is not in the cart")

        del cart.items[product_id]
        return cart

    def compute_subtotal(self, cart: Cart) -> float:
        """
        Estimated total shown in the cart view. Recalculated from current
        catalog prices every time (Assumption 9) - this is intentionally
        an ESTIMATE; checkout recomputes it again from scratch (Decision 5)
        so a stale cart view can never leak into the final charged amount.
        """
        total = 0.0
        for item in cart.items.values():
            product = self._products.get(item.product_id)
            total += product.price * item.quantity
        return round(total, 2)
