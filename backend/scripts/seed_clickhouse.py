import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_DNS, uuid5

import clickhouse_connect
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def stable_uuid(entity: str, number: int):
    return uuid5(NAMESPACE_DNS, f"studiopay-{entity}-{number}")


def create_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database="studiopay",
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
    )


def seed_database():
    client = create_client()

    existing_payments = client.query(
        "SELECT count() FROM studiopay.payments"
    ).result_rows[0][0]

    if existing_payments > 0:
        print(
            f"Database already contains {existing_payments} payments. "
            "Seed operation skipped."
        )
        return

    now = datetime.now(timezone.utc)

    vendors = [
        (
            stable_uuid("vendor", 1),
            "FrameForge Studios",
            "finance@frameforge.demo",
            "Production",
            "low",
            now,
        ),
        (
            stable_uuid("vendor", 2),
            "PixelCraft Media",
            "billing@pixelcraft.demo",
            "Post Production",
            "medium",
            now,
        ),
        (
            stable_uuid("vendor", 3),
            "SoundWave Audio",
            "accounts@soundwave.demo",
            "Audio",
            "low",
            now,
        ),
        (
            stable_uuid("vendor", 4),
            "MotionMint VFX",
            "payments@motionmint.demo",
            "VFX",
            "high",
            now,
        ),
        (
            stable_uuid("vendor", 5),
            "SceneSet Rentals",
            "finance@sceneset.demo",
            "Equipment",
            "medium",
            now,
        ),
    ]

    client.insert(
        "studiopay.vendors",
        vendors,
        column_names=[
            "vendor_id",
            "name",
            "email",
            "category",
            "risk_level",
            "created_at",
        ],
    )

    payment_specs = [
        # vendor, customer, email, amount, status, failure code, reason
        (1, "Aarav Sharma", "aarav@example.demo", "12000", "paid", "", ""),
        (2, "Diya Verma", "diya@example.demo", "8500", "paid", "", ""),
        (3, "Kabir Singh", "kabir@example.demo", "15750", "paid", "", ""),
        (4, "Meera Shah", "meera@example.demo", "6200", "paid", "", ""),
        (5, "Vihaan Gupta", "vihaan@example.demo", "9900", "paid", "", ""),
        (1, "Anaya Rao", "anaya@example.demo", "18500", "paid", "", ""),
        (2, "Arjun Nair", "arjun@example.demo", "7300", "paid", "", ""),
        (3, "Ira Kapoor", "ira@example.demo", "11000", "paid", "", ""),

        (4, "Rohan Jain", "rohan@example.demo", "4500", "recovered",
         "insufficient_funds", "Insufficient account balance"),
        (5, "Saanvi Das", "saanvi@example.demo", "7800", "recovered",
         "upi_timeout", "UPI request timed out"),
        (1, "Aditya Mehta", "aditya@example.demo", "12500", "recovered",
         "bank_declined", "Payment declined by bank"),
        (2, "Myra Iyer", "myra@example.demo", "3600", "recovered",
         "technical_error", "Temporary payment gateway error"),

        (3, "Reyansh Bose", "reyansh@example.demo", "5200", "failed",
         "insufficient_funds", "Insufficient account balance"),
        (4, "Aadhya Pillai", "aadhya@example.demo", "9600", "failed",
         "card_expired", "Customer card has expired"),
        (5, "Dhruv Joshi", "dhruv@example.demo", "15000", "failed",
         "bank_declined", "Payment declined by bank"),
        (1, "Tara Menon", "tara@example.demo", "2750", "failed",
         "upi_timeout", "UPI request timed out"),
        (2, "Krish Malhotra", "krish@example.demo", "6800", "failed",
         "technical_error", "Temporary payment gateway error"),

        (3, "Riya Kulkarni", "riya@example.demo", "4200", "pending", "", ""),
        (4, "Vivaan Roy", "vivaan@example.demo", "8700", "pending", "", ""),
        (5, "Navya Sethi", "navya@example.demo", "5300", "pending", "", ""),
    ]

    payments = []
    recovery_attempts = []
    audit_logs = []

    action_mapping = {
        "insufficient_funds": "smart_retry",
        "upi_timeout": "smart_retry",
        "technical_error": "smart_retry",
        "card_expired": "send_payment_link",
        "bank_declined": "customer_notification",
    }

    for index, spec in enumerate(payment_specs, start=1):
        (
            vendor_number,
            customer_name,
            customer_email,
            amount,
            status,
            failure_code,
            failure_reason,
        ) = spec

        payment_id = stable_uuid("payment", index)
        payment_date = now - timedelta(days=(index % 14) + 1)
        attempted_at = payment_date + timedelta(hours=6)

        recovered_at = (
            attempted_at + timedelta(minutes=5)
            if status == "recovered"
            else None
        )

        next_retry_at = (
            now + timedelta(hours=index)
            if status == "failed"
            else None
        )

        attempt_count = 1 if status in {"failed", "recovered"} else 0

        payments.append(
            (
                payment_id,
                stable_uuid("vendor", vendor_number),
                f"INV-{1000 + index}",
                f"pay_test_{index:04d}",
                customer_name,
                customer_email,
                Decimal(amount),
                "INR",
                status,
                failure_code,
                failure_reason,
                attempt_count,
                payment_date,
                next_retry_at,
                recovered_at,
                now,
            )
        )

        if status in {"failed", "recovered"}:
            action = action_mapping[failure_code]
            result = "success" if status == "recovered" else "failed"
            recovered_amount = (
                Decimal(amount)
                if status == "recovered"
                else Decimal("0")
            )

            recovery_attempts.append(
                (
                    stable_uuid("attempt", index),
                    payment_id,
                    action,
                    "automated",
                    result,
                    recovered_amount,
                    "" if result == "success" else failure_reason,
                    "policy_engine",
                    attempted_at,
                    None if result == "success" else next_retry_at,
                )
            )

            audit_logs.append(
                (
                    stable_uuid("audit", index),
                    payment_id,
                    f"recovery_{result}",
                    "policy_engine",
                    f"{action} selected for {failure_code}",
                    json.dumps(
                        {
                            "action": action,
                            "result": result,
                            "failure_code": failure_code,
                        }
                    ),
                    attempted_at,
                )
            )

    client.insert(
        "studiopay.payments",
        payments,
        column_names=[
            "payment_id",
            "vendor_id",
            "invoice_id",
            "razorpay_payment_id",
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
            "created_at",
        ],
    )

    client.insert(
        "studiopay.recovery_attempts",
        recovery_attempts,
        column_names=[
            "attempt_id",
            "payment_id",
            "action",
            "channel",
            "result",
            "amount_recovered",
            "failure_reason",
            "initiated_by",
            "attempted_at",
            "next_action_at",
        ],
    )

    client.insert(
        "studiopay.audit_logs",
        audit_logs,
        column_names=[
            "event_id",
            "payment_id",
            "event_type",
            "actor",
            "decision",
            "metadata",
            "created_at",
        ],
    )

    metrics = client.query(
        """
        SELECT
            count() AS total_payments,
            countIf(status = 'paid') AS paid_payments,
            countIf(status = 'failed') AS failed_payments,
            countIf(status = 'recovered') AS recovered_payments,
            sumIf(amount, status = 'failed') AS revenue_at_risk,
            sumIf(amount, status = 'recovered') AS recovered_revenue,
            round(
                100 * countIf(status = 'recovered') /
                nullIf(
                    countIf(status IN ('failed', 'recovered')),
                    0
                ),
                2
            ) AS recovery_rate
        FROM studiopay.payments
        """
    ).result_rows[0]

    print("Sample data inserted successfully")
    print(f"Total payments: {metrics[0]}")
    print(f"Paid payments: {metrics[1]}")
    print(f"Failed payments: {metrics[2]}")
    print(f"Recovered payments: {metrics[3]}")
    print(f"Revenue at risk: INR {metrics[4]}")
    print(f"Recovered revenue: INR {metrics[5]}")
    print(f"Recovery rate: {metrics[6]}%")


if __name__ == "__main__":
    seed_database()