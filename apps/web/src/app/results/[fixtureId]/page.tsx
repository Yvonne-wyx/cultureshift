import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { FixtureBrandLockForm } from "../../../components/fixture-brand-lock-form";
import { DraftEvidence } from "../../../components/draft-evidence";
import { listFixtureIds, loadFixture } from "../../../fixtures/fixture-loader";
import type { FixtureId } from "../../../fixtures/types";
import { composeFixtureResult } from "../../../results/compose-fixture-result";

import styles from "./result.module.css";

export function generateStaticParams() {
  return listFixtureIds().map((fixtureId) => ({ fixtureId }));
}

function isFixtureId(value: string): value is FixtureId {
  return listFixtureIds().includes(value as FixtureId);
}

export default async function ResultPage({
  params,
}: {
  params: Promise<{ fixtureId: string }>;
}) {
  const { fixtureId } = await params;
  if (!isFixtureId(fixtureId)) notFound();
  const fixture = loadFixture(fixtureId);
  const result = composeFixtureResult(fixture);

  return (
    <main className={styles.page}>
      <p className={styles.watermark} data-watermark={result.watermark}>{result.watermark}</p>
      <header className={styles.header}>
        <Link href="/">← Fixture lab</Link>
        <h1>Localized fixture result</h1>
        <p>{result.direction_label}: {result.source_locale} → {result.target_locale}</p>
      </header>

      <ol className={styles.walkthrough} aria-label="Three-step walkthrough">
        {result.walkthrough.map((step) => (
          <li key={step.title}><strong>{step.title}</strong><span>{step.description}</span></li>
        ))}
      </ol>

      <div className={styles.comparison}>
        <section className={styles.panel} aria-labelledby="source-heading">
          <h2 id="source-heading">Source creative</h2>
          <Image src={result.source.asset_path} alt="Source creative" width={960} height={540} />
          <h3>{result.source.headline}</h3><p>{result.source.body}</p>
        </section>
        <section className={styles.panel} aria-labelledby="proposal-heading">
          <div className={styles.statusRow}>
            <Image src={result.proposal.logo_asset_path} alt="Orbit AI" width={120} height={32} />
            <strong>Human review required</strong>
          </div>
          <h2 id="proposal-heading">Localized proposal</h2>
          <h3>{result.proposal.headline}</h3><p>{result.proposal.body}</p>
          <p className={styles.cta}>{result.proposal.cta_label}</p>
          <Image src={result.proposal.product_ui_asset_path} alt="Orbit AI product interface" width={560} height={315} />
        </section>
      </div>

      <section className={styles.details} aria-labelledby="brand-lock-heading">
        <h2 id="brand-lock-heading">Brand Lock</h2>
        <dl>
          <div><dt>Logo asset ID</dt><dd><code>{result.brand_lock.logo_asset_id}</code></dd></div>
          <div><dt>Product name</dt><dd>{result.brand_lock.product_name}</dd></div>
          <div><dt>Verified product facts</dt><dd><ul>{result.brand_lock.verified_product_facts.map((v) => <li key={v}>{v}</li>)}</ul></dd></div>
          <div><dt>Product UI asset IDs</dt><dd><ul>{result.brand_lock.product_ui_asset_ids.map((v) => <li key={v}><code>{v}</code></li>)}</ul></dd></div>
          <div><dt>Benefit order</dt><dd><ol>{result.brand_lock.benefit_order.map((v) => <li key={v}>{v}</li>)}</ol></dd></div>
          <div><dt>CTA action meaning</dt><dd>{result.brand_lock.cta_action_meaning}</dd></div>
          <div><dt>Layout template asset ID</dt><dd><code>{result.brand_lock.layout_template_asset_id}</code></dd></div>
          <div><dt>Localizable fields</dt><dd><ul>{result.brand_lock.localizable_fields.map((v) => <li key={v}><code>{v}</code></li>)}</ul></dd></div>
        </dl>
      </section>

      <FixtureBrandLockForm fixture={fixture} />

      <DraftEvidence draft={result.draft} disclosure={result.watermark} />

      <section className={styles.details} aria-labelledby="traceability-heading">
        <h2 id="traceability-heading">Traceability</h2>
        <h3>Rules</h3><ul>{result.rule_ids.map((id) => <li key={id}><code>{id}</code></li>)}</ul>
        <h3>Pending hypotheses</h3>
        {result.hypotheses.map((hypothesis) => (
          <article key={hypothesis.hypothesis_id}>
            <strong>Pending review</strong><p>{hypothesis.claim}</p>
            <p><code>{hypothesis.hypothesis_id}</code></p>
            <ul>{hypothesis.evidence_refs.map((ref) => <li key={ref}><code>{ref}</code></li>)}</ul>
          </article>
        ))}
        <h3>Warnings</h3><ul>{result.warnings.map((warning) => <li key={warning}>{warning === "HUMAN_REVIEW_REQUIRED" ? "Human review required" : warning}</li>)}</ul>
        <p>{result.limitation}</p>
      </section>
    </main>
  );
}
