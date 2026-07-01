"""
Discount code domain model.

Generated automatically when a store-wide "Nth order" milestone is
reached (see DECISIONS.md - "Milestone-Based Discount Codes"), never
created ad hoc by an admin. Each code:
  * belongs to exactly one milestone (5th order, 10th order, ...)
  * is redeemable only by the customer who placed the triggering order
  * is single-use
"""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DiscountCode:
    code: str
    owner_user_id: int          # only this user may redeem it
    percentage: float           # e.g. 10.0 == 10% off
    milestone: int              # which multiple of N this corresponds to (1, 2, 3...)
    source_order_id: int        # the order that triggered generation
    is_used: bool = False
    created_at: datetime = None
    used_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
