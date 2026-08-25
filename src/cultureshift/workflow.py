from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cultureshift.domain import ProjectRunStatus


class RetryCondition(StrEnum):
    CONNECTION_BEFORE_ACCEPTANCE = "connection_before_acceptance"
    ACCEPTED_WITH_CALL_ID = "accepted_with_call_id"
    ACCEPTANCE_UNKNOWN = "acceptance_unknown"
    INVALID_SCHEMA = "invalid_schema"
    SAFETY_REFUSAL = "safety_refusal"
    BRAND_LOCK_FAILURE = "brand_lock_failure"
    CULTURAL_AMBIGUITY = "cultural_ambiguity"


class RetryAction(StrEnum):
    RETRY_ONCE = "retry_once"
    POLL_EXISTING = "poll_existing"
    REQUIRE_EXPLICIT_ACKNOWLEDGEMENT = "require_explicit_acknowledgement"
    REPAIR_ONCE = "repair_once"
    DO_NOT_RETRY = "do_not_retry"
    RECOMPOSE_SAME_LAYERS_ONCE = "recompose_same_layers_once"
    REQUIRE_HUMAN_REVIEW = "require_human_review"


@dataclass(frozen=True, slots=True)
class RetryDecision:
    action: RetryAction
    next_status: ProjectRunStatus


def decide_retry(
    condition: RetryCondition,
    attempt_count: int,
    provider_call_id: str | None,
) -> RetryDecision:
    if attempt_count < 0:
        raise ValueError("attempt_count must be non-negative")
    if condition is RetryCondition.ACCEPTED_WITH_CALL_ID:
        if not provider_call_id or len(provider_call_id) > 128:
            raise ValueError("provider_call_id is required for polling")
        return RetryDecision(RetryAction.POLL_EXISTING, ProjectRunStatus.IN_PROGRESS)
    if condition in {
        RetryCondition.CONNECTION_BEFORE_ACCEPTANCE,
        RetryCondition.BRAND_LOCK_FAILURE,
        RetryCondition.INVALID_SCHEMA,
    }:
        if attempt_count >= 1:
            return RetryDecision(
                RetryAction.DO_NOT_RETRY,
                ProjectRunStatus.FAILED_FINAL,
            )
        action = {
            RetryCondition.CONNECTION_BEFORE_ACCEPTANCE: RetryAction.RETRY_ONCE,
            RetryCondition.BRAND_LOCK_FAILURE: RetryAction.RECOMPOSE_SAME_LAYERS_ONCE,
            RetryCondition.INVALID_SCHEMA: RetryAction.REPAIR_ONCE,
        }[condition]
        return RetryDecision(action, ProjectRunStatus.IN_PROGRESS)
    if condition is RetryCondition.ACCEPTANCE_UNKNOWN:
        return RetryDecision(
            RetryAction.REQUIRE_EXPLICIT_ACKNOWLEDGEMENT,
            ProjectRunStatus.FAILED_RETRYABLE,
        )
    if condition is RetryCondition.CULTURAL_AMBIGUITY:
        return RetryDecision(
            RetryAction.REQUIRE_HUMAN_REVIEW,
            ProjectRunStatus.READY,
        )
    return RetryDecision(RetryAction.DO_NOT_RETRY, ProjectRunStatus.FAILED_FINAL)
