from app.agent.tools.policy_tool import (
    evaluate_recovery_policy,
)
from app.db.clickhouse import get_clickhouse_client


def get_failed_payments():
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            toString(p.payment_id) AS payment_id,
            p.invoice_id,
            p.customer_name,
            toFloat64(p.amount) AS amount,
            toString(p.status) AS status,
            p.failure_code,
            p.failure_reason,
            p.attempt_count

        FROM studiopay.payments AS p

        LEFT JOIN
        (
            SELECT
                payment_id,
                count() AS recovered_count
            FROM studiopay.recovery_attempts
            WHERE result = 'recovered'
            GROUP BY payment_id
        ) AS r
            ON p.payment_id = r.payment_id

        WHERE
            p.status = 'failed'
            AND r.recovered_count = 0

        ORDER BY p.amount DESC
        """
    )

    return [
        dict(zip(result.column_names, row))
        for row in result.result_rows
    ]


def get_payment(
    payment_id: str,
) -> dict | None:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            toString(payment_id),
            invoice_id,
            customer_name,
            customer_email,
            customer_phone,
            amount,
            currency,
            status,
            failure_code,
            failure_reason,
            attempt_count
        FROM studiopay.payments
        WHERE payment_id =
            toUUID({payment_id:String})
        LIMIT 1
        """,
        parameters={
            "payment_id": payment_id,
        },
    )

    if not result.result_rows:
        return None

    row = result.result_rows[0]

    def to_text(value) -> str:
        if value is None:
            return ""

        if isinstance(value, bytes):
            return value.decode(
                "utf-8",
                errors="replace",
            )

        return str(value)

    return {
        "payment_id": to_text(row[0]),
        "invoice_id": to_text(row[1]),
        "customer_name": to_text(row[2]),
        "customer_email": to_text(row[3]),
        "customer_phone": to_text(row[4]),
        "amount": float(row[5]),
        "currency": to_text(row[6]).upper(),
        "status": to_text(row[7]).lower(),
        "failure_code": to_text(row[8]),
        "failure_reason": to_text(row[9]),
        "attempt_count": int(row[10]),
    }


def evaluate_payment(payment: dict):
    return evaluate_recovery_policy(
        payment_id=payment["payment_id"],
        status=payment["status"],
        failure_code=payment["failure_code"],
        amount=payment["amount"],
        attempt_count=payment["attempt_count"],
    )


def get_recovery_recommendations():
    payments = get_failed_payments()
    review_statuses = get_manual_review_statuses()

    return [
        {
            **payment,
            "decision": evaluate_payment(payment),
            "review": review_statuses.get(
                payment["payment_id"]
            ),
        }
        for payment in payments
    ]

def get_manual_review_statuses():
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            toString(a.payment_id) AS payment_id,
            argMax(
                a.event_type,
                a.created_at
            ) AS event_type,
            argMax(
                a.actor,
                a.created_at
            ) AS reviewer,
            max(a.created_at) AS reviewed_at
        FROM studiopay.audit_logs AS a
        WHERE
            a.payment_id IS NOT NULL
            AND a.event_type IN (
                'manual_review_approved',
                'manual_review_rejected'
            )
        GROUP BY a.payment_id
        """
    )

    return {
        row[0]: {
            "event_type": row[1],
            "result": (
                "approved"
                if row[1] == "manual_review_approved"
                else "rejected"
            ),
            "reviewer": row[2],
            "reviewed_at": row[3],
        }
        for row in result.result_rows
    }