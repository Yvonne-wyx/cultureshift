import { describe, expect, it } from "vitest";

import type { RevisionCompleted } from "@/generated/contracts";
import {
  beginRevision,
  canSubmitRevision,
  failRevision,
  idleRevisionState,
  resolveRevision,
  selectRevisionChange,
} from "./revision-flow";

const completed = {
  result_version: 2,
  human_revision_count: 1,
} as RevisionCompleted;

describe("revision flow", () => {
  it("selects one or two supported changes without duplicates", () => {
    const headline = selectRevisionChange(
      idleRevisionState(),
      "shorten_headline",
    );
    const duplicate = selectRevisionChange(headline, "shorten_headline");
    const both = selectRevisionChange(duplicate, "shorten_body");

    expect(duplicate.selectedChanges).toEqual(["shorten_headline"]);
    expect(both.selectedChanges).toEqual(["shorten_headline", "shorten_body"]);
    expect(canSubmitRevision(both)).toBe(true);
  });

  it("disables submit with no selection or while active", () => {
    const idle = idleRevisionState();
    const selected = selectRevisionChange(idle, "shorten_body");

    expect(canSubmitRevision(idle)).toBe(false);
    expect(canSubmitRevision(beginRevision(selected))).toBe(false);
  });

  it("shows exactly versions one and two after success or replay", () => {
    const selected = selectRevisionChange(idleRevisionState(), "shorten_body");
    const succeeded = resolveRevision(beginRevision(selected), completed);
    const replayed = resolveRevision(succeeded, completed);

    expect(succeeded.phase).toBe("succeeded");
    expect(succeeded.visibleVersions).toEqual([1, 2]);
    expect(succeeded.result?.human_revision_count).toBe(1);
    expect(replayed.visibleVersions).toEqual([1, 2]);
  });

  it.each([
    "revision_limit_reached",
    "idempotency_conflict",
    "operation_in_progress",
  ] as const)("keeps %s as a distinct conflict", (code) => {
    const selected = selectRevisionChange(idleRevisionState(), "shorten_body");
    const failed = failRevision(beginRevision(selected), code);

    expect(failed.phase).toBe("conflict");
    expect(failed.conflictCode).toBe(code);
    expect(failed.canRetry).toBe(false);
  });

  it("allows only retryable technical failure to enable retry", () => {
    const selected = selectRevisionChange(idleRevisionState(), "shorten_body");
    const active = beginRevision(selected);

    expect(failRevision(active, "revision_failed").phase).toBe(
      "retryable_failure",
    );
    expect(failRevision(active, "revision_failed").canRetry).toBe(true);
    for (const code of ["retry_failed", "safety_refusal", "culture_review_required"] as const) {
      const failed = failRevision(active, code);
      expect(failed.phase).toBe("final_failure");
      expect(failed.canRetry).toBe(false);
    }
  });
});
