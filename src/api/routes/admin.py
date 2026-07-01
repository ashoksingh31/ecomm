"""
POST /admin/discount-codes/generate, GET /admin/stats

Both require the is_admin claim (Decision 2 - JWT-based authorization
using claims, no extra DB lookup).
"""

from fastapi import APIRouter, Depends

from src.api.deps import get_admin_service, get_coupon_service, require_admin
from src.core.security import TokenPayload
from src.schemas.admin import GenerateDiscountCodesResponse, StatsOut
from src.services.admin_service import AdminService
from src.services.coupon_service import CouponService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/discount-codes/generate", response_model=GenerateDiscountCodesResponse)
def generate_discount_codes(
    service: CouponService = Depends(get_coupon_service),
    _admin: TokenPayload = Depends(require_admin),
):
    # Raises NoNewMilestoneReachedError -> 409 if nothing new to award.
    generated = service.generate_new_milestone_codes()
    return GenerateDiscountCodesResponse(generated=generated)


@router.get("/stats", response_model=StatsOut)
def get_stats(
    service: AdminService = Depends(get_admin_service),
    _admin: TokenPayload = Depends(require_admin),
):
    return service.get_stats()
