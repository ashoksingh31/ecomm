"""Pydantic schemas for the /cart endpoints."""

from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, description="Must be a positive integer")


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(gt=0, description="Must be a positive integer")


class CartItemOut(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float


class CartOut(BaseModel):
    user_id: int
    items: list[CartItemOut]
    subtotal: float
