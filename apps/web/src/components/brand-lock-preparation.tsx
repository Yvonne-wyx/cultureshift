import Image from "next/image";
import type { ReactNode } from "react";

import { BRAND_LOCK_FORM_SPEC } from "../brand-lock/brand-lock-form-spec";
import type { FixtureBundle } from "../fixtures/types";
import type { BrandLock } from "../generated/contracts";

import styles from "./brand-lock-preparation.module.css";

const DIRECTION_LABELS: Readonly<Record<FixtureBundle["fixture_id"], string>> = {
  "china-to-uk": "China to UK",
  "uk-to-china": "UK to China",
};

function codeList(values: readonly string[]): ReactNode {
  return <ul>{values.map((value) => <li key={value}><code>{value}</code></li>)}</ul>;
}

function textList(values: readonly string[], ordered = false): ReactNode {
  const items = values.map((value) => <li key={value}>{value}</li>);
  return ordered ? <ol>{items}</ol> : <ul>{items}</ul>;
}

function renderValue(key: keyof BrandLock, brandLock: BrandLock): ReactNode {
  switch (key) {
    case "logo_asset_id":
      return <code>{brandLock.logo_asset_id}</code>;
    case "product_name":
      return brandLock.product_name;
    case "verified_product_facts":
      return textList(brandLock.verified_product_facts);
    case "product_ui_asset_ids":
      return codeList(brandLock.product_ui_asset_ids);
    case "benefit_order":
      return textList(brandLock.benefit_order, true);
    case "cta_action_meaning":
      return brandLock.cta_action_meaning;
    case "layout_template_asset_id":
      return <code>{brandLock.layout_template_asset_id}</code>;
    case "localizable_fields":
      return codeList(brandLock.localizable_fields);
  }
}

function renderFieldPreview(
  key: keyof BrandLock,
  fixture: Readonly<FixtureBundle>,
  directionLabel: string,
): ReactNode {
  switch (key) {
    case "logo_asset_id":
      return (
        <Image
          className={styles.fieldPreview}
          src={fixture.preview.logo_asset_path}
          alt={`${directionLabel} logo asset preview`}
          width={320}
          height={120}
        />
      );
    case "product_ui_asset_ids":
      return (
        <Image
          className={styles.fieldPreview}
          src={fixture.preview.product_ui_asset_path}
          alt={`${directionLabel} product UI asset preview`}
          width={560}
          height={315}
        />
      );
    case "layout_template_asset_id":
      return (
        <figure
          className={styles.layoutPreview}
          aria-label={`${directionLabel} layout template preview`}
        >
          <strong>{fixture.preview.localized_copy.headline}</strong>
          <p>{fixture.preview.localized_copy.body}</p>
          <span>{fixture.preview.localized_copy.cta_label}</span>
        </figure>
      );
    default:
      return null;
  }
}

export function BrandLockPreparation({
  fixture,
}: {
  fixture: Readonly<FixtureBundle>;
}) {
  const headingId = `${fixture.fixture_id}-brand-lock-preparation`;
  const directionLabel = DIRECTION_LABELS[fixture.fixture_id];
  const brandLock = fixture.preview.brand_lock;

  return (
    <section className={styles.preparation} aria-labelledby={headingId}>
      <div className={styles.headingRow}>
        <div>
          <p className={styles.eyebrow}>Day 9 · read-only preparation</p>
          <h2 id={headingId}>Brand Lock confirmation preparation</h2>
        </div>
        <code className={styles.status}>awaiting_brand_lock</code>
      </div>
      <p>Review the complete lock and bilateral preview before Day 10 confirmation.</p>
      <p>Cultural hypotheses remain pending human review.</p>

      <div className={styles.previews}>
        <figure>
          <Image
            src={fixture.preview.source_asset_path}
            alt={`${directionLabel} source preview`}
            width={960}
            height={540}
          />
          <figcaption>Source · {fixture.source_locale}</figcaption>
        </figure>
        <figure>
          <Image
            src={fixture.preview.product_ui_asset_path}
            alt={`${directionLabel} target preview`}
            width={560}
            height={315}
          />
          <figcaption>Target layout context · {fixture.target_locale}</figcaption>
        </figure>
      </div>

      <dl className={styles.fields}>
        {BRAND_LOCK_FORM_SPEC.map((field) => (
          <div key={field.key}>
            <dt>{field.label}</dt>
            <dd>{renderValue(field.key, brandLock)}</dd>
            <p>{field.help}</p>
            <small>Planned control: {field.control.replaceAll("_", " ")}</small>
            {field.preview ? renderFieldPreview(field.key, fixture, directionLabel) : null}
          </div>
        ))}
      </dl>

      <button type="button" disabled>
        Confirm Brand Lock — available Day 10
      </button>
    </section>
  );
}
