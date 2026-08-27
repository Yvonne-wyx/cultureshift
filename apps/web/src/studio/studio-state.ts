import type {
  AnalysisCompleted,
  AssetUploaded,
  BrandLockConfirmed,
  CompositionGenerated,
  CritiqueCompleted,
  DraftGenerated,
  RevisionCompleted,
  RunCreated,
} from "../generated/contracts";
import type { FixtureId } from "../fixtures/types";
import type { StudioErrorCode } from "./studio-api";

export type StudioPhase =
  | "configure"
  | "uploading"
  | "analyzing"
  | "awaiting_brand_lock"
  | "generating_draft"
  | "composing"
  | "reviewing"
  | "ready_v1"
  | "submitting_revision"
  | "ready_v2"
  | "retryable_failure"
  | "conflict"
  | "final_failure"
  | "deleting";

export interface StudioState {
  phase: StudioPhase;
  fixtureId: FixtureId;
  upload?: AssetUploaded;
  run?: RunCreated;
  analysis?: AnalysisCompleted;
  confirmation?: BrandLockConfirmed;
  draft?: DraftGenerated;
  composition?: CompositionGenerated;
  critique?: CritiqueCompleted;
  revision?: RevisionCompleted;
  visibleVersions: readonly [] | readonly [1] | readonly [1, 2];
  errorCode?: StudioErrorCode;
}

export type StudioEvent =
  | { type: "fixture_selected"; fixtureId: FixtureId }
  | { type: "upload_started" }
  | { type: "upload_succeeded"; result: AssetUploaded }
  | { type: "run_created"; result: RunCreated }
  | { type: "analysis_succeeded"; result: AnalysisCompleted }
  | { type: "brand_lock_confirmed"; result: BrandLockConfirmed }
  | { type: "generation_started" }
  | { type: "draft_succeeded"; result: DraftGenerated }
  | { type: "composition_succeeded"; result: CompositionGenerated }
  | { type: "critic_succeeded"; result: CritiqueCompleted }
  | { type: "revision_started" }
  | { type: "revision_succeeded"; result: RevisionCompleted }
  | { type: "retry_started" }
  | { type: "operation_failed"; code: StudioErrorCode }
  | { type: "delete_started" }
  | { type: "delete_succeeded" }
  | { type: "reset" };

const CONFLICT_CODES: ReadonlySet<StudioErrorCode> = new Set([
  "revision_limit_reached",
  "idempotency_conflict",
  "operation_in_progress",
]);

export function initialStudioState(fixtureId: FixtureId): StudioState {
  return { phase: "configure", fixtureId, visibleVersions: [] };
}

export function canUpload(state: StudioState): boolean {
  return state.phase === "configure";
}

export function canConfirmBrandLock(state: StudioState): boolean {
  return (
    state.phase === "awaiting_brand_lock" &&
    state.analysis !== undefined &&
    state.confirmation === undefined
  );
}

export function canGenerate(state: StudioState): boolean {
  return state.phase === "awaiting_brand_lock" && state.confirmation !== undefined;
}

export function canSubmitRevision(state: StudioState): boolean {
  return state.phase === "ready_v1" && state.revision === undefined;
}

export function canRetry(state: StudioState): boolean {
  return state.phase === "retryable_failure" && state.errorCode === "revision_failed";
}

export function canExport(state: StudioState, version: 1 | 2): boolean {
  return version === 1
    ? state.visibleVersions[0] === 1
    : state.visibleVersions[1] === 2;
}

export function canDelete(state: StudioState): boolean {
  return (
    state.upload !== undefined &&
    state.phase !== "uploading" &&
    state.phase !== "deleting"
  );
}

export function studioReducer(state: StudioState, event: StudioEvent): StudioState {
  if (event.type === "reset") return initialStudioState(state.fixtureId);
  if (event.type === "fixture_selected") {
    return state.phase === "configure"
      ? initialStudioState(event.fixtureId)
      : state;
  }
  if (event.type === "upload_started") {
    return canUpload(state) ? { ...state, phase: "uploading" } : state;
  }
  if (event.type === "upload_succeeded") {
    return state.phase === "uploading" ? { ...state, upload: event.result } : state;
  }
  if (event.type === "run_created") {
    return state.phase === "uploading" && state.upload
      ? { ...state, phase: "analyzing", run: event.result }
      : state;
  }
  if (event.type === "analysis_succeeded") {
    return state.phase === "analyzing" && state.run
      ? { ...state, phase: "awaiting_brand_lock", analysis: event.result }
      : state;
  }
  if (event.type === "brand_lock_confirmed") {
    return canConfirmBrandLock(state)
      ? { ...state, confirmation: event.result }
      : state;
  }
  if (event.type === "generation_started") {
    return canGenerate(state) ? { ...state, phase: "generating_draft" } : state;
  }
  if (event.type === "draft_succeeded") {
    return state.phase === "generating_draft"
      ? { ...state, phase: "composing", draft: event.result }
      : state;
  }
  if (event.type === "composition_succeeded") {
    return state.phase === "composing" && state.draft
      ? { ...state, phase: "reviewing", composition: event.result }
      : state;
  }
  if (event.type === "critic_succeeded") {
    if (state.phase !== "reviewing" || !state.composition) return state;
    return event.result.status === "ready"
      ? {
          ...state,
          phase: "ready_v1",
          critique: event.result,
          visibleVersions: [1],
          errorCode: undefined,
        }
      : {
          ...state,
          phase: "final_failure",
          critique: event.result,
          errorCode: "critic_failed",
        };
  }
  if (event.type === "revision_started") {
    return canSubmitRevision(state)
      ? { ...state, phase: "submitting_revision", errorCode: undefined }
      : state;
  }
  if (event.type === "revision_succeeded") {
    if (state.phase !== "submitting_revision" && state.phase !== "ready_v2") return state;
    if (
      event.result.result_version !== 2 ||
      event.result.human_revision_count !== 1
    ) {
      return { ...state, phase: "final_failure", errorCode: "revision_failed" };
    }
    return {
      ...state,
      phase: "ready_v2",
      revision: event.result,
      visibleVersions: [1, 2],
      errorCode: undefined,
    };
  }
  if (event.type === "retry_started") {
    return canRetry(state)
      ? { ...state, phase: "submitting_revision", errorCode: undefined }
      : state;
  }
  if (event.type === "operation_failed") {
    if (state.phase === "configure" || state.phase === "deleting") return state;
    if (CONFLICT_CODES.has(event.code)) {
      return { ...state, phase: "conflict", errorCode: event.code };
    }
    if (event.code === "revision_failed") {
      return { ...state, phase: "retryable_failure", errorCode: event.code };
    }
    return { ...state, phase: "final_failure", errorCode: event.code };
  }
  if (event.type === "delete_started") {
    return canDelete(state) ? { ...state, phase: "deleting" } : state;
  }
  if (event.type === "delete_succeeded") {
    return state.phase === "deleting" ? initialStudioState(state.fixtureId) : state;
  }
  return state;
}
