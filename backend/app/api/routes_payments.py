from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.services.payment_ingestion_service import (
    DuplicateInvoiceError,
    VendorNotFoundError,
    create_payment_record,
    get_available_vendors,
)
from app.services.recovery_execution_service import (
    PaymentNotFoundError,
    RecoveryActionNotAllowedError,
    execute_payment_link_recovery,
    record_manual_review,
    schedule_smart_retry,
)


router = APIRouter(
    prefix="/api/payments",
    tags=["Payment Recovery"],
)


class CreatePaymentRequest(BaseModel):
    # Unknown fields will now cause validation errors
    # instead of being silently discarded.
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    vendor_id: UUID

    invoice_id: str = Field(
        min_length=2,
        max_length=100,
    )

    customer_name: str = Field(
        min_length=2,
        max_length=150,
    )

    customer_email: str = Field(
        min_length=5,
        max_length=255,
    )

    customer_phone: str = Field(
        min_length=8,
        max_length=16,
        pattern=r"^\+[1-9]\d{7,14}$",
    )

    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        pattern=r"^[A-Za-z]{3}$",
    )

    status: Literal[
        "paid",
        "failed",
        "pending",
        "recovered",
    ] = "failed"

    failure_code: str = Field(
        default="",
        max_length=100,
    )

    failure_reason: str = Field(
        default="",
        max_length=500,
    )

    attempt_count: int = Field(
        default=1,
        ge=0,
        le=255,
    )

    payment_date: datetime | None = None


class ManualReviewRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    approved: bool

    reviewer: str = Field(
        min_length=2,
        max_length=100,
    )


@router.get("/vendors")
def list_vendors():
    try:
        return {
            "vendors": get_available_vendors(),
        }

    except Exception as error:
        print(f"Vendor-list error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve vendors",
        ) from error


@router.post("")
def create_payment(
    request: CreatePaymentRequest,
):
    try:
        # model_dump includes customer_phone.
        return create_payment_record(
            payment_data=request.model_dump()
        )

    except VendorNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except DuplicateInvoiceError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        print(f"Payment-creation error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to create payment",
        ) from error


@router.post("/{payment_id}/payment-link")
def create_recovery_link(
    payment_id: UUID,
):
    try:
        return execute_payment_link_recovery(
            str(payment_id)
        )

    except PaymentNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except RecoveryActionNotAllowedError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except Exception as error:
        print(
            f"Razorpay payment-link error: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to create Razorpay "
                "payment link"
            ),
        ) from error


@router.post("/{payment_id}/smart-retry")
def create_smart_retry(
    payment_id: UUID,
):
    try:
        return schedule_smart_retry(
            str(payment_id)
        )

    except PaymentNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except RecoveryActionNotAllowedError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except Exception as error:
        print(f"Smart-retry error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to schedule smart retry",
        ) from error


@router.post("/{payment_id}/manual-review")
def submit_manual_review(
    payment_id: UUID,
    request: ManualReviewRequest,
):
    try:
        return record_manual_review(
            payment_id=str(payment_id),
            approved=request.approved,
            reviewer=request.reviewer,
        )

    except PaymentNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except RecoveryActionNotAllowedError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except Exception as error:
        print(f"Manual-review error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to record manual review",
        ) from error