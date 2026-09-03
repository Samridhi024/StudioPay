from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.services.policy_service import (
    evaluate_payment,
    get_payment,
    get_recovery_recommendations,
)


router = APIRouter(
    prefix="/api/policy",
    tags=["Recovery Policy"],
)


@router.get("/recommendations")
def recovery_recommendations():
    recommendations = get_recovery_recommendations()

    return {
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@router.get("/evaluate/{payment_id}")
def evaluate_single_payment(payment_id: UUID):
    payment = get_payment(str(payment_id))

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return {
        "payment": payment,
        "decision": evaluate_payment(payment),
    }