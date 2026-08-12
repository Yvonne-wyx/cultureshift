import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { loadFixture } from "../fixtures/fixture-loader";

import { FixturePreview } from "./fixture-preview";

const fixtureIds = ["china-to-uk", "uk-to-china"] as const;
const directionLabels = {
  "china-to-uk": "China to UK",
  "uk-to-china": "UK to China",
} as const;

describe("FixturePreview", () => {
  it("renders every protected Brand Lock category and literal value", () => {
    render(<FixturePreview fixture={loadFixture("china-to-uk")} />);

    expect(screen.getByText("Logo asset ID")).toBeInTheDocument();
    expect(
      screen.getByText("a1111111-1111-4111-8111-111111111111", { selector: "code" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Product name")).toBeInTheDocument();
    expect(screen.getAllByText("Orbit AI").length).toBeGreaterThan(0);
    expect(screen.getByText("Verified product facts")).toBeInTheDocument();
    expect(
      screen.getByText("Turns approved notes into task summaries"),
    ).toBeInTheDocument();
    expect(screen.getByText("Product UI asset IDs")).toBeInTheDocument();
    expect(
      screen.getByText("a2222222-2222-4222-8222-222222222222", {
        selector: "code",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Benefit order")).toBeInTheDocument();
    expect(screen.getByText("Summarize")).toBeInTheDocument();
    expect(screen.getByText("Organize")).toBeInTheDocument();
    expect(screen.getByText("CTA action meaning")).toBeInTheDocument();
    expect(screen.getByText("Start a fixture demo")).toBeInTheDocument();
    expect(screen.getByText("Layout template asset ID")).toBeInTheDocument();
    expect(
      screen.getByText("a3333333-3333-4333-8333-333333333333", {
        selector: "code",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Localizable fields")).toBeInTheDocument();
    expect(screen.getByText("narrative")).toBeInTheDocument();
    expect(screen.getByText("use_scenario")).toBeInTheDocument();
    expect(screen.getByText("trust_information")).toBeInTheDocument();
    expect(screen.getByText("language")).toBeInTheDocument();
  });

  it.each(fixtureIds)("renders the %s fixture without interactive claims", (id) => {
    const fixture = loadFixture(id);
    const { container } = render(<FixturePreview fixture={fixture} />);
    const directionLabel = directionLabels[id];

    expect(
      screen.getByRole("heading", { level: 2, name: directionLabel }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("article", {
        name: `${directionLabel}: ${fixture.source_locale} to ${fixture.target_locale}`,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(fixture.source_locale)).toBeInTheDocument();
    expect(screen.getByText(fixture.target_locale)).toBeInTheDocument();
    expect(screen.getByAltText("Source creative")).toHaveAttribute(
      "src",
      expect.stringContaining("/fixtures/orbit-ai/"),
    );

    expect(
      screen.getByRole("heading", { name: fixture.preview.localized_copy.headline }),
    ).toBeInTheDocument();
    expect(screen.getByText(fixture.preview.localized_copy.body)).toBeInTheDocument();
    expect(screen.getByText(fixture.preview.localized_copy.cta_label)).toBeInTheDocument();
    expect(screen.getAllByText("Orbit AI").length).toBeGreaterThan(0);
    for (const fact of fixture.preview.brand_lock.verified_product_facts) {
      expect(screen.getByText(fact)).toBeInTheDocument();
    }
    for (const ruleId of fixture.preview.rule_ids) {
      expect(screen.getByText(ruleId)).toBeInTheDocument();
    }
    for (const hypothesis of fixture.preview.hypotheses) {
      expect(screen.getByText(hypothesis.hypothesis_id)).toBeInTheDocument();
      for (const evidenceRef of hypothesis.evidence_refs) {
        expect(screen.getByText(evidenceRef)).toBeInTheDocument();
      }
    }
    expect(screen.getAllByText("Pending review")).toHaveLength(
      fixture.preview.hypotheses.length,
    );
    expect(screen.getByText("Human review required")).toBeInTheDocument();
    expect(screen.getAllByText("Fixture Demo / 非实时模型")).toHaveLength(1);

    const limitation = screen.getByText(fixture.preview.limitation);
    expect(limitation).toBeInTheDocument();
    expect(limitation.textContent).not.toMatch(/approval|correctness|compliance|uplift/i);
    expect(screen.getByRole("link", { name: `View ${directionLabel} result` })).toHaveAttribute(
      "href",
      `/results/${id}`,
    );
    expect(
      container.querySelectorAll(
        'button, input, textarea, select, form, [contenteditable]:not([contenteditable="false"])',
      ),
    ).toHaveLength(0);
    expect(container.querySelectorAll("[data-watermark]")).toHaveLength(0);
  });
});
