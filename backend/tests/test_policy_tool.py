from app.agent.tools.policy_tool import evaluate_recovery_policy


def evaluate(
    *,
    status="failed",
    failure_code="technical_error",
    amount=5000,
    attempt_count=1,
):
    return evaluate_recovery_policy(
        payment_id="test-payment",
        status=status,
        failure_code=failure_code,
        amount=amount,
        attempt_count=attempt_count,
    )


def test_technical_error_uses_smart_retry():
    result = evaluate(failure_code="technical_error")

    assert result["action"] == "smart_retry"
    assert result["retry_after_minutes"] == 15
    assert result["can_execute_automatically"] is True


def test_expired_card_uses_payment_link():
    result = evaluate(failure_code="card_expired")

    assert result["action"] == "send_payment_link"
    assert result["can_execute_automatically"] is True


def test_high_value_payment_requires_approval():
    result = evaluate(amount=15000)

    assert result["action"] == "manual_review"
    assert result["requires_approval"] is True
    assert result["can_execute_automatically"] is False


def test_maximum_attempts_stops_recovery():
    result = evaluate(attempt_count=3)

    assert result["action"] == "manual_review"
    assert result["stop_recovery"] is True


def test_successful_payment_receives_no_action():
    result = evaluate(
        status="paid",
        failure_code="",
        attempt_count=0,
    )

    assert result["action"] == "no_action"
    assert result["stop_recovery"] is True