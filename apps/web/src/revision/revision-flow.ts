import type { RevisionChange, RevisionCompleted } from "@/generated/contracts";

export type RevisionPhase =
  | "idle"
  | "submitting"
  | "succeeded"
  | "conflict"
  | "retryable_failure"
  | "final_failure";

export type RevisionConflictCode =
  | "revision_limit_reached"
  | "idempotency_conflict"
  | "operation_in_progress";

export type RevisionFailureCode =
  | RevisionConflictCode
  | "revision_failed"
  | "retry_failed"
  | "safety_refusal"
  | "culture_review_required";

export interface RevisionFlowState {
  phase: RevisionPhase;
  selectedChanges: readonly RevisionChange[];
  visibleVersions: readonly [1] | readonly [1, 2];
  conflictCode?: RevisionConflictCode;
  canRetry: boolean;
  result?: RevisionCompleted;
}

export function idleRevisionState(): RevisionFlowState {
  return {
    phase: "idle",
    selectedChanges: [],
    visibleVersions: [1],
    canRetry: false,
  };
}

export function selectRevisionChange(
  state: RevisionFlowState,
  change: RevisionChange,
): RevisionFlowState {
  if (
    state.phase !== "idle" ||
    state.selectedChanges.includes(change) ||
    state.selectedChanges.length >= 2
  ) {
    return state;
  }
  return { ...state, selectedChanges: [...state.selectedChanges, change] };
}

export function canSubmitRevision(state: RevisionFlowState): boolean {
  return state.phase === "idle" && state.selectedChanges.length > 0;
}

export function beginRevision(state: RevisionFlowState): RevisionFlowState {
  if (!canSubmitRevision(state)) {
    return state;
  }
  return { ...state, phase: "submitting", canRetry: false };
}

export function resolveRevision(
  state: RevisionFlowState,
  result: RevisionCompleted,
): RevisionFlowState {
  if (result.result_version !== 2 || result.human_revision_count !== 1) {
    return {
      ...state,
      phase: "final_failure",
      canRetry: false,
      result: undefined,
    };
  }
  return {
    ...state,
    phase: "succeeded",
    visibleVersions: [1, 2],
    canRetry: false,
    conflictCode: undefined,
    result,
  };
}

export function failRevision(
  state: RevisionFlowState,
  code: RevisionFailureCode,
): RevisionFlowState {
  if (
    code === "revision_limit_reached" ||
    code === "idempotency_conflict" ||
    code === "operation_in_progress"
  ) {
    return {
      ...state,
      phase: "conflict",
      conflictCode: code,
      canRetry: false,
    };
  }
  if (code === "revision_failed") {
    return {
      ...state,
      phase: "retryable_failure",
      conflictCode: undefined,
      canRetry: true,
    };
  }
  return {
    ...state,
    phase: "final_failure",
    conflictCode: undefined,
    canRetry: false,
  };
}
