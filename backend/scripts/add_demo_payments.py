import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(
    PROJECT_ROOT / ".env",
    override=True,
)


from app.db.clickhouse import get_clickhouse_client  # noqa: E402


def build_demo_payments():
    now = datetime.now(timezone.utc)

    return [
        {
            "invoice_id": "INV-2026",
            "customer_name": "Rohan Verma",
            "customer_email": "rohan@example.demo",
            "amount": Decimal("4800.00"),
            "status": "failed",
            "failure_code": "technical_error",
            "failure_reason": "Temporary payment gateway error",
            "attempt_count": 1,
            "payment_date": now - timedelta(hours=2),
        },
        {
            "invoice_id": "INV-2027",
            "customer_name": "Meera Nair",
            "customer_email": "meera@example.demo",
            "amount": Decimal("2350.00"),
            "status": "failed",
            "failure_code": "upi_timeout",
            "failure_reason": "UPI payment request timed out",
            "attempt_count": 1,
            "payment_date": now - timedelta(hours=4),
        },
        {
            "invoice_id": "INV-2028",
            "customer_name": "Arjun Sinha",
            "customer_email": "arjun@example.demo",
            "amount": Decimal("6200.00"),
            "status": "failed",
            "failure_code": "insufficient_funds",
            "failure_reason": "Insufficient account balance",
            "attempt_count": 2,
            "payment_date": now - timedelta(hours=6),
        },
        {
            "invoice_id": "INV-2029",
            "customer_name": "Kavya Iyer",
            "customer_email": "kavya@example.demo",
            "amount": Decimal("8400.00"),
            "status": "failed",
            "failure_code": "card_expired",
            "failure_reason": "Customer card has expired",
            "attempt_count": 1,
            "payment_date": now - timedelta(hours=8),
        },
        {
            "invoice_id": "INV-2030",
            "customer_name": "Aditya Rao",
            "customer_email": "aditya@example.demo",
            "amount": Decimal("9200.00"),
            "status": "failed",
            "failure_code": "bank_declined",
            "failure_reason": "Payment was declined by the bank",
            "attempt_count": 1,
            "payment_date": now - timedelta(hours=10),
        },
        {
            "invoice_id": "INV-2031",
            "customer_name": "Sneha Kapoor",
            "customer_email": "sneha@example.demo",
            "amount": Decimal("16500.00"),
            "status": "failed",
            "failure_code": "technical_error",
            "failure_reason": "Temporary payment gateway error",
            "attempt_count": 1,
            "payment_date": now - timedelta(days=1),
        },
        {
            "invoice_id": "INV-2032",
            "customer_name": "Vihaan Das",
            "customer_email": "vihaan@example.demo",
            "amount": Decimal("3900.00"),
            "status": "failed",
            "failure_code": "technical_error",
            "failure_reason": "Temporary payment gateway error",
            "attempt_count": 3,
            "payment_date": now - timedelta(days=1, hours=2),
        },
        {
            "invoice_id": "INV-2033",
            "customer_name": "Nisha Mehta",
            "customer_email": "nisha@example.demo",
            "amount": Decimal("11000.00"),
            "status": "paid",
            "failure_code": "",
            "failure_reason": "",
            "attempt_count": 0,
            "payment_date": now - timedelta(days=1, hours=4),
        },
        {
            "invoice_id": "INV-2034",
            "customer_name": "Dev Malhotra",
            "customer_email": "dev@example.demo",
            "amount": Decimal("7400.00"),
            "status": "pending",
            "failure_code": "",
            "failure_reason": "",
            "attempt_count": 0,
            "payment_date": now - timedelta(days=2),
        },
        {
            "invoice_id": "INV-2035",
            "customer_name": "Ishita Bose",
            "customer_email": "ishita@example.demo",
            "amount": Decimal("5800.00"),
            "status": "recovered",
            "failure_code": "upi_timeout",
            "failure_reason": "UPI payment request previously timed out",
            "attempt_count": 2,
            "payment_date": now - timedelta(days=3),
            "recovered_at": now - timedelta(days=1),
        },
        {
            "invoice_id": "INV-2036",
            "customer_name": "Kabir Jain",
            "customer_email": "kabir@example.demo",
            "amount": Decimal("9700.00"),
            "status": "failed",
            "failure_code": "card_expired",
            "failure_reason": "Customer card has expired",
            "attempt_count": 2,
            "payment_date": now - timedelta(days=2, hours=3),
        },
        {
            "invoice_id": "INV-2037",
            "customer_name": "Aarav Gupta",
            "customer_email": "aarav@example.demo",
            "amount": Decimal("3100.00"),
            "status": "failed",
            "failure_code": "insufficient_funds",
            "failure_reason": "Insufficient account balance",
            "attempt_count": 2,
            "payment_date": now - timedelta(days=2, hours=5),
        },
        {
            "invoice_id": "INV-2038",
            "customer_name": "Diya Menon",
            "customer_email": "diya@example.demo",
            "amount": Decimal("12000.00"),
            "status": "failed",
            "failure_code": "upi_timeout",
            "failure_reason": "UPI payment request timed out",
            "attempt_count": 1,
            "payment_date": now - timedelta(days=3, hours=2),
        },
        {
            "invoice_id": "INV-2039",
            "customer_name": "Yash Patel",
            "customer_email": "yash@example.demo",
            "amount": Decimal("6600.00"),
            "status": "failed",
            "failure_code": "issuer_unavailable",
            "failure_reason": "Card issuer was temporarily unavailable",
            "attempt_count": 1,
            "payment_date": now - timedelta(days=3, hours=5),
        },
        {
            "invoice_id": "INV-2040",
            "customer_name": "Sara Kulkarni",
            "customer_email": "sara@example.demo",
            "amount": Decimal("9999.00"),
            "status": "failed",
            "failure_code": "technical_error",
            "failure_reason": "Temporary payment gateway error",
            "attempt_count": 1,
            "payment_date": now - timedelta(days=4),
        },
    ]


def add_demo_payments():
    client = get_clickhouse_client()

    vendor_result = client.query(
        """
        SELECT
            vendor_id,
            name
        FROM studiopay.vendors
        ORDER BY name
        """
    )

    if not vendor_result.result_rows:
        raise RuntimeError(
            "No vendors exist. Run the original seed script first."
        )

    vendors = vendor_result.result_rows

    existing_result = client.query(
        """
        SELECT invoice_id
        FROM studiopay.payments
        """
    )

    existing_invoices = {
        row[0]
        for row in existing_result.result_rows
    }

    demo_payments = build_demo_payments()
    rows = []

    added_invoices = []
    skipped_invoices = []

    for index, payment in enumerate(demo_payments):
        invoice_id = payment["invoice_id"]

        if invoice_id in existing_invoices:
            skipped_invoices.append(invoice_id)
            continue

        vendor_id = vendors[index % len(vendors)][0]

        payment_id = uuid5(
            NAMESPACE_URL,
            f"https://studiopay.demo/{invoice_id}",
        )

        recovered_at = payment.get("recovered_at")

        rows.append(
            [
                payment_id,
                vendor_id,
                invoice_id,
                payment["customer_name"],
                payment["customer_email"],
                payment["amount"],
                "INR",
                payment["status"],
                payment["failure_code"],
                payment["failure_reason"],
                payment["attempt_count"],
                payment["payment_date"],
                None,
                recovered_at,
            ]
        )

        added_invoices.append(invoice_id)

    if rows:
        client.insert(
            "studiopay.payments",
            rows,
            column_names=[
                "payment_id",
                "vendor_id",
                "invoice_id",
                "customer_name",
                "customer_email",
                "amount",
                "currency",
                "status",
                "failure_code",
                "failure_reason",
                "attempt_count",
                "payment_date",
                "next_retry_at",
                "recovered_at",
            ],
        )

    print(f"Added payments: {len(added_invoices)}")

    for invoice_id in added_invoices:
        print(f"- Added {invoice_id}")

    if skipped_invoices:
        print(
            f"Skipped existing payments: "
            f"{len(skipped_invoices)}"
        )

        for invoice_id in skipped_invoices:
            print(f"- Skipped {invoice_id}")

    total_result = client.query(
        """
        SELECT count()
        FROM studiopay.payments
        """
    )

    print(
        "Total payments in ClickHouse:",
        total_result.result_rows[0][0],
    )


if __name__ == "__main__":
    add_demo_payments()