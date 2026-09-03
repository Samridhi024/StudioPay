from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.customer_service import (
    CustomerPaymentNotFoundError,
    find_customer_payment,
)


router = APIRouter(
    prefix="/api/customer",
    tags=["Customer Portal"],
)


class CustomerPaymentStatusRequest(BaseModel):
    invoice_id: str = Field(
        min_length=2,
        max_length=100,
    )

    customer_email: str = Field(
        min_length=5,
        max_length=255,
    )

    customer_phone: str = Field(
        min_length=8,
        max_length=16,
        pattern=r"^\+[1-9]\d{7,14}$",
        examples=["+919876543210"],
    )


@router.post("/payment-status")
def customer_payment_status(
    request: CustomerPaymentStatusRequest,
):
    try:
        return find_customer_payment(
            invoice_id=request.invoice_id,
            customer_email=request.customer_email,
            customer_phone=request.customer_phone,
        )

    except CustomerPaymentNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=(
                "No payment matched the provided details"
            ),
        ) from error

    except Exception as error:
        print(
            f"Customer payment lookup error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve payment status",
        ) from error