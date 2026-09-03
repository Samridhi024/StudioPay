import json

import razorpay
from fastapi import APIRouter, HTTPException, Request

from app.agent.tools.razorpay_tool import (
    verify_webhook_signature,
)
from app.services.webhook_service import (
    WebhookPayloadError,
    handle_payment_link_paid,
)


router = APIRouter(
    prefix="/api/webhooks",
    tags=["Webhooks"],
)


@router.post("/razorpay")
async def receive_razorpay_webhook(
    request: Request,
):
    request_body = await request.body()

    signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay signature",
        )

    try:
        verify_webhook_signature(
            request_body=request_body,
            signature=signature,
        )

    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay signature",
        )

    try:
        webhook_payload = json.loads(request_body)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        ) from error

    event_type = webhook_payload.get(
        "event",
        "unknown",
    )

    if event_type != "payment_link.paid":
        return {
            "status": "verified",
            "event": event_type,
            "handled": False,
        }

    try:
        result = handle_payment_link_paid(
            webhook_payload
        )

        return {
            "status": "verified",
            "event": event_type,
            **result,
        }

    except WebhookPayloadError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        print(f"Webhook processing error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to process webhook",
        ) from error