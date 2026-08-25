import pytest

from cultureshift.domain import ProjectRunStatus
from cultureshift.workflow import RetryAction, RetryCondition, decide_retry


@pytest.mark.parametrize(
    ("condition", "attempts", "call_id", "action", "status"),
    [
        (
            RetryCondition.CONNECTION_BEFORE_ACCEPTANCE,
            0,
            None,
            RetryAction.RETRY_ONCE,
            ProjectRunStatus.IN_PROGRESS,
        ),
        (
            RetryCondition.ACCEPTED_WITH_CALL_ID,
            1,
            "job-1",
            RetryAction.POLL_EXISTING,
            ProjectRunStatus.IN_PROGRESS,
        ),
        (
            RetryCondition.ACCEPTANCE_UNKNOWN,
            1,
            None,
            RetryAction.REQUIRE_EXPLICIT_ACKNOWLEDGEMENT,
            ProjectRunStatus.FAILED_RETRYABLE,
        ),
        (
            RetryCondition.INVALID_SCHEMA,
            0,
            None,
            RetryAction.REPAIR_ONCE,
            ProjectRunStatus.IN_PROGRESS,
        ),
        (
            RetryCondition.SAFETY_REFUSAL,
            0,
            None,
            RetryAction.DO_NOT_RETRY,
            ProjectRunStatus.FAILED_FINAL,
        ),
        (
            RetryCondition.BRAND_LOCK_FAILURE,
            0,
            None,
            RetryAction.RECOMPOSE_SAME_LAYERS_ONCE,
            ProjectRunStatus.IN_PROGRESS,
        ),
        (
            RetryCondition.CULTURAL_AMBIGUITY,
            0,
            None,
            RetryAction.REQUIRE_HUMAN_REVIEW,
            ProjectRunStatus.READY,
        ),
    ],
)
def test_retry_policy_maps_each_failure_to_one_safe_action(
    condition: RetryCondition,
    attempts: int,
    call_id: str | None,
    action: RetryAction,
    status: ProjectRunStatus,
) -> None:
    decision = decide_retry(condition, attempts, call_id)

    assert decision.action is action
    assert decision.next_status is status


@pytest.mark.parametrize(
    "condition",
    [RetryCondition.CONNECTION_BEFORE_ACCEPTANCE, RetryCondition.BRAND_LOCK_FAILURE],
)
def test_one_shot_retry_conditions_fail_final_after_first_attempt(
    condition: RetryCondition,
) -> None:
    decision = decide_retry(condition, attempt_count=1, provider_call_id=None)

    assert decision.action is RetryAction.DO_NOT_RETRY
    assert decision.next_status is ProjectRunStatus.FAILED_FINAL


def test_polling_requires_a_bounded_provider_call_id() -> None:
    with pytest.raises(ValueError, match="provider_call_id"):
        decide_retry(RetryCondition.ACCEPTED_WITH_CALL_ID, 0, None)
    with pytest.raises(ValueError, match="attempt_count"):
        decide_retry(RetryCondition.INVALID_SCHEMA, -1, None)
