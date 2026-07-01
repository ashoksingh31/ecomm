"""
Admin service.

Pure read-side aggregation over OrderRepository + CouponRepository.
Owns no storage of its own - matches the "repositories own state,
services own behaviour" split used everywhere else in this codebase.
"""

from src.repositories.coupon_repository import CouponRepository
from src.repositories.order_repository import OrderRepository


class AdminService:
    def __init__(self, order_repository: OrderRepository, coupon_repository: CouponRepository):
        self._orders = order_repository
        self._coupons = coupon_repository

    def get_stats(self) -> dict:
        orders = self._orders.list_all()

        total_orders = len(orders)
        total_items_purchased = sum(
            line.quantity for order in orders for line in order.lines
        )
        total_revenue = round(sum(order.total for order in orders), 2)
        total_discount_amount = round(sum(order.discount_amount for order in orders), 2)

        return {
            "total_orders": total_orders,
            "total_items_purchased": total_items_purchased,
            "total_revenue": total_revenue,
            "total_discount_amount": total_discount_amount,
            "discount_codes": self._coupons.list_all(),
        }
