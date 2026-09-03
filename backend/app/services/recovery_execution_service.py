import json
from decimal import Decimal
from uuid import UUID

from app.agent.tools.razorpay_tool import (
    create_payment_link,
)
from app.db.clickhouse import get_clickhouse_client
from app.services.policy_service import (
    evaluate_payment,
    get_payment,
)

from datetime import datetime, timedelta, timezone

class PaymentNotFoundError(Exception):
    pass


class RecoveryActionNotAllowedError(Exception):
    pass


def get_existing_payment_link(
    payment_id: str,
) -> dict | None:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT metadata
        FROM studiopay.audit_logs
        WHERE
            toString(payment_id) =
                toString({payment_id:String})
            AND event_type = 'payment_link_created'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        parameters={
            "payment_id": payment_id,
        },
    )

    if not result.result_rows:
        return None

    try:
        metadata = json.loads(
            result.result_rows[0][0]
        )
    except (TypeError, json.JSONDecodeError):
        return None

    if not metadata.get("short_url"):
        return None

    metadata["reused"] = True

    return metadata


def record_recovery_attempt(
    payment_id: str,
    result: str,
    failure_reason: str = "",
):
    client = get_clickhouse_client()
    payment_uuid = UUID(payment_id)

    client.insert(
        "studiopay.recovery_attempts",
        [
            [
                payment_uuid,
                "send_payment_link",
                "razorpay",
                result,
                Decimal("0.00"),
                failure_reason,
                "policy_engine",
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


def record_audit_event(
    payment_id: str,
    event_type: str,
    decision: str,
    metadata: dict,
    actor: str = "studiopay_agent",
):
    client = get_clickhouse_client()
    payment_uuid = UUID(payment_id)

    client.insert(
        "studiopay.audit_logs",
        [
            [
                payment_uuid,
                event_type,
                actor,
                decision,
                json.dumps(
                    metadata,
                    default=str,
                ),
            ]
        ],
        column_names=[
            "payment_id",
            "event_type",
            "actor",
            "decision",
            "metadata",
        ],
    )


def execute_payment_link_recovery(
    payment_id: str,
) -> dict:
    payment = get_payment(payment_id)

    if payment is None:
        raise PaymentNotFoundError(
            "Payment was not found"
        )

    decision = evaluate_payment(payment)

    if (
        decision["action"] != "send_payment_link"
        or not decision["can_execute_automatically"]
        or decision["requires_approval"]
    ):
        raise RecoveryActionNotAllowedError(
            decision["reason"]
        )

    # Check whether an existing payment link can be reused.
    existing_link = get_existing_payment_link(
        payment_id
    )

    current_phone = str(
        payment.get("customer_phone") or ""
    ).strip()

    link_has_same_phone = bool(
        existing_link
        and current_phone
        and existing_link.get("customer_phone")
        == current_phone
    )

    link_requested_sms = bool(
        existing_link
        and existing_link.get(
            "sms_notification_requested"
        )
    )

    can_reuse_existing_link = bool(
        existing_link
        and (
            not current_phone
            or (
                link_has_same_phone
                and link_requested_sms
            )
        )
    )

    if can_reuse_existing_link:
        return {
            "payment": payment,
            "decision": decision,
            "payment_link": existing_link,
        }

    # If the previous link had no phone/SMS request,
    # execution continues here and creates a new link.
    try:
        payment_link = create_payment_link(payment)

        record_recovery_attempt(
            payment_id=payment_id,
            result="created",
        )

        record_audit_event(
            payment_id=payment_id,
            event_type="payment_link_created",
            decision=decision["reason"],
            metadata=payment_link,
        )

        payment_link["reused"] = False

        return {
            "payment": payment,
            "decision": decision,
            "payment_link": payment_link,
        }

    except Exception as error:
        failure_reason = str(error)[:500]

        record_recovery_attempt(
            payment_id=payment_id,
            result="failed",
            failure_reason=failure_reason,
        )

        record_audit_event(
            payment_id=payment_id,
            event_type="payment_link_creation_failed",
            decision=decision["reason"],
            metadata={
                "error": failure_reason,
                "test_mode": True,
            },
        )

        raise

def get_existing_smart_retry(
    payment_id: str,
) -> dict | None:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT next_action_at
        FROM studiopay.recovery_attempts
        WHERE
            payment_id =
                toUUID(
                    toString({payment_id:String})
                )
            AND action = 'smart_retry'
            AND result = 'scheduled'
            AND next_action_at > now64(3)
        ORDER BY attempted_at DESC
        LIMIT 1
        """,
        parameters={
            "payment_id": payment_id,
        },
    )

    if not result.result_rows:
        return None

    return {
        "next_action_at": result.result_rows[0][0],
        "reused": True,
    }


def schedule_smart_retry(
    payment_id: str,
) -> dict:
    payment = get_payment(payment_id)

    if payment is None:
        raise PaymentNotFoundError(
            "Payment was not found"
        )

    decision = evaluate_payment(payment)

    allowed = (
        decision["action"] == "smart_retry"
        and decision["can_execute_automatically"]
        and not decision["requires_approval"]
        and not decision["stop_recovery"]
        and decision["retry_after_minutes"] is not None
    )

    if not allowed:
        raise RecoveryActionNotAllowedError(
            decision["reason"]
        )

    existing_retry = get_existing_smart_retry(
        payment_id
    )

    if existing_retry:
        return {
            "payment": payment,
            "decision": decision,
            "retry": existing_retry,
        }

    retry_after_minutes = int(
        decision["retry_after_minutes"]
    )

    next_action_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=retry_after_minutes)
    )

    client = get_clickhouse_client()

    client.insert(
        "studiopay.recovery_attempts",
        [
            [
                UUID(payment_id),
                "smart_retry",
                "razorpay",
                "scheduled",
                Decimal("0.00"),
                "",
                "policy_engine",
                next_action_at,
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
            "next_action_at",
        ],
    )

    retry_metadata = {
        "payment_id": payment_id,
        "invoice_id": payment["invoice_id"],
        "retry_after_minutes": retry_after_minutes,
        "next_action_at": next_action_at.isoformat(),
        "test_mode": True,
    }

    record_audit_event(
        payment_id=payment_id,
        event_type="smart_retry_scheduled",
        decision=decision["reason"],
        metadata=retry_metadata,
    )

    return {
        "payment": payment,
        "decision": decision,
        "retry": {
            **retry_metadata,
            "reused": False,
        },
    }

def get_existing_manual_review(
    payment_id: str,
) -> dict | None:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            event_type,
            actor,
            decision,
            metadata,
            created_at
        FROM studiopay.audit_logs
        WHERE
            payment_id =
                toUUID(
                    toString({payment_id:String})
                )
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

    row = result.result_rows[0]

    return {
        "event_type": row[0],
        "reviewer": row[1],
        "decision": row[2],
        "metadata": json.loads(row[3]),
        "reviewed_at": row[4],
        "reused": True,
    }


def record_manual_review(
    payment_id: str,
    approved: bool,
    reviewer: str,
) -> dict:
    payment = get_payment(payment_id)

    if payment is None:
        raise PaymentNotFoundError(
            "Payment was not found"
        )

    decision = evaluate_payment(payment)

    if not decision["requires_approval"]:
        raise RecoveryActionNotAllowedError(
            "This payment does not require manual approval"
        )

    existing_review = get_existing_manual_review(
        payment_id
    )

    if existing_review:
        return {
            "payment": payment,
            "policy_decision": decision,
            "review": existing_review,
        }

    review_result = (
        "approved"
        if approved
        else "rejected"
    )

    event_type = (
        "manual_review_approved"
        if approved
        else "manual_review_rejected"
    )

    review_reason = (
        "Reviewer approved manual recovery follow-up"
        if approved
        else "Reviewer rejected manual recovery follow-up"
    )

    client = get_clickhouse_client()

    client.insert(
        "studiopay.recovery_attempts",
        [
            [
                UUID(payment_id),
                "manual_review",
                "dashboard",
                review_result,
                Decimal("0.00"),
                "" if approved else review_reason,
                reviewer,
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

    review_metadata = {
        "payment_id": payment_id,
        "invoice_id": payment["invoice_id"],
        "amount": payment["amount"],
        "approved": approved,
        "reviewer": reviewer,
        "policy_version": decision["policy_version"],
        "test_mode": True,
    }

    record_audit_event(
        payment_id=payment_id,
        event_type=event_type,
        decision=review_reason,
        metadata=review_metadata,
        actor=reviewer,
    )

    return {
        "payment": payment,
        "policy_decision": decision,
        "review": {
            "result": review_result,
            "reviewer": reviewer,
            "reason": review_reason,
            "reused": False,
        },
    }