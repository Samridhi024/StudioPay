import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from app.db.clickhouse import get_clickhouse_client
from app.services.policy_service import evaluate_payment


class VendorNotFoundError(Exception):
    pass


class DuplicateInvoiceError(Exception):
    pass


def get_available_vendors() -> list[dict]:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            toString(vendor_id),
            name,
            email,
            category,
            risk_level
        FROM studiopay.vendors
        ORDER BY name ASC
        """
    )

    vendors = []

    for row in result.result_rows:
        vendors.append(
            {
                "vendor_id": row[0],
                "name": row[1],
                "email": row[2],
                "category": row[3],
                "risk_level": row[4],
            }
        )

    return vendors


def vendor_exists(
    vendor_id: str,
) -> bool:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT count() > 0
        FROM studiopay.vendors
        WHERE vendor_id =
            toUUID({vendor_id:String})
        """,
        parameters={
            "vendor_id": vendor_id,
        },
    )

    return bool(result.result_rows[0][0])


def invoice_exists(
    invoice_id: str,
) -> bool:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT count() > 0
        FROM studiopay.payments
        WHERE invoice_id = {invoice_id:String}
        """,
        parameters={
            "invoice_id": invoice_id,
        },
    )

    return bool(result.result_rows[0][0])


def normalize_payment_date(
    payment_date: datetime | None,
) -> datetime:
    if payment_date is None:
        return datetime.now(timezone.utc)

    if payment_date.tzinfo is None:
        return payment_date.replace(
            tzinfo=timezone.utc
        )

    return payment_date.astimezone(timezone.utc)


def validate_phone_number(
    customer_phone: str,
) -> str:
    normalized_phone = customer_phone.strip()

    if not re.fullmatch(
        r"\+[1-9]\d{7,14}",
        normalized_phone,
    ):
        raise ValueError(
            "Phone number must contain a country "
            "code, for example +919876543210"
        )

    return normalized_phone


def create_payment_record(
    payment_data: dict,
) -> dict:
    client = get_clickhouse_client()

    vendor_id = str(
        payment_data["vendor_id"]
    ).strip()

    invoice_id = str(
        payment_data["invoice_id"]
    ).strip()

    customer_name = str(
        payment_data["customer_name"]
    ).strip()

    customer_email = str(
        payment_data["customer_email"]
    ).strip()

    customer_phone = validate_phone_number(
        str(payment_data["customer_phone"])
    )

    currency = str(
        payment_data.get("currency", "INR")
    ).strip().upper()

    status = str(
        payment_data.get("status", "failed")
    ).strip().lower()

    failure_code = str(
        payment_data.get("failure_code", "")
    ).strip()

    failure_reason = str(
        payment_data.get("failure_reason", "")
    ).strip()

    attempt_count = int(
        payment_data.get("attempt_count", 1)
    )

    try:
        amount = Decimal(
            str(payment_data["amount"])
        ).quantize(Decimal("0.01"))

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "Payment amount is invalid"
        ) from error

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero"
        )

    if not re.fullmatch(
        r"[A-Z]{3}",
        currency,
    ):
        raise ValueError(
            "Currency must be a three-letter code"
        )

    allowed_statuses = {
        "paid",
        "failed",
        "pending",
        "recovered",
    }

    if status not in allowed_statuses:
        raise ValueError(
            "Invalid payment status"
        )

    if attempt_count < 0 or attempt_count > 255:
        raise ValueError(
            "Attempt count must be between 0 and 255"
        )

    if "@" not in customer_email:
        raise ValueError(
            "Customer email is invalid"
        )

    if not vendor_exists(vendor_id):
        raise VendorNotFoundError(
            "The selected vendor was not found"
        )

    if invoice_exists(invoice_id):
        raise DuplicateInvoiceError(
            f"Invoice {invoice_id} already exists"
        )

    payment_id = uuid4()

    payment_date = normalize_payment_date(
        payment_data.get("payment_date")
    )

    recovered_at = (
        payment_date
        if status == "recovered"
        else None
    )

    # Failed-payment details should not remain
    # attached to successful payments.
    if status in {
        "paid",
        "pending",
        "recovered",
    }:
        failure_code = ""
        failure_reason = ""

    payment = {
        "payment_id": str(payment_id),
        "vendor_id": vendor_id,
        "invoice_id": invoice_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "amount": float(amount),
        "currency": currency,
        "status": status,
        "failure_code": failure_code,
        "failure_reason": failure_reason,
        "attempt_count": attempt_count,
        "payment_date": payment_date,
        "recovered_at": recovered_at,
    }

    decision = evaluate_payment(payment)

    client.insert(
        "studiopay.payments",
        [
            [
                payment_id,
                UUID(vendor_id),
                invoice_id,
                customer_name,
                customer_email,
                customer_phone,
                amount,
                currency,
                status,
                failure_code,
                failure_reason,
                attempt_count,
                payment_date,
                recovered_at,
            ]
        ],
        column_names=[
            "payment_id",
            "vendor_id",
            "invoice_id",
            "customer_name",
            "customer_email",
            "customer_phone",
            "amount",
            "currency",
            "status",
            "failure_code",
            "failure_reason",
            "attempt_count",
            "payment_date",
            "recovered_at",
        ],
    )

    return {
        "created": True,
        "payment": payment,
        "decision": decision,
    }