"""
Discount code service.

Implements the "every Nth order" business rule end to end:

  * generate_new_milestone_codes() - called from the admin endpoint.
    Compares how many milestones (multiples of N) have been REACHED
    (based on total orders placed) against how many have already been
    AWARDED a code, and mints one code per unclaimed milestone. This
    "catch-up" behaviour (awarding more than one at once if the admin
    hasn't called the endpoint in a while) is a deliberate design choice
    documented in DECISIONS.md - we never want a customer who genuinely
    hit a milestone to silently lose their code just because nobody
    called the generate endpoint in time.

  * validate_and_get() / mark_used() - used by CheckoutService to
    redeem a code. Enforces: exists, owned by the redeeming user, not
    already used (single-use, per your decision).
"""

import secrets
import string
from datetime import datetime, timezone

from src.config.settings import settings
from src.core.exceptions import (
    DiscountCodeAlreadyUsedError,
    DiscountCodeNotOwnedError,
    NoNewMilestoneReachedError,
)
from src.models.coupon import DiscountCode
from src.repositories.coupon_repository import CouponRepository
from src.repositories.order_repository import OrderRepository


def _generate_code(length: int = 10) -> str:
    """Random, human-typeable discount code, e.g. 'A3F9K2QZP1'."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class CouponService:
    def __init__(self, coupon_repository: CouponRepository, order_repository: OrderRepository):
        self._coupons = coupon_repository
        self._orders = order_repository

    def generate_new_milestone_codes(self) -> list[DiscountCode]:
        interval = settings.milestone_interval
        total_orders = self._orders.count()

        highest_reached = total_orders // interval           # milestones REACHED so far
        highest_awarded = self._coupons.highest_awarded_milestone()  # milestones already CODED

        if highest_reached <= highest_awarded:
            raise NoNewMilestoneReachedError(
                f"No new milestone reached yet. {interval - (total_orders % interval)} "
                f"more order(s) needed for the next discount code."
            )

        newly_generated: list[DiscountCode] = []
        # Award every unclaimed milestone in between, not just the latest
        # one - see module docstring.
        for milestone in range(highest_awarded + 1, highest_reached + 1):
            triggering_sequence_number = milestone * interval
            triggering_order = self._orders.order_at_sequence(triggering_sequence_number)
            if triggering_order is None:
                # Defensive guard only; shouldn't happen since
                # highest_reached is derived from total_orders itself.
                continue

            discount_code = DiscountCode(
                code=_generate_code(),
                owner_user_id=triggering_order.user_id,
                percentage=settings.milestone_discount_percentage,
                milestone=milestone,
                source_order_id=triggering_order.id,
            )
            self._coupons.save(discount_code)
            newly_generated.append(discount_code)

        return newly_generated

    def validate_and_get(self, code: str, user_id: int) -> DiscountCode:
        """
        Raises DiscountCodeNotFoundError (from the repository),
        DiscountCodeNotOwnedError, or DiscountCodeAlreadyUsedError.
        Does NOT mark the code used - that only happens after the order
        is successfully created, see CheckoutService.
        """
        discount_code = self._coupons.get(code)

        if discount_code.owner_user_id != user_id:
            raise DiscountCodeNotOwnedError("This discount code was not issued to you")

        if discount_code.is_used:
            raise DiscountCodeAlreadyUsedError("This discount code has already been used")

        return discount_code

    def mark_used(self, discount_code: DiscountCode) -> None:
        discount_code.is_used = True
        discount_code.used_at = datetime.now(timezone.utc)
        self._coupons.save(discount_code)

    def list_all(self) -> list[DiscountCode]:
        return self._coupons.list_all()
