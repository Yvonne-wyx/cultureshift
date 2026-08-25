from __future__ import annotations

import hashlib
import json
import re
from contextlib import suppress
from datetime import timedelta
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from cultureshift.composition import DISCLOSURE, ComposeRequest, CompositionError, PillowCompositor
from cultureshift.composition_storage import CompositionArtifactError, CompositionArtifactStore
from cultureshift.contracts import (
    BackgroundRequest,
    CompositionGenerated,
    ExecutionMode,
    FeedbackRequest,
    RetryRequest,
    RevisionCompleted,
    RunStatus,
)
from cultureshift.critic import Critic, CriticRequest
from cultureshift.domain import utc_now
from cultureshift.fixture_assets import FixtureAssetError, FixtureAssetRegistry
from cultureshift.image_provider import FixtureImageProvider, ImageProviderError
from cultureshift.repository import (
    DraftRecord,
    IdempotencyConflictError,
    InvalidRunStateError,
    OperationInProgressError,
    OperationRecord,
    OperationState,
    ProjectRunNotFoundError,
    RevisionLimitReachedError,
    RevisionRecord,
    SQLiteProjectRunRepository,
)
from cultureshift.revision import FixtureRevisionEngine
from cultureshift.workflow import RetryAction, RetryCondition, decide_retry

_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


class RevisionServiceErrorCode(StrEnum):
    RUN_NOT_FOUND = "run_not_found"
    INVALID_RUN_STATE = "invalid_run_state"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    OPERATION_IN_PROGRESS = "operation_in_progress"
    REVISION_LIMIT_REACHED = "revision_limit_reached"
    INVALID_REVISION_REQUEST = "invalid_revision_request"
    REVISION_FAILED = "revision_failed"
    RETRY_FAILED = "retry_failed"


class RevisionServiceError(RuntimeError):
    def __init__(self, code: RevisionServiceErrorCode) -> None:
        self.code = code
        super().__init__("revision operation failed")


class RevisionService:
    def __init__(
        self,
        repository: SQLiteProjectRunRepository,
        engine: FixtureRevisionEngine,
        provider: FixtureImageProvider,
        registry: FixtureAssetRegistry,
        compositor: PillowCompositor,
        artifact_store: CompositionArtifactStore,
        font_path: str | Path,
        critic: Critic,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._provider = provider
        self._registry = registry
        self._compositor = compositor
        self._artifact_store = artifact_store
        self._font_path = Path(font_path)
        self._critic = critic

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @classmethod
    def _key_digest(cls, key: str) -> str:
        if _IDEMPOTENCY_KEY.fullmatch(key) is None:
            raise RevisionServiceError(RevisionServiceErrorCode.INVALID_REVISION_REQUEST)
        return cls._digest(key)

    @classmethod
    def _fingerprint(cls, request: FeedbackRequest | RetryRequest) -> str:
        canonical = json.dumps(
            request.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return cls._digest(canonical)

    @staticmethod
    def _map_repository_error(error: Exception) -> RevisionServiceError:
        if isinstance(error, ProjectRunNotFoundError):
            code = RevisionServiceErrorCode.RUN_NOT_FOUND
        elif isinstance(error, IdempotencyConflictError):
            code = RevisionServiceErrorCode.IDEMPOTENCY_CONFLICT
        elif isinstance(error, OperationInProgressError):
            code = RevisionServiceErrorCode.OPERATION_IN_PROGRESS
        elif isinstance(error, RevisionLimitReachedError):
            code = RevisionServiceErrorCode.REVISION_LIMIT_REACHED
        else:
            code = RevisionServiceErrorCode.INVALID_RUN_STATE
        return RevisionServiceError(code)

    def submit_feedback(
        self, request: FeedbackRequest, idempotency_key: str
    ) -> RevisionCompleted:
        key_digest = self._key_digest(idempotency_key)
        fingerprint = self._fingerprint(request)
        now = utc_now()
        try:
            operation = self._repository.claim_feedback_operation(
                request.run_id,
                key_digest,
                fingerprint,
                request.requested_changes,
                self._digest(request.feedback),
                now,
            )
        except (
            ProjectRunNotFoundError,
            IdempotencyConflictError,
            OperationInProgressError,
            RevisionLimitReachedError,
            InvalidRunStateError,
        ) as error:
            raise self._map_repository_error(error) from None
        if operation.state is OperationState.SUCCEEDED and operation.public_response:
            return operation.public_response
        return self._execute(operation, retrying=False)

    def retry(self, request: RetryRequest, idempotency_key: str) -> RevisionCompleted:
        key_digest = self._key_digest(idempotency_key)
        fingerprint = self._fingerprint(request)
        try:
            operation = self._repository.claim_retry_operation(
                request.run_id, key_digest, fingerprint, utc_now()
            )
        except (
            ProjectRunNotFoundError,
            IdempotencyConflictError,
            OperationInProgressError,
            RevisionLimitReachedError,
            InvalidRunStateError,
        ) as error:
            raise self._map_repository_error(error) from None
        if operation.state is OperationState.SUCCEEDED and operation.public_response:
            return operation.public_response
        if operation.retry_condition is None or operation.retry_action is None:
            raise RevisionServiceError(RevisionServiceErrorCode.INVALID_RUN_STATE)
        attempt_count = self._repository.get(request.run_id).technical_attempt_count - 1
        decision = decide_retry(operation.retry_condition, attempt_count, None)
        if decision.action is not operation.retry_action or decision.action not in {
            RetryAction.RETRY_ONCE,
            RetryAction.REPAIR_ONCE,
            RetryAction.RECOMPOSE_SAME_LAYERS_ONCE,
        }:
            raise RevisionServiceError(RevisionServiceErrorCode.INVALID_RUN_STATE)
        return self._execute(operation, retrying=True)

    def _execute(
        self, operation: OperationRecord, *, retrying: bool
    ) -> RevisionCompleted:
        artifact_id = uuid4()
        artifact_saved = False
        try:
            run = self._repository.get(operation.run_id)
            request = self._repository.get_request(operation.run_id)
            analysis = self._repository.get_analysis(operation.run_id)
            confirmation = self._repository.get_confirmed_brand_lock(operation.run_id)
            original_draft = self._repository.get_draft(operation.run_id)
            previous = self._repository.get_composition(operation.run_id)
            previous_critique = self._repository.get_critique(operation.run_id)
            if (
                request.execution_mode is not ExecutionMode.FIXTURE
                or analysis is None
                or confirmation is None
                or original_draft is None
                or previous is None
                or previous_critique is None
                or previous_critique.report.status.value == "reject"
            ):
                raise InvalidRunStateError("complete reviewed version one required")
            revised = self._engine.revise(
                run.direction, original_draft, operation.requested_changes
            )
            now = utc_now()
            background = self._provider.generate_background(
                BackgroundRequest(
                    direction=run.direction,
                    target_locale=revised.brief.target_locale,
                    narrative=revised.brief.narrative,
                    use_scenario=revised.brief.use_scenario,
                )
            )
            composed = self._compositor.compose(
                ComposeRequest(
                    run_id=run.id,
                    background=background,
                    brand_lock=confirmation.brand_lock,
                    ad_copy=revised.ad_copy,
                    logo=self._registry.resolve(confirmation.brand_lock.logo_asset_id),
                    product_ui=self._registry.resolve(
                        confirmation.brand_lock.product_ui_asset_ids[0]
                    ),
                    font_path=self._font_path,
                )
            )
            stored = self._artifact_store.save(
                artifact_id, composed.png_bytes, expires_at=now + timedelta(hours=24)
            )
            artifact_saved = True
            if stored.sha256 != composed.sha256:
                raise CompositionArtifactError("composition artifact unavailable")
            composition = CompositionGenerated(
                run_id=run.id,
                status=RunStatus.IN_PROGRESS,
                execution_mode=ExecutionMode.FIXTURE,
                width=1600,
                height=900,
                media_type="image/png",
                rendered_sha256=composed.sha256,
                artifact_id=artifact_id,
                layers=composed.layers,
                disclosure=DISCLOSURE,
                generated_at=now,
            )
            revised_draft = DraftRecord(
                brief=revised.brief,
                ad_copy=revised.ad_copy,
                fact_references=revised.fact_references,
                rule_ids=revised.rule_ids,
                generated_at=now,
            )
            report = self._critic.review(
                CriticRequest(
                    analysis=analysis,
                    confirmed_brand_lock=confirmation.brand_lock,
                    draft=revised_draft,
                    composition=composition,
                    warning_codes=run.warning_codes,
                )
            )
            status = (
                RunStatus.FAILED_FINAL
                if report.status.value == "reject"
                else RunStatus.READY
            )
            current = self._repository.get(run.id)
            response = RevisionCompleted(
                run_id=run.id,
                status=status,
                result_version=2,
                previous_composition=previous,
                brief=revised.brief,
                copy=revised.ad_copy,
                composition=composition,
                critique=report,
                initial_generation_count=1,
                human_revision_count=1,
                technical_attempt_count=current.technical_attempt_count,
                revised_at=report.reviewed_at,
            )
            revision = RevisionRecord(
                run_id=run.id,
                result_version=2,
                requested_changes=operation.requested_changes,
                feedback_digest=operation.feedback_digest or self._digest(""),
                draft=revised_draft,
                composition=composition,
                critique=report,
                revised_at=report.reviewed_at,
            )
            self._repository.complete_revision(run.id, operation.id, revision, response)
            return response
        except (
            IdempotencyConflictError,
            OperationInProgressError,
            RevisionLimitReachedError,
        ) as error:
            if artifact_saved:
                self._artifact_store.delete(artifact_id)
            raise self._map_repository_error(error) from None
        except InvalidRunStateError:
            if artifact_saved:
                self._artifact_store.delete(artifact_id)
            raise RevisionServiceError(RevisionServiceErrorCode.INVALID_RUN_STATE) from None
        except (
            CompositionError,
            CompositionArtifactError,
            FixtureAssetError,
            ImageProviderError,
            IndexError,
            ValidationError,
        ):
            if artifact_saved:
                self._artifact_store.delete(artifact_id)
            with suppress(Exception):
                self._repository.fail_revision_operation(
                    operation.run_id,
                    operation.id,
                    RetryCondition.CONNECTION_BEFORE_ACCEPTANCE,
                    RetryAction.DO_NOT_RETRY if retrying else RetryAction.RETRY_ONCE,
                    utc_now(),
                )
            code = (
                RevisionServiceErrorCode.RETRY_FAILED
                if retrying
                else RevisionServiceErrorCode.REVISION_FAILED
            )
            raise RevisionServiceError(code) from None
        except Exception:
            if artifact_saved:
                self._artifact_store.delete(artifact_id)
            code = (
                RevisionServiceErrorCode.RETRY_FAILED
                if retrying
                else RevisionServiceErrorCode.REVISION_FAILED
            )
            raise RevisionServiceError(code) from None
