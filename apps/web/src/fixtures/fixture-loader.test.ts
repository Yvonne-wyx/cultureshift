import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import chinaToUkRaw from "./data/china-to-uk.json";
import ukToChinaRaw from "./data/uk-to-china.json";
import { loadFixture, listFixtureIds } from "./fixture-loader";
import { validateFixture } from "./fixture-validation";
import type { FixtureId } from "./types";

const SECRET = "fixture-secret-sentinel";

function cloneChinaToUk(): Record<string, unknown> {
  return structuredClone(chinaToUkRaw) as Record<string, unknown>;
}

function cloneUkToChina(): Record<string, unknown> {
  return structuredClone(ukToChinaRaw) as Record<string, unknown>;
}

function expectInvalidValue(
  fixture: unknown,
  code: string,
  expectedId: FixtureId = "china-to-uk",
): void {
  let error: unknown;
  try {
    validateFixture(fixture, expectedId);
  } catch (caught) {
    error = caught;
  }

  expect(error).toEqual(new Error(`Invalid fixture: ${code}`));
  expect(String(error)).not.toContain(SECRET);
}

function expectInvalid(
  mutate: (fixture: Record<string, unknown>) => void,
  code: string,
): void {
  const fixture = cloneChinaToUk();
  mutate(fixture);
  expectInvalidValue(fixture, code);
}

describe("fixture loader", () => {
  it("lists the two stable fixture IDs", () => {
    expect(listFixtureIds()).toEqual(["china-to-uk", "uk-to-china"]);
  });

  it("loads the approved bilateral directions in fixture mode", () => {
    expect(loadFixture("china-to-uk").request.direction).toBe("china_to_uk");
    expect(loadFixture("uk-to-china").request.direction).toBe("uk_to_china");
    expect(loadFixture("china-to-uk").request.execution_mode).toBe("fixture");
  });

  it("loads only the exact approved source asset identity for each direction", () => {
    expect(loadFixture("china-to-uk")).toMatchObject({
      request: {
        direction: "china_to_uk",
        source_asset: {
          asset_id: "b1111111-1111-4111-8111-111111111111",
          kind: "source_ad",
          media_type: "image/svg+xml",
          sha256: "58c22343c4cc16ee3ba25bdeed5c897dce442426d9b500a7a2704edeac3ccc39",
          provenance_ref: "fixture:orbit-ai-source-zh-cn-001",
          rights_ref: "rights:demo-assets-manifest",
        },
      },
      preview: {
        source_asset_path: "/fixtures/orbit-ai/source-zh-cn.svg",
      },
    });
    expect(loadFixture("uk-to-china")).toMatchObject({
      request: {
        direction: "uk_to_china",
        source_asset: {
          asset_id: "b2222222-2222-4222-8222-222222222222",
          kind: "source_ad",
          media_type: "image/svg+xml",
          sha256: "f85f732a435126690b2908508597cc800e7b99fc07b98c9a035bddd0b9091d68",
          provenance_ref: "fixture:orbit-ai-source-en-gb-001",
          rights_ref: "rights:demo-assets-manifest",
        },
      },
      preview: {
        source_asset_path: "/fixtures/orbit-ai/source-en-gb.svg",
      },
    });
  });

  it.each([
    ["china-to-uk", "39d3233aa64533558579a5d9ad0ff345105555ea4ae69dfd8c26f5faaddb0d15", "../../public/fixtures/orbit-ai/composed-china-to-uk.png"],
    ["uk-to-china", "e64f1342a728d561c141accf9cf78b5d43f251b5f550cf7be616a00da049517f", "../../public/fixtures/orbit-ai/composed-uk-to-china.png"],
  ] as const)("loads exact Day 12 composition evidence for %s", (fixtureId, sha256, previewPath) => {
    const fixture = loadFixture(fixtureId);
    expect(fixture.composition).toMatchObject({
      execution_mode: "fixture",
      width: 1600,
      height: 900,
      media_type: "image/png",
      rendered_sha256: sha256,
      disclosure: "Fixture Demo / 非实时模型",
      font: {
        path: "assets/fonts/NotoSansCJKsc-Regular.otf",
        upstream_commit: "f8d157532fbfaeda587e826d4cd5b21a49186f7c",
      },
    });
    expect(fixture.composition.layers.map((layer) => layer.kind)).toEqual([
      "background", "product_ui", "logo", "headline", "body", "cta", "disclosure",
    ]);
    expect(fixture.composition.layers[1].source_asset_id).toBe(
      fixture.request.brand_lock.product_ui_asset_ids[0],
    );
    expect(fixture.composition.layers[2].source_asset_id).toBe(
      fixture.request.brand_lock.logo_asset_id,
    );
    const preview = readFileSync(fileURLToPath(new URL(previewPath, import.meta.url)));
    expect(createHash("sha256").update(preview).digest("hex")).toBe(sha256);
  });

  it("loads exact bilateral Day 11 draft evidence", () => {
    expect(loadFixture("china-to-uk").draft).toMatchObject({
      brief: { direction: "china_to_uk", target_locale: "en-GB" },
      copy: { locale: "en-GB", cta_action_meaning: "Start a fixture demo" },
      rule_ids: ["ZEU-S1", "ZEU-S3"],
      prompt_summary: "Use verified facts and ZEU-S1/ZEU-S3; preserve Brand Lock.",
    });
    expect(loadFixture("uk-to-china").draft).toMatchObject({
      brief: { direction: "uk_to_china", target_locale: "zh-CN" },
      copy: { locale: "zh-CN", cta_action_meaning: "Start a fixture demo" },
      rule_ids: ["EZC-S1", "EZC-S3"],
      prompt_summary: "仅使用已验证事实与 EZC-S1/EZC-S3；保持品牌锁定。",
    });
  });

  it("rejects Day 11 draft rule, lock, and hypothesis drift", () => {
    expectInvalid((fixture) => {
      const draft = fixture.draft as Record<string, unknown>;
      draft.rule_ids = ["EZC-S1", "EZC-S3"];
    }, "invalid_draft");
    expectInvalid((fixture) => {
      const draft = fixture.draft as Record<string, Record<string, unknown>>;
      const brief = draft.brief;
      brief.brand_lock = {
        ...(brief.brand_lock as Record<string, unknown>),
        product_name: SECRET,
      };
    }, "invalid_draft");
    expectInvalid((fixture) => {
      const draft = fixture.draft as Record<string, Record<string, unknown>>;
      const hypotheses = draft.brief.hypotheses as Array<Record<string, unknown>>;
      hypotheses[0].review_status = "accepted";
    }, "invalid_draft");
  });

  it.each([
    ["china-to-uk", "../../public/fixtures/orbit-ai/source-zh-cn.svg"],
    ["uk-to-china", "../../public/fixtures/orbit-ai/source-en-gb.svg"],
  ] as const)("keeps %s source copy identical to the visible committed SVG", (id, path) => {
    const fixture = loadFixture(id);
    const svg = readFileSync(fileURLToPath(new URL(path, import.meta.url)), "utf8");

    expect(svg).toContain(fixture.preview.source_copy.headline);
    expect(svg).toContain(fixture.preview.source_copy.body);
  });

  it("keeps both source creatives and localized proposals on the approved-notes concept", () => {
    const chinaToUk = loadFixture("china-to-uk");
    const ukToChina = loadFixture("uk-to-china");

    expect(chinaToUk.preview.source_copy).toEqual({
      headline: "把已批准笔记整理成任务摘要",
      body: "Orbit AI 将已批准的会议笔记转成清晰的任务摘要。",
    });
    expect(chinaToUk.preview.localized_copy.headline).toContain("approved notes");
    expect(chinaToUk.preview.localized_copy.body).toContain("approved meeting notes");

    expect(ukToChina.preview.source_copy).toEqual({
      headline: "Turn approved notes into clear task summaries",
      body: "Orbit AI helps teams organise approved meeting notes into task summaries.",
    });
    expect(ukToChina.preview.localized_copy.headline).toContain("已批准");
    expect(ukToChina.preview.localized_copy.body).toContain("已批准");
  });

  it("rejects source asset values that are safe-looking but not approved", () => {
    const mutations: Array<(fixture: Record<string, unknown>) => void> = [
      (fixture) => {
        const request = fixture.request as Record<string, Record<string, unknown>>;
        request.source_asset.sha256 = "f".repeat(64);
      },
      (fixture) => {
        const preview = fixture.preview as Record<string, unknown>;
        preview.source_asset_path = "/fixtures/orbit-ai/orbit-ai-logo.svg";
      },
      (fixture) => {
        const request = fixture.request as Record<string, Record<string, unknown>>;
        request.source_asset.provenance_ref = "fixture:unknown-source-001";
      },
      (fixture) => {
        const request = fixture.request as Record<string, Record<string, unknown>>;
        request.source_asset.rights_ref = "rights:unknown-manifest";
      },
    ];

    for (const mutate of mutations) {
      const fixture = cloneChinaToUk();
      mutate(fixture);
      expectInvalidValue(fixture, "source_asset_mismatch");
    }

    const englishFixture = cloneUkToChina();
    const request = englishFixture.request as Record<string, Record<string, unknown>>;
    request.source_asset.asset_id = "b1111111-1111-4111-8111-111111111111";
    expectInvalidValue(englishFixture, "source_asset_mismatch", "uk-to-china");
  });

  it("preserves and freezes the shared Brand Lock", () => {
    expect(loadFixture("china-to-uk").preview.brand_lock).toEqual(
      loadFixture("uk-to-china").preview.brand_lock,
    );
    expect(Object.isFrozen(loadFixture("china-to-uk").preview.brand_lock)).toBe(true);
  });

  it("rejects unapproved validation boundary changes without disclosing values", () => {
    expectInvalid((fixture) => {
      (fixture.request as Record<string, unknown>).execution_mode = `live_${SECRET}`;
    }, "live_execution");
    expectInvalid((fixture) => {
      (fixture.preview as Record<string, unknown>).source_asset_path = `C:\\${SECRET}.svg`;
    }, "unsafe_asset_path");
    expectInvalid((fixture) => {
      (fixture.request as Record<string, unknown>).source_asset = {
        ...(fixture.request as Record<string, Record<string, unknown>>).source_asset,
        rights_ref: `private:${SECRET}`,
      };
    }, "rights_missing");
    expectInvalid((fixture) => {
      (fixture.preview as Record<string, unknown>).brand_lock = {
        ...((fixture.preview as Record<string, Record<string, unknown>>).brand_lock),
        product_name: SECRET,
      };
    }, "brand_lock_mismatch");
    expectInvalid((fixture) => {
      const preview = fixture.preview as Record<string, unknown>;
      const hypotheses = preview.hypotheses as Array<Record<string, unknown>>;
      hypotheses[0].review_status = `accepted_${SECRET}`;
    }, "hypothesis_not_pending");
  });

  it("rejects matching bilateral Brand Lock drift", () => {
    expectInvalid((fixture) => {
      const request = fixture.request as Record<string, Record<string, unknown>>;
      const preview = fixture.preview as Record<string, Record<string, unknown>>;
      request.brand_lock.product_name = SECRET;
      preview.brand_lock.product_name = SECRET;
    }, "brand_lock_mismatch");
  });

  it("rejects exotic objects at the fixture boundary", () => {
    class ExoticFixture {
      fixture_id = SECRET;
    }

    expectInvalidValue(new ExoticFixture(), "invalid_shape");
  });

  it("rejects an incorrect bilateral hypothesis mapping", () => {
    expectInvalid((fixture) => {
      const preview = fixture.preview as Record<string, unknown>;
      const hypotheses = preview.hypotheses as Array<Record<string, unknown>>;
      hypotheses[0].hypothesis_id = "c9999999-9999-4999-8999-999999999999";
    }, "hypothesis_mapping");
    expectInvalid((fixture) => {
      const preview = fixture.preview as Record<string, unknown>;
      const hypotheses = preview.hypotheses as Array<Record<string, unknown>>;
      hypotheses[0].evidence_refs = [`evidence:${SECRET}`];
    }, "hypothesis_mapping");
    expectInvalid((fixture) => {
      const preview = fixture.preview as Record<string, unknown>;
      const hypotheses = preview.hypotheses as Array<Record<string, unknown>>;
      hypotheses.push(structuredClone(hypotheses[0]));
    }, "hypothesis_mapping");
  });
});
