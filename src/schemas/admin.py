"""Pydantic schemas for the /admin endpoints."""

from datetime import datetime

from pydantic import BaseModel


class DiscountCodeOut(BaseModel):
    code: str
    owner_user_id: int
    percentage: float
    milestone: int
    source_order_id: int
    is_used: bool
    created_at: datetime
    used_at: datetime | None

    model_config = {"from_attributes": True}


class GenerateDiscountCodesResponse(BaseModel):
    """
    A single admin call can award more than one code if multiple
    milestones elapsed since the last call (see DECISIONS.md - "catch-up"
    generation), so this always returns a list, even when it's length 1.
    """
    generated: list[DiscountCodeOut]


class StatsOut(BaseModel):
    total_orders: int
    total_items_purchased: int
    total_revenue: float
    total_discount_amount: float
    discount_codes: list[DiscountCodeOut]
