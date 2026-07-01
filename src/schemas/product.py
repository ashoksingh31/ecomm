"""Pydantic schemas for the /products endpoints (API-facing, not domain models)."""

from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float

    model_config = {"from_attributes": True}
