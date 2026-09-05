import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BRAND_LOCK_FORM_SPEC } from "../brand-lock/brand-lock-form-spec";
import { loadFixture } from "../fixtures/fixture-loader";
import type { BrandLockConfirmed } from "../generated/contracts";

import { BrandLockForm } from "./brand-lock-form";

function renderForm(confirmBrandLock = vi.fn()) {
  const fixture = loadFixture("china-to-uk");
  return {
    fixture,
    confirmBrandLock,
    ...render(
      <BrandLockForm
        initialBrandLock={fixture.preview.brand_lock}
        directionLabel="China to UK"
        logoAssetPath={fixture.preview.logo_asset_path}
        productUiAssetPath={fixture.preview.product_ui_asset_path}
        layoutPreview={fixture.preview.localized_copy}
        confirmBrandLock={confirmBrandLock}
      />,
    ),
  };
}

describe("BrandLockForm", () => {
  it("shows the full lock while exposing only the two approved mutations", () => {
    const { container, fixture } = renderForm();

    expect(BRAND_LOCK_FORM_SPEC.map((field) => field.key)).toEqual([
      "logo_asset_id",
      "product_name",
      "verified_product_facts",
      "product_ui_asset_ids",
      "benefit_order",
      "cta_action_meaning",
      "layout_template_asset_id",
      "localizable_fields",
    ]);
    for (const field of BRAND_LOCK_FORM_SPEC) {
      expect(screen.getByText(field.label)).toBeInTheDocument();
    }
    expect(screen.getByText(fixture.preview.brand_lock.product_name)).toBeInTheDocument();
    expect(screen.getByAltText("China to UK logo asset preview")).toBeInTheDocument();
    expect(screen.getByAltText("China to UK product UI asset preview")).toBeInTheDocument();
    expect(
      screen.getByRole("figure", { name: "China to UK layout template preview" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(container.querySelector('input[type="file"]')).toBeNull();
    expect(screen.getAllByRole("checkbox")).toHaveLength(5);
    expect(screen.getByRole("checkbox", { name: /become immutable/i })).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Confirm Brand Lock" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move Organize up" })).toBeEnabled();
  });

  it("submits a complete reordered snapshot and becomes immutable", async () => {
    const confirmation = vi.fn(async (brandLock): Promise<BrandLockConfirmed> => ({
      run_id: "a1111111-1111-4111-8111-111111111111",
      status: "in_progress",
      brand_lock: brandLock,
      confirmed_at: "2026-08-20T00:00:00Z",
    }));
    const { fixture } = renderForm(confirmation);

    fireEvent.click(screen.getByRole("button", { name: "Move Organize up" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "language" }));
    fireEvent.click(screen.getByRole("checkbox", { name: /become immutable/i }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));

    await waitFor(() => expect(confirmation).toHaveBeenCalledTimes(1));
    expect(confirmation).toHaveBeenCalledWith({
      ...fixture.preview.brand_lock,
      benefit_order: ["Organize", "Summarize"],
      localizable_fields: ["narrative", "use_scenario", "trust_information"],
    });
    expect(await screen.findByText(/Brand Lock confirmed and immutable/)).toBeInTheDocument();
    expect(screen.getByText("in_progress")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm Brand Lock" })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: "narrative" })).toBeDisabled();
  });

  it("disables empty confirmation and sanitizes an unexpected failure", async () => {
    const confirmation = vi.fn().mockRejectedValue(new Error("private marker"));
    renderForm(confirmation);
    for (const checkbox of screen.getAllByRole("checkbox", { name: /^(narrative|use_scenario|trust_information|language)$/ })) fireEvent.click(checkbox);
    expect(screen.getByRole("button", { name: "Confirm Brand Lock" })).toBeDisabled();

    fireEvent.click(screen.getByRole("checkbox", { name: "narrative" }));
    fireEvent.click(screen.getByRole("checkbox", { name: /become immutable/i }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to confirm Brand Lock.",
    );
    expect(screen.getByRole("alert")).not.toHaveTextContent("private marker");
  });

  it("locks all mutation controls while confirmation is pending", () => {
    const confirmation = vi.fn(() => new Promise<BrandLockConfirmed>(() => undefined));
    renderForm(confirmation);

    fireEvent.click(screen.getByRole("checkbox", { name: /become immutable/i }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));

    expect(screen.getByRole("button", { name: "Confirming…" })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: "narrative" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Move Organize up" })).toBeDisabled();
  });
});
