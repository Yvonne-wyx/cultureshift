"use client";

import type { FixtureBundle } from "../fixtures/types";
import type { BrandLock } from "../generated/contracts";

import { BrandLockForm } from "./brand-lock-form";

const DIRECTION_LABELS: Readonly<Record<FixtureBundle["fixture_id"], string>> = {
  "china-to-uk": "China to UK",
  "uk-to-china": "UK to China",
};

export function FixtureBrandLockForm({ fixture }: { fixture: Readonly<FixtureBundle> }) {
  async function confirmFixture(brandLock: BrandLock) {
    return {
      run_id: fixture.request.source_asset.asset_id,
      status: "in_progress" as const,
      brand_lock: brandLock,
      confirmed_at: "2026-08-20T00:00:00Z",
    };
  }

  return (
    <div>
      <p><strong>Fixture confirmation only</strong> — no production record is changed.</p>
      <BrandLockForm
        initialBrandLock={fixture.preview.brand_lock}
        directionLabel={DIRECTION_LABELS[fixture.fixture_id]}
        logoAssetPath={fixture.preview.logo_asset_path}
        productUiAssetPath={fixture.preview.product_ui_asset_path}
        layoutPreview={fixture.preview.localized_copy}
        confirmBrandLock={confirmFixture}
      />
    </div>
  );
}
