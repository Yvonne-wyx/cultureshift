from __future__ import annotations

from datetime import timedelta
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError

from cultureshift.composition import (
    DISCLOSURE,
    ComposeRequest,
    CompositionError,
    PillowCompositor,
)
from cultureshift.composition_storage import (
    CompositionArtifactError,
    CompositionArtifactStore,
)
from cultureshift.contracts import (
    BackgroundRequest,
    CompositionGenerated,
    ExecutionMode,
    RunStatus,
)
from cultureshift.domain import ProjectRunStatus, utc_now
from cultureshift.fixture_assets import FixtureAssetError, FixtureAssetRegistry
from cultureshift.image_provider import FixtureImageProvider, ImageProviderError
from cultureshift.repository import (
    CompositionImmutableError,
    InvalidRunStateError,
    ProjectRunNotFoundError,
    SQLiteProjectRunRepository,
)


class CompositionServiceErrorCode(StrEnum):
    RUN_NOT_FOUND = "run_not_found"
    INVALID_RUN_STATE = "invalid_run_state"
    BRAND_LOCK_UNCONFIRMED = "brand_lock_unconfirmed"
    DRAFT_UNAVAILABLE = "draft_unavailable"
    OUTPUT_INVALID = "composition_output_invalid"
    PERSISTENCE_FAILED = "composition_persistence_failed"


class CompositionServiceError(RuntimeError):
    def __init__(self, code: CompositionServiceErrorCode) -> None:
        self.code = code
        super().__init__("composition generation failed")


class CompositionService:
    def __init__(
        self,
        repository: SQLiteProjectRunRepository,
        provider: FixtureImageProvider,
        registry: FixtureAssetRegistry,
        compositor: PillowCompositor,
        artifact_store: CompositionArtifactStore,
        font_path: str | Path,
    ) -> None:
        self._repository = repository
        self._provider = provider
        self._registry = registry
        self._compositor = compositor
        self._artifact_store = artifact_store
        self._font_path = Path(font_path)

    def generate(self, run_id: UUID) -> CompositionGenerated:
        try:
            existing = self._repository.get_composition(run_id)
            if existing is not None:
                return existing
            run = self._repository.get(run_id)
            request = self._repository.get_request(run_id)
            analysis = self._repository.get_analysis(run_id)
            confirmation = self._repository.get_confirmed_brand_lock(run_id)
            draft = self._repository.get_draft(run_id)
        except ProjectRunNotFoundError:
            raise CompositionServiceError(CompositionServiceErrorCode.RUN_NOT_FOUND) from None
        if run.status is not ProjectRunStatus.IN_PROGRESS or analysis is None:
            raise CompositionServiceError(
                CompositionServiceErrorCode.INVALID_RUN_STATE
            )
        if request.execution_mode is not ExecutionMode.FIXTURE:
            raise CompositionServiceError(
                CompositionServiceErrorCode.INVALID_RUN_STATE
            )
        if confirmation is None:
            raise CompositionServiceError(
                CompositionServiceErrorCode.BRAND_LOCK_UNCONFIRMED
            )
        if draft is None:
            raise CompositionServiceError(CompositionServiceErrorCode.DRAFT_UNAVAILABLE)

        artifact_id = uuid4()
        now = utc_now()
        try:
            background = self._provider.generate_background(
                BackgroundRequest(
                    direction=run.direction,
                    target_locale=draft.brief.target_locale,
                    narrative=draft.brief.narrative,
                    use_scenario=draft.brief.use_scenario,
                )
            )
            logo = self._registry.resolve(confirmation.brand_lock.logo_asset_id)
            product_ui = self._registry.resolve(
                confirmation.brand_lock.product_ui_asset_ids[0]
            )
            composed = self._compositor.compose(
                ComposeRequest(
                    run_id=run.id,
                    background=background,
                    brand_lock=confirmation.brand_lock,
                    ad_copy=draft.ad_copy,
                    logo=logo,
                    product_ui=product_ui,
                    font_path=self._font_path,
                )
            )
            stored = self._artifact_store.save(
                artifact_id,
                composed.png_bytes,
                expires_at=now + timedelta(hours=24),
            )
            if stored.sha256 != composed.sha256:
                raise CompositionArtifactError("composition artifact unavailable")
            summary = CompositionGenerated(
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
        except (
            CompositionError,
            FixtureAssetError,
            ImageProviderError,
            IndexError,
            ValidationError,
        ):
            raise CompositionServiceError(CompositionServiceErrorCode.OUTPUT_INVALID) from None
        except CompositionArtifactError:
            self._artifact_store.delete(artifact_id)
            raise CompositionServiceError(
                CompositionServiceErrorCode.PERSISTENCE_FAILED
            ) from None

        try:
            return self._repository.save_composition(run_id, summary)
        except CompositionImmutableError:
            self._artifact_store.delete(artifact_id)
            try:
                replay = self._repository.get_composition(run_id)
            except ProjectRunNotFoundError:
                replay = None
            if replay is not None:
                return replay
            raise CompositionServiceError(
                CompositionServiceErrorCode.PERSISTENCE_FAILED
            ) from None
        except InvalidRunStateError:
            self._artifact_store.delete(artifact_id)
            raise CompositionServiceError(
                CompositionServiceErrorCode.INVALID_RUN_STATE
            ) from None
        except Exception:
            self._artifact_store.delete(artifact_id)
            raise CompositionServiceError(
                CompositionServiceErrorCode.PERSISTENCE_FAILED
            ) from None
