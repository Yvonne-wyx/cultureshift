import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BRAND_LOCK_FORM_SPEC } from "../brand-lock/brand-lock-form-spec";
import { loadFixture } from "../fixtures/fixture-loader";

import { BrandLockPreparation } from "./brand-lock-preparation";

const expectedKeys = [
  "logo_asset_id",
  "product_name",
  "verified_product_facts",
  "product_ui_asset_ids",
  "benefit_order",
  "cta_action_meaning",
  "layout_template_asset_id",
  "localizable_fields",
] as const;

describe("BrandLockPreparation", () => {
  it("defines every generated Brand Lock field in review order", () => {
    expect(BRAND_LOCK_FORM_SPEC.map((field) => field.key)).toEqual(expectedKeys);
    expect(BRAND_LOCK_FORM_SPEC.every((field) => field.help.length > 0)).toBe(true);
    expect(BRAND_LOCK_FORM_SPEC.every((field) => field.required)).toBe(true);
    expect(
      BRAND_LOCK_FORM_SPEC.find((field) => field.key === "verified_product_facts")
        ?.constraints,
    ).toEqual({ ordered: true, repeatable: true, minItems: 1, maxItems: 32 });
    expect(
      BRAND_LOCK_FORM_SPEC.find((field) => field.key === "product_ui_asset_ids")
        ?.constraints,
    ).toEqual({ ordered: true, repeatable: true, minItems: 1, maxItems: 16 });
    expect(
      BRAND_LOCK_FORM_SPEC.find((field) => field.key === "localizable_fields")
        ?.constraints,
    ).toEqual({
      repeatable: true,
      minItems: 1,
      maxItems: 4,
      allowedValues: ["narrative", "use_scenario", "trust_information", "language"],
    });
  });

  it.each(["china-to-uk", "uk-to-china"] as const)(
    "renders %s as a read-only Day 10 preparation",
    (fixtureId) => {
      const fixture = loadFixture(fixtureId);
      const directionLabel = fixtureId === "china-to-uk" ? "China to UK" : "UK to China";

      const { container } = render(<BrandLockPreparation fixture={fixture} />);

      expect(screen.getByText("awaiting_brand_lock")).toBeInTheDocument();
      expect(screen.getByText("Cultural hypotheses remain pending human review.")).toBeInTheDocument();
      expect(screen.getByAltText(`${directionLabel} source preview`)).toBeInTheDocument();
      expect(screen.getByAltText(`${directionLabel} target preview`)).toBeInTheDocument();
      expect(screen.getByAltText(`${directionLabel} logo asset preview`)).toBeInTheDocument();
      expect(screen.getByAltText(`${directionLabel} product UI asset preview`)).toBeInTheDocument();
      expect(
        screen.getByRole("figure", { name: `${directionLabel} layout template preview` }),
      ).toBeInTheDocument();
      for (const field of BRAND_LOCK_FORM_SPEC) {
        expect(screen.getByText(field.label)).toBeInTheDocument();
      }
      expect(screen.getByText(fixture.preview.brand_lock.product_name)).toBeInTheDocument();
      expect(
        screen.getByText(fixture.preview.brand_lock.logo_asset_id, { selector: "code" }),
      ).toBeInTheDocument();
      for (const fact of fixture.preview.brand_lock.verified_product_facts) {
        expect(screen.getByText(fact)).toBeInTheDocument();
      }
      for (const benefit of fixture.preview.brand_lock.benefit_order) {
        expect(screen.getByText(benefit)).toBeInTheDocument();
      }
      expect(
        screen.getByText(fixture.preview.brand_lock.cta_action_meaning),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Confirm Brand Lock — available Day 10" }),
      ).toBeDisabled();
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      expect(container.querySelector("form")).toBeNull();
    },
  );
});
