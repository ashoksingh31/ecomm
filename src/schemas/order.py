"""Pydantic schemas for /checkout and /orders endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    # Decision 7 - Idempotent Checkout: caller supplies a client-generated
    # key (e.g. a UUID); retrying with the same key returns the original
    # order instead of creating a duplicate one.
    idempotency_key: str = Field(min_length=1)
    discount_code: str | None = None


class OrderLineOut(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    user_id: int
    sequence_number: int
    lines: list[OrderLineOut]
    subtotal: float
    discount_code: str | None
    discount_amount: float
    total: float
    created_at: datetime

    model_config = {"from_attributes": True}
