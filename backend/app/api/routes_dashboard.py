from fastapi import APIRouter, Query

from app.services.analytics_service import (
    get_dashboard_summary,
    get_recent_payments,
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def dashboard_summary():
    return get_dashboard_summary()


@router.get("/payments")
def recent_payments(
    limit: int = Query(default=10, ge=1, le=100),
):
    return {
        "payments": get_recent_payments(limit),
    }