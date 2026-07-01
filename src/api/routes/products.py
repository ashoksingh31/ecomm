"""GET /products, GET /products/{id} - read-only catalog browsing."""

from fastapi import APIRouter, Depends

from src.api.deps import get_current_user, get_product_service
from src.core.security import TokenPayload
from src.schemas.product import ProductOut
from src.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    service: ProductService = Depends(get_product_service),
    _user: TokenPayload = Depends(get_current_user),
):
    return service.list_products()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    _user: TokenPayload = Depends(get_current_user),
):
    return service.get_product(product_id)
