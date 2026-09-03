from app.agent.tools.policy_tool import (
    evaluate_recovery_policy,
)
from app.db.clickhouse import get_clickhouse_client
from app.services.recovery_execution_service import (
    get_existing_payment_link,
)


class CustomerPaymentNotFoundError(Exception):
    pass


def get_latest_smart_retry(
    payment_id: str,
) -> dict | None:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            result,
            attempted_at,
            next_action_at
        FROM studiopay.recovery_attempts
        WHERE
            payment_id =
                toUUID({payment_id:String})
            AND action = 'smart_retry'
        ORDER BY attempted_at DESC
        LIMIT 1
        """,
        parameters={
            "payment_id": payment_id,
        },
    )

    if not result.result_rows:
        return None

    return dict(
        zip(
            result.column_names,
            result.result_rows[0],
        )
    )


def get_manual_review_status(
    payment_id: str,
) -> dict | None:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            event_type,
            actor AS reviewer,
            created_at AS reviewed_at
        FROM studiopay.audit_logs
        WHERE
            payment_id =
                toUUID({payment_id:String})
            AND event_type IN (
                'manual_review_approved',
                'manual_review_rejected'
            )
        ORDER BY created_at DESC
        LIMIT 1
        """,
        parameters={
            "payment_id": payment_id,
        },
    )

    if not result.result_rows:
        return None

    review = dict(
        zip(
            result.column_names,
            result.result_rows[0],
        )
    )

    review["result"] = (
        "approved"
        if review["event_type"]
        == "manual_review_approved"
        else "rejected"
    )

    return review


def find_customer_payment(
    invoice_id: str,
    customer_email: str,
    customer_phone: str,
) -> dict:
    client = get_clickhouse_client()

    invoice_id = invoice_id.strip()
    customer_email = customer_email.strip().lower()
    customer_phone = customer_phone.strip()

    result = client.query(
        """
        SELECT
            toString(p.payment_id) AS payment_id,
            p.invoice_id,
            v.name AS vendor_name,
            p.customer_name,
            toFloat64(p.amount) AS amount,
            p.currency,
            if(
                p.status = 'recovered'
                OR coalesce(
                    recovery_state.recovered,
                    0
                ) = 1,
                'recovered',
                p.status
            ) AS status,
            p.failure_code,
            p.failure_reason,
            p.attempt_count,
            p.payment_date
        FROM studiopay.payments AS p
        LEFT JOIN studiopay.vendors AS v
            ON p.vendor_id = v.vendor_id
        LEFT JOIN
        (
            SELECT
                payment_id,
                toUInt8(1) AS recovered
            FROM studiopay.recovery_attempts
            WHERE result = 'recovered'
            GROUP BY payment_id
        ) AS recovery_state
            ON p.payment_id =
                recovery_state.payment_id
        WHERE
            p.invoice_id = {invoice_id:String}
            AND lowerUTF8(p.customer_email) =
                {customer_email:String}
            AND p.customer_phone =
                {customer_phone:String}
        ORDER BY p.payment_date DESC
        LIMIT 1
        """,
        parameters={
            "invoice_id": invoice_id,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
        },
    )

    if not result.result_rows:
        raise CustomerPaymentNotFoundError(
            "Payment details were not found"
        )

    payment = dict(
        zip(
            result.column_names,
            result.result_rows[0],
        )
    )

    decision = evaluate_recovery_policy(
        payment_id=payment["payment_id"],
        status=payment["status"],
        failure_code=payment["failure_code"],
        amount=payment["amount"],
        attempt_count=payment["attempt_count"],
    )

    payment_link = None
    smart_retry = None
    manual_review = None

    if payment["status"] == "failed":
        payment_link = get_existing_payment_link(
            payment["payment_id"]
        )

        smart_retry = get_latest_smart_retry(
            payment["payment_id"]
        )

        manual_review = get_manual_review_status(
            payment["payment_id"]
        )

    return {
        "payment": payment,
        "recovery": {
            "action": decision["action"],
            "reason": decision["reason"],
            "requires_approval": (
                decision["requires_approval"]
            ),
            "retry_after_minutes": (
                decision["retry_after_minutes"]
            ),
            "payment_link": payment_link,
            "smart_retry": smart_retry,
            "manual_review": manual_review,
        },
    }