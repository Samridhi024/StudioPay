from typing import Any


MAX_RETRY_ATTEMPTS = 3
MANUAL_APPROVAL_THRESHOLD = 10_000.0


def build_decision(
    action: str,
    reason: str,
    can_execute_automatically: bool,
    requires_approval: bool = False,
    retry_after_minutes: int | None = None,
    stop_recovery: bool = False,
) -> dict[str, Any]:
    return {
        "action": action,
        "reason": reason,
        "can_execute_automatically": can_execute_automatically,
        "requires_approval": requires_approval,
        "retry_after_minutes": retry_after_minutes,
        "stop_recovery": stop_recovery,
    }


def evaluate_recovery_policy(
    payment_id: str,
    status: str,
    failure_code: str,
    amount: float,
    attempt_count: int,
) -> dict[str, Any]:
    """
    Evaluate deterministic payment-recovery rules.

    This function does not call an LLM or payment provider.
    """

    if status != "failed":
        decision = build_decision(
            action="no_action",
            reason="Only failed payments are eligible for recovery",
            can_execute_automatically=False,
            stop_recovery=True,
        )

    elif attempt_count >= MAX_RETRY_ATTEMPTS:
        decision = build_decision(
            action="manual_review",
            reason="Maximum recovery attempts reached",
            can_execute_automatically=False,
            requires_approval=True,
            stop_recovery=True,
        )

    elif amount >= MANUAL_APPROVAL_THRESHOLD:
        decision = build_decision(
            action="manual_review",
            reason=(
                "Payment amount exceeds the automatic "
                "recovery threshold"
            ),
            can_execute_automatically=False,
            requires_approval=True,
        )

    elif failure_code == "technical_error":
        decision = build_decision(
            action="smart_retry",
            reason="Temporary gateway error can be retried",
            can_execute_automatically=True,
            retry_after_minutes=15,
        )

    elif failure_code == "upi_timeout":
        decision = build_decision(
            action="smart_retry",
            reason="UPI timeout can be retried after a short delay",
            can_execute_automatically=True,
            retry_after_minutes=30,
        )

    elif failure_code == "insufficient_funds":
        decision = build_decision(
            action="smart_retry",
            reason="Allow time for the customer to add funds",
            can_execute_automatically=True,
            retry_after_minutes=1440,
        )

    elif failure_code == "card_expired":
        decision = build_decision(
            action="send_payment_link",
            reason="Customer must use a new payment method",
            can_execute_automatically=True,
        )

    elif failure_code == "bank_declined":
        decision = build_decision(
            action="customer_notification",
            reason="Customer should contact their bank or use another method",
            can_execute_automatically=True,
        )

    else:
        decision = build_decision(
            action="manual_review",
            reason="No approved recovery rule exists for this failure",
            can_execute_automatically=False,
            requires_approval=True,
        )

    return {
        "payment_id": payment_id,
        "policy_version": "1.0",
        "max_retry_attempts": MAX_RETRY_ATTEMPTS,
        "manual_approval_threshold": MANUAL_APPROVAL_THRESHOLD,
        **decision,
    }