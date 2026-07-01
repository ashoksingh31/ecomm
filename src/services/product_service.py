"""Product service - thin pass-through since the catalog is read-only."""

from src.models.product import Product
from src.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self._products = product_repository

    def list_products(self) -> list[Product]:
        return self._products.list_all()

    def get_product(self, product_id: int) -> Product:
        return self._products.get(product_id)
