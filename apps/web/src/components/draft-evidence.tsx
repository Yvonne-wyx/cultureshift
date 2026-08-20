import type { FixtureBundle } from "../fixtures/types";

import styles from "./draft-evidence.module.css";

export function DraftEvidence({
  draft,
  disclosure,
}: {
  draft: FixtureBundle["draft"];
  disclosure: FixtureBundle["disclosure"];
}) {
  return (
    <section className={styles.section} aria-labelledby="draft-heading">
      <div className={styles.statusRow}>
        <p className={styles.label}>{disclosure}</p>
        <strong>Human review required</strong>
      </div>
      <h2 id="draft-heading">Creative brief / 创意简报</h2>
      <dl className={styles.brief}>
        <div><dt>Narrative</dt><dd>{draft.brief.narrative}</dd></div>
        <div><dt>Use scenario</dt><dd>{draft.brief.use_scenario}</dd></div>
        <div><dt>Prompt summary</dt><dd>{draft.prompt_summary}</dd></div>
      </dl>

      <h2>Factual copy / 事实文案</h2>
      <article className={styles.copy} aria-label="Generated factual copy">
        <h3>{draft.copy.headline}</h3>
        <p>{draft.copy.body}</p>
        <p><strong>CTA:</strong> {draft.copy.cta_label}</p>
        <p><strong>Locked action meaning:</strong> {draft.copy.cta_action_meaning}</p>
      </article>

      <h3>Source-backed drafting rules</h3>
      <ul>{draft.rule_ids.map((ruleId) => <li key={ruleId}><code>{ruleId}</code></li>)}</ul>
      <h3>Pending hypotheses</h3>
      {draft.brief.hypotheses.map((hypothesis) => (
        <article key={hypothesis.hypothesis_id} className={styles.hypothesis}>
          <strong>Pending human review</strong>
          <p>{hypothesis.claim}</p>
        </article>
      ))}
      <p className={styles.limitation}>
        This proposal is not cultural, legal, or performance validation.
      </p>
    </section>
  );
}
