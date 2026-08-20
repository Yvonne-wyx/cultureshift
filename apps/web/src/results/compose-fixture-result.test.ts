import { describe, expect, it } from "vitest";

import { loadFixture } from "../fixtures/fixture-loader";

import { composeFixtureResult } from "./compose-fixture-result";

describe("composeFixtureResult", () => {
  it.each(["china-to-uk", "uk-to-china"] as const)(
    "composes %s deterministically without changing the fixture",
    (fixtureId) => {
      const fixture = loadFixture(fixtureId);
      const before = JSON.stringify(fixture);
      const first = composeFixtureResult(fixture);
      const second = composeFixtureResult(fixture);

      expect(first).toEqual(second);
      expect(first).not.toBe(second);
      expect(JSON.stringify(fixture)).toBe(before);
      expect(Object.isFrozen(first)).toBe(true);
      expect(Object.isFrozen(first.brand_lock)).toBe(true);
      expect(Object.isFrozen(first.hypotheses)).toBe(true);
      expect(Object.isFrozen(first.draft)).toBe(true);
      expect(Object.isFrozen(first.draft.brief.brand_lock)).toBe(true);
      expect(first.draft.rule_ids).toEqual(first.rule_ids);
      expect(first.watermark).toBe("Fixture Demo / 非实时模型");
      expect(first.walkthrough.map((step) => step.title)).toEqual([
        "1. Review source",
        "2. Inspect proposal",
        "3. Verify traceability",
      ]);
    },
  );
});
