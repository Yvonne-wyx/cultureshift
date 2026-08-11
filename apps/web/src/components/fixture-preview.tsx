import Image from "next/image";

import type { FixtureBundle } from "../fixtures/types";

import styles from "./fixture-preview.module.css";

const DIRECTION_LABELS: Readonly<Record<FixtureBundle["fixture_id"], string>> = {
  "china-to-uk": "China to UK",
  "uk-to-china": "UK to China",
};

export function FixturePreview({
  fixture,
}: {
  fixture: Readonly<FixtureBundle>;
}) {
  const { preview } = fixture;
  const directionLabel = DIRECTION_LABELS[fixture.fixture_id];
  const articleName = `${directionLabel}: ${fixture.source_locale} to ${fixture.target_locale}`;

  return (
    <article className={styles.card} aria-label={articleName}>
      <header className={styles.header}>
        <p className={styles.disclosure}>{fixture.disclosure}</p>
        <h2 className={styles.direction}>{directionLabel}</h2>
        <p className={styles.locales}>
          <span>{fixture.source_locale}</span>
          <span aria-hidden="true">→</span>
          <span>{fixture.target_locale}</span>
        </p>
      </header>

      <section className={styles.section} aria-labelledby={`${fixture.fixture_id}-source`}>
        <h3 id={`${fixture.fixture_id}-source`}>Source creative</h3>
        <Image
          className={styles.sourceCreative}
          src={preview.source_asset_path}
          alt="Source creative"
          width={960}
          height={540}
          sizes="(max-width: 640px) 100vw, 640px"
        />
        <p>{preview.source_copy.headline}</p>
        <p>{preview.source_copy.body}</p>
      </section>

      <section className={styles.proposal} aria-labelledby={`${fixture.fixture_id}-proposal`}>
        <div className={styles.brandRow}>
          <Image
            src={preview.logo_asset_path}
            alt="Orbit AI"
            width={120}
            height={32}
          />
          <span className={styles.pendingBadge}>Human review required</span>
        </div>
        <h3 id={`${fixture.fixture_id}-proposal`}>{preview.localized_copy.headline}</h3>
        <p>{preview.localized_copy.body}</p>
        <p className={styles.cta}>{preview.localized_copy.cta_label}</p>
        <Image
          className={styles.productUi}
          src={preview.product_ui_asset_path}
          alt="Orbit AI product interface"
          width={560}
          height={315}
          sizes="(max-width: 640px) 100vw, 560px"
        />
      </section>

      <section className={styles.section} aria-labelledby={`${fixture.fixture_id}-brand-lock`}>
        <h3 id={`${fixture.fixture_id}-brand-lock`}>Brand Lock</h3>
        <dl className={styles.definitionList}>
          <div>
            <dt>Logo asset ID</dt>
            <dd><code>{preview.brand_lock.logo_asset_id}</code></dd>
          </div>
          <div>
            <dt>Product name</dt>
            <dd>{preview.brand_lock.product_name}</dd>
          </div>
          <div>
            <dt>Verified product facts</dt>
            <dd>
              <ul>
                {preview.brand_lock.verified_product_facts.map((fact) => (
                  <li key={fact}>{fact}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Product UI asset IDs</dt>
            <dd>
              <ul>
                {preview.brand_lock.product_ui_asset_ids.map((assetId) => (
                  <li key={assetId}><code>{assetId}</code></li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Benefit order</dt>
            <dd>
              <ol>
                {preview.brand_lock.benefit_order.map((benefit) => (
                  <li key={benefit}>{benefit}</li>
                ))}
              </ol>
            </dd>
          </div>
          <div>
            <dt>CTA action meaning</dt>
            <dd>{preview.brand_lock.cta_action_meaning}</dd>
          </div>
          <div>
            <dt>Layout template asset ID</dt>
            <dd><code>{preview.brand_lock.layout_template_asset_id}</code></dd>
          </div>
          <div>
            <dt>Localizable fields</dt>
            <dd>
              <ul>
                {preview.brand_lock.localizable_fields.map((field) => (
                  <li key={field}><code>{field}</code></li>
                ))}
              </ul>
            </dd>
          </div>
        </dl>
      </section>

      <section className={styles.section} aria-labelledby={`${fixture.fixture_id}-traceability`}>
        <h3 id={`${fixture.fixture_id}-traceability`}>Traceability</h3>
        <h4>Rules</h4>
        <ul className={styles.tagList}>
          {preview.rule_ids.map((ruleId) => (
            <li key={ruleId}>{ruleId}</li>
          ))}
        </ul>
        <h4>Pending hypotheses</h4>
        <ul className={styles.hypothesisList}>
          {preview.hypotheses.map((hypothesis) => {
            const reviewStatus =
              hypothesis.review_status === "pending"
                ? "Pending review"
                : "Review status unavailable";

            return (
              <li key={hypothesis.hypothesis_id}>
                <strong>{hypothesis.hypothesis_id}</strong>
                <span className={styles.hypothesisStatus}>{reviewStatus}</span>
                <span>{hypothesis.claim}</span>
                <span className={styles.evidenceLabel}>Evidence references</span>
                <ul className={styles.evidenceList}>
                  {hypothesis.evidence_refs.map((evidenceRef) => (
                    <li key={evidenceRef}>{evidenceRef}</li>
                  ))}
                </ul>
              </li>
            );
          })}
        </ul>
      </section>

      <footer className={styles.footer}>
        <p>{preview.limitation}</p>
      </footer>
    </article>
  );
}
