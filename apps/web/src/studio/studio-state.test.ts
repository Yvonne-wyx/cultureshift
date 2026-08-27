import { describe, expect, it } from "vitest";

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

import {
  canConfirmBrandLock,
  canDelete,
  canExport,
  canGenerate,
  canRetry,
  canSubmitRevision,
  canUpload,
  initialStudioState,
  studioReducer,
} from "./studio-state";

const uploaded = {
  asset: { asset_id: "22222222-2222-4222-8222-222222222222" },
  delete_capability_token: "delete-capability-private-value",
} as AssetUploaded;
const runCreated = {
  run_id: "11111111-1111-4111-8111-111111111111",
  capability_token: "run-capability-private-value",
  status: "pending",
} as RunCreated;
const analysis = { status: "awaiting_brand_lock" } as AnalysisCompleted;
const confirmation = { status: "in_progress" } as BrandLockConfirmed;
const draft = { status: "in_progress" } as DraftGenerated;
const composition = {
  artifact_id: "33333333-3333-4333-8333-333333333333",
} as CompositionGenerated;
const critique = { status: "ready" } as CritiqueCompleted;
const revision = {
  result_version: 2,
  human_revision_count: 1,
  composition: {
    artifact_id: "44444444-4444-4444-8444-444444444444",
  },
} as RevisionCompleted;

function readyVersionOne(fixtureId: "china-to-uk" | "uk-to-china" = "china-to-uk") {
  let state = initialStudioState(fixtureId);
  state = studioReducer(state, { type: "upload_started" });
  state = studioReducer(state, { type: "upload_succeeded", result: uploaded });
  state = studioReducer(state, { type: "run_created", result: runCreated });
  state = studioReducer(state, { type: "analysis_succeeded", result: analysis });
  state = studioReducer(state, {
    type: "brand_lock_confirmed",
    result: confirmation,
  });
  state = studioReducer(state, { type: "generation_started" });
  state = studioReducer(state, { type: "draft_succeeded", result: draft });
  state = studioReducer(state, {
    type: "composition_succeeded",
    result: composition,
  });
  state = studioReducer(state, { type: "critic_succeeded", result: critique });
  return state;
}

describe("Studio state", () => {
  it.each(["china-to-uk", "uk-to-china"] as const)(
    "reaches ready version one through every required phase for %s",
    (fixtureId) => {
      const state = readyVersionOne(fixtureId);

      expect(state.phase).toBe("ready_v1");
      expect(state.fixtureId).toBe(fixtureId);
      expect(state.visibleVersions).toEqual([1]);
      expect(state.upload).toBe(uploaded);
      expect(state.run).toBe(runCreated);
      expect(canSubmitRevision(state)).toBe(true);
      expect(canExport(state, 1)).toBe(true);
      expect(canExport(state, 2)).toBe(false);
    },
  );

  it("enables actions only at their legal boundary", () => {
    const initial = initialStudioState("china-to-uk");
    expect(canUpload(initial)).toBe(true);
    expect(canConfirmBrandLock(initial)).toBe(false);

    const uploadedState = studioReducer(
      studioReducer(initial, { type: "upload_started" }),
      { type: "upload_succeeded", result: uploaded },
    );
    const running = studioReducer(uploadedState, {
      type: "run_created",
      result: runCreated,
    });
    const analyzed = studioReducer(running, {
      type: "analysis_succeeded",
      result: analysis,
    });
    const confirmed = studioReducer(analyzed, {
      type: "brand_lock_confirmed",
      result: confirmation,
    });

    expect(canUpload(running)).toBe(false);
    expect(canConfirmBrandLock(analyzed)).toBe(true);
    expect(canConfirmBrandLock(confirmed)).toBe(false);
    expect(canGenerate(analyzed)).toBe(false);
    expect(canGenerate(confirmed)).toBe(true);
    expect(canDelete(confirmed)).toBe(true);
  });

  it("replay replaces version two and never appends version three", () => {
    const ready = readyVersionOne();
    const submitting = studioReducer(ready, { type: "revision_started" });
    const first = studioReducer(submitting, {
      type: "revision_succeeded",
      result: revision,
    });
    const replay = studioReducer(first, {
      type: "revision_succeeded",
      result: revision,
    });

    expect(first.phase).toBe("ready_v2");
    expect(replay.phase).toBe("ready_v2");
    expect(replay.visibleVersions).toEqual([1, 2]);
    expect(canSubmitRevision(replay)).toBe(false);
    expect(canExport(replay, 2)).toBe(true);
  });

  it.each([
    "revision_limit_reached",
    "idempotency_conflict",
    "operation_in_progress",
  ] as const)("keeps %s as a distinct non-retryable conflict", (code) => {
    const active = studioReducer(readyVersionOne(), { type: "revision_started" });
    const failed = studioReducer(active, { type: "operation_failed", code });

    expect(failed.phase).toBe("conflict");
    expect(failed.errorCode).toBe(code);
    expect(canRetry(failed)).toBe(false);
  });

  it("allows only a retryable revision failure to retry", () => {
    const active = studioReducer(readyVersionOne(), { type: "revision_started" });
    const retryable = studioReducer(active, {
      type: "operation_failed",
      code: "revision_failed",
    });
    const final = studioReducer(active, {
      type: "operation_failed",
      code: "unsafe_hypothesis",
    });

    expect(retryable.phase).toBe("retryable_failure");
    expect(canRetry(retryable)).toBe(true);
    expect(studioReducer(retryable, { type: "retry_started" }).phase).toBe(
      "submitting_revision",
    );
    expect(final.phase).toBe("final_failure");
    expect(canRetry(final)).toBe(false);
  });

  it("deletion and reset remove both in-memory capabilities", () => {
    const ready = readyVersionOne();
    const deleting = studioReducer(ready, { type: "delete_started" });
    const reset = studioReducer(deleting, { type: "delete_succeeded" });

    expect(deleting.phase).toBe("deleting");
    expect(reset.phase).toBe("configure");
    expect(reset.upload).toBeUndefined();
    expect(reset.run).toBeUndefined();
    expect(reset.visibleVersions).toEqual([]);
    expect(canUpload(reset)).toBe(true);
  });

  it("ignores impossible events without corrupting state", () => {
    const initial = initialStudioState("china-to-uk");
    expect(
      studioReducer(initial, { type: "critic_succeeded", result: critique }),
    ).toBe(initial);
    expect(studioReducer(initial, { type: "revision_started" })).toBe(initial);
    expect(studioReducer(initial, { type: "delete_started" })).toBe(initial);
  });
});
