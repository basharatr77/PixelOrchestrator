
from app.core.module_contract import ActionResult
from app.core.retry_policy import RetryPolicy


def test_retry_policy_defaults_to_one_attempt():
    policy = RetryPolicy()

    assert policy.max_attempts == 1


def test_retry_policy_accepts_positive_max_attempts():
    policy = RetryPolicy(max_attempts=3)

    assert policy.max_attempts == 3


def test_retry_policy_rejects_zero_max_attempts():
    try:
        RetryPolicy(max_attempts=0)
    except ValueError:
        pass
    else:
        raise AssertionError("RetryPolicy must reject zero max_attempts")


def test_retry_policy_rejects_negative_max_attempts():
    try:
        RetryPolicy(max_attempts=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("RetryPolicy must reject negative max_attempts")


def test_retry_policy_does_not_retry_success():
    policy = RetryPolicy(max_attempts=3)
    result = ActionResult(success=True, message="ok")

    assert policy.should_retry(attempts=1, result=result) is False


def test_retry_policy_retries_failure_when_attempts_remain():
    policy = RetryPolicy(max_attempts=3)
    result = ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    )

    assert policy.should_retry(attempts=1, result=result) is True


def test_retry_policy_stops_at_max_attempts():
    policy = RetryPolicy(max_attempts=3)
    result = ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    )

    assert policy.should_retry(attempts=3, result=result) is False


def test_retry_policy_stops_when_attempt_count_exceeds_limit():
    policy = RetryPolicy(max_attempts=3)
    result = ActionResult(
        success=False,
        message="failed",
        error_code="TEST_FAILURE",
    )

    assert policy.should_retry(attempts=4, result=result) is False
