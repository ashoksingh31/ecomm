"""
Product repository.

Owns its own in-memory dict (Decision - each repository owns its own
storage, rather than sharing one generic memory_store.py). Preloaded with
sample data at construction time because Assumption 2 says the catalog
already exists before this application starts - this app never writes
to it.
"""

from src.core.exceptions import ProductNotFoundError
from src.models.product import Product


class ProductRepository:
    def __init__(self):
        self._products: dict[int, Product] = {}
        self._seed()

    def _seed(self):
        """Preload a small fixed catalog so the app is usable out of the box."""
        seed_data = [
            (1, "Wireless Mouse", "Ergonomic 2.4GHz wireless mouse", 19.99),
            (2, "Mechanical Keyboard", "Hot-swappable mechanical keyboard", 79.99),
            (3, "USB-C Hub", "7-in-1 USB-C hub with HDMI", 34.50),
            (4, "27-inch Monitor", "1440p IPS monitor, 144Hz", 249.00),
            (5, "Laptop Stand", "Adjustable aluminium laptop stand", 29.95),
            (6, "Webcam 1080p", "Full HD webcam with autofocus", 45.00),
            (7, "Noise Cancelling Headphones", "Over-ear ANC headphones", 129.99),
            (8, "Desk Mat", "Extended waterproof desk mat", 15.00),
        ]
        for product_id, name, description, price in seed_data:
            self._products[product_id] = Product(product_id, name, description, price)

    def list_all(self) -> list[Product]:
        return list(self._products.values())

    def get(self, product_id: int) -> Product:
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} does not exist")
        return product

    def exists(self, product_id: int) -> bool:
        return product_id in self._products
