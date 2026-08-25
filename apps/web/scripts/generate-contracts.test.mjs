import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { renderContracts, syncGeneratedFile } from "./generate-contracts.mjs";

describe("generated contract freshness", () => {
  it("fails closed when committed output is stale", () => {
    const directory = mkdtempSync(join(tmpdir(), "cultureshift-contracts-"));
    const output = join(directory, "contracts.ts");
    writeFileSync(output, "stale\n", "utf8");
    expect(() => syncGeneratedFile("fresh\n", output, true)).toThrow("stale");
  });
});

describe("generated public contract types", () => {
  it("preserves safety literals and the ResultVersion object name", async () => {
    const output = await renderContracts();
    expect(output).toMatch(/export interface ResultVersion \{/);
    expect(output).not.toContain("ResultVersion1");
    expect(output).toContain('export type ExecutionMode = "fixture" | "live";');
    expect(output).toContain('export type FixtureExecutionMode = "fixture";');
    expect(output).toMatch(/execution_mode: FixtureExecutionMode;/);
    expect(output).toContain('export type SourceAssetKind = "source_ad";');
    expect(output).toMatch(/kind: SourceAssetKind;/);
    expect(output).toMatch(/export interface AdAnalysis \{[\s\S]*?source_asset: SourceAdAssetRef;/);
    expect(output).toMatch(/"pass" \| "revise" \| "needs_human_review" \| "reject"/);
    expect(output).toMatch(/"brand_lock" \| "fact" \| "readability" \| "culture" \| "safety"/);
    expect(output).toContain(
      'export type RevisionChange = "shorten_headline" | "shorten_body";',
    );
    expect(output).toMatch(/export interface RevisionCompleted \{/);
  });
});
