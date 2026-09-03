from decimal import Decimal
from uuid import UUID

from app.agent.tools.razorpay_tool import (
    normalize_currency,
)
from app.db.clickhouse import get_clickhouse_client
from app.services.policy_service import get_payment
from app.services.recovery_execution_service import (
    get_existing_payment_link,
    record_audit_event,
)


class WebhookPayloadError(Exception):
    pass


def is_payment_recovered(payment_id: str) -> bool:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT count() > 0
        FROM studiopay.recovery_attempts
        WHERE
            payment_id =
                toUUID(toString({payment_id:String}))
            AND result = 'recovered'
        """,
        parameters={
            "payment_id": payment_id,
        },
    )

    return bool(result.result_rows[0][0])


def record_successful_recovery(
    payment_id: str,
    amount: float,
):
    client = get_clickhouse_client()

    client.insert(
        "studiopay.recovery_attempts",
        [
            [
                UUID(payment_id),
                "send_payment_link",
                "razorpay",
                "recovered",
                Decimal(str(amount)),
                "",
                "razorpay_webhook",
            ]
        ],
        column_names=[
            "payment_id",
            "action",
            "channel",
            "result",
            "amount_recovered",
            "failure_reason",
            "initiated_by",
        ],
    )


def handle_payment_link_paid(
    webhook_payload: dict,
) -> dict:
    payload = webhook_payload.get("payload", {})

    link = (
        payload
        .get("payment_link", {})
        .get("entity", {})
    )

    razorpay_payment = (
        payload
        .get("payment", {})
        .get("entity", {})
    )

    notes = link.get("notes") or {}

    studiopay_payment_id = notes.get(
        "studiopay_payment_id"
    )

    if not studiopay_payment_id:
        raise WebhookPayloadError(
            "Missing StudioPay payment ID"
        )

    try:
        UUID(studiopay_payment_id)
    except ValueError as error:
        raise WebhookPayloadError(
            "Invalid StudioPay payment ID"
        ) from error

    payment = get_payment(studiopay_payment_id)

    if payment is None:
        raise WebhookPayloadError(
            "StudioPay payment was not found"
        )

    existing_link = get_existing_payment_link(
        studiopay_payment_id
    )

    if not existing_link:
        raise WebhookPayloadError(
            "Payment link was not created by StudioPay"
        )

    if (
        existing_link["razorpay_link_id"]
        != link.get("id")
    ):
        raise WebhookPayloadError(
            "Razorpay payment-link ID does not match"
        )

    expected_amount_paise = int(
        round(float(payment["amount"]) * 100)
    )

    received_amount_paise = int(
        razorpay_payment.get("amount", 0)
    )

    if received_amount_paise != expected_amount_paise:
        raise WebhookPayloadError(
            "Recovered amount does not match payment amount"
        )

    expected_currency = normalize_currency(
        payment["currency"]
    )

    received_currency = normalize_currency(
        razorpay_payment.get("currency", "")
    )

    if received_currency != expected_currency:
        raise WebhookPayloadError(
            "Recovered currency does not match"
        )

    if is_payment_recovered(studiopay_payment_id):
        return {
            "handled": True,
            "already_processed": True,
            "payment_id": studiopay_payment_id,
        }

    razorpay_payment_id = razorpay_payment.get("id")

    if not razorpay_payment_id:
        raise WebhookPayloadError(
            "Missing Razorpay payment ID"
        )

    record_successful_recovery(
        payment_id=studiopay_payment_id,
        amount=float(payment["amount"]),
    )

    record_audit_event(
        payment_id=studiopay_payment_id,
        event_type="payment_recovered",
        decision=(
            "Razorpay confirmed payment-link payment"
        ),
        metadata={
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_link_id": link.get("id"),
            "invoice_id": payment["invoice_id"],
            "amount": payment["amount"],
            "currency": expected_currency,
            "test_mode": True,
        },
    )

    return {
        "handled": True,
        "already_processed": False,
        "payment_id": studiopay_payment_id,
        "invoice_id": payment["invoice_id"],
        "status": "recovered",
    }