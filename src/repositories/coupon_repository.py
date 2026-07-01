"""
Discount code repository. Owns the `code -> DiscountCode` in-memory map.
"""

from src.core.exceptions import DiscountCodeNotFoundError
from src.models.coupon import DiscountCode


class CouponRepository:
    def __init__(self):
        self._codes: dict[str, DiscountCode] = {}

    def save(self, discount_code: DiscountCode) -> DiscountCode:
        self._codes[discount_code.code] = discount_code
        return discount_code

    def get(self, code: str) -> DiscountCode:
        discount_code = self._codes.get(code)
        if discount_code is None:
            raise DiscountCodeNotFoundError(f"Discount code '{code}' does not exist")
        return discount_code

    def list_all(self) -> list[DiscountCode]:
        return list(self._codes.values())

    def highest_awarded_milestone(self) -> int:
        """
        The largest milestone number for which a code has already been
        generated. 0 if none have been generated yet. Used by
        CouponService to figure out which milestones are still unclaimed.
        """
        if not self._codes:
            return 0
        return max(c.milestone for c in self._codes.values())
