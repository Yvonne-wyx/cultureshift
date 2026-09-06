import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import baseStyles from "../portfolio.module.css";
import fontStyles from "../font.module.css";
import sectionStyles from "./sections.module.css";

const styles = { ...baseStyles, ...sectionStyles };

export const metadata: Metadata = { title: "CultureShift — Case Study", description: "A human-in-the-loop system for accountable cross-cultural creative adaptation." };

const tensions = [
  { number: "01", title: "Localization", accent: styles.lilac, text: "Narrative, scenario, language, and trust framing may need to shift for a new market." },
  { number: "02", title: "Brand Truth", accent: styles.mint, text: "Product identity, verified facts, real UI, benefit order, and CTA meaning must remain intact." },
  { number: "03", title: "AI Uncertainty", accent: styles.orange, text: "Cultural reasoning is contextual and contestable. A generated suggestion cannot become a cultural fact." },
];

const journey = [
  ["01", "Ingest", "Authorized creative, provenance, rights, and direction enter the workflow."],
  ["02", "Extract", "Text and structural elements are treated as untrusted candidate data."],
  ["03", "Lock", "Immutable brand fields are confirmed before transformation can proceed."],
  ["04", "Reason", "Cultural inferences become evidence-linked hypotheses with uncertainty."],
  ["05", "Generate", "Only permitted fields are adapted into a static proposal."],
  ["06", "Review", "Warnings, evidence, preserved fields, and changes reach a human reviewer."],
];

export default function CaseStudy() {
  return (
    <main className={`${styles.casePage} ${fontStyles.calibri}`}>
      <nav className={`${styles.nav} ${styles.caseNav}`} aria-label="Primary navigation">
        <Link className={styles.wordmark} href="/">CultureShift<span>.</span></Link>
        <div className={styles.navLinks}><Link href="#problem">Problem</Link><Link href="#system">System</Link><Link href="#architecture">Architecture</Link><Link className={styles.navCta} href="/studio">Open the Studio <span aria-hidden="true">↗</span></Link></div>
      </nav>
      <section className={styles.caseHero}>
        <div className={styles.caseHeroCopy}>
          <p className={styles.sectionLabel}>01 · Project overview</p><h1>CultureShift</h1>
          <p className={styles.caseHeadline}>Creative adaptation,<br/><em>without losing control.</em></p>
          <p className={styles.caseIntro}>A human-in-the-loop reasoning system for adapting AI-product advertising between China and the UK while preserving verified brand truth.</p>
          <div className={styles.tagRow}><span>AI Product Design</span><span>Full-stack System</span><span>Cross-cultural Localization</span></div>
        </div>
        <div className={styles.caseHeroImage}><div className={styles.marketBadge}>China <span>→</span> UK</div><Image src="/fixtures/orbit-ai/composed-china-to-uk.png" alt="Orbit AI China to UK proposal shown in CultureShift" width={1600} height={900} priority /><p>Fixture-based proposal · Human review required</p></div>
        <dl className={styles.projectFacts}><div><dt>Product</dt><dd>Technical prototype</dd></div><div><dt>Scope</dt><dd>China ↔ UK</dd></div><div><dt>Creative format</dt><dd>Static advertising</dd></div><div><dt>Domain</dt><dd>AI software / apps</dd></div></dl>
      </section>
      <section className={styles.problemSection} id="problem">
        <header className={styles.sectionHeader}><p className={styles.sectionLabel}>02 · Problem space</p><h2>Cross-cultural adaptation requires change.<br/><em>Not everything should change.</em></h2><p>Generative AI increases creative range, but also collapses three fundamentally different concerns into a single prompt.</p></header>
        <div className={styles.tensionGrid}>{tensions.map((item) => <article className={`${styles.tensionCard} ${item.accent}`} key={item.title}><div><span>{item.number}</span><span className={styles.cardMark}>●</span></div><h3>{item.title}</h3><p>{item.text}</p></article>)}</div>
        <div className={styles.problemStatement}><span>The design challenge</span><p>How can a system enable meaningful creative adaptation while separating what may change, what must remain true, and what still requires human judgement?</p></div>
      </section>
      <section className={styles.insightSection} id="insight">
        <header className={styles.sectionHeader}><p className={styles.sectionLabel}>03 · Product insight</p><h2>Localization is not just a generation problem.<br/><em>It is a constraint, uncertainty, and review problem.</em></h2></header>
        <div className={styles.workflowCompare}>
          <article className={styles.workflowLegacy}><div className={styles.workflowTitle}><span>Typical approach</span><h3>Traditional prompt-to-output</h3></div><div className={styles.legacyFlow}><span>Prompt</span><i>→</i><span>AI generation</span><i>→</i><span>Output</span></div><p className={styles.workflowNote}>Constraints, evidence, and approval are implicit—making drift difficult to detect.</p></article>
          <article className={styles.workflowCulture}><div className={styles.workflowTitle}><span>CultureShift approach</span><h3>CultureShift constrained workflow</h3></div><div className={styles.constraintFlow}>
            <div><b>01</b><span><strong>Brand Lock</strong><small>Define immutable truth</small></span></div><i>→</i><div><b>02</b><span><strong>CulturalHypothesis</strong><small>Make uncertainty visible</small></span></div><i>→</i><div><b>03</b><span><strong>Constrained proposal</strong><small>Adapt permitted fields</small></span></div><i>→</i><div><b>04</b><span><strong>Human review</strong><small>Approve explicitly</small></span></div>
          </div><div className={styles.outcomeBar}><span>Verified truth preserved</span><span>Reasoning traceable</span><span>Accountability retained</span></div></article>
        </div>
      </section>
      <section className={styles.productSystem} id="system">
        <header className={styles.sectionHeader}><p className={styles.sectionLabel}>04 · Product system</p><h2>Three mechanisms turn principles<br/><em>into enforceable product behaviour.</em></h2><p>The system separates immutable truth, uncertain reasoning, and accountable decision-making instead of asking one model response to carry all three.</p></header>
        <div className={styles.systemGrid}>
          <article><span className={styles.systemNumber}>01</span><div className={styles.systemGlyph}>⌾</div><h3>Brand Lock</h3><p>A fail-closed constraint layer protects logo, product name, verified facts, real UI, benefit order, CTA meaning, and layout template.</p><ul><li>Immutable fields stay traceable</li><li>Conflicts block dependent changes</li><li>Localizable fields remain explicit</li></ul></article>
          <article><span className={styles.systemNumber}>02</span><div className={styles.systemGlyph}>△</div><h3>CulturalHypothesis</h3><p>Every cultural inference is represented as a reviewable hypothesis—not presented as an established market fact.</p><ul><li>Rationale linked to evidence</li><li>Uncertainty remains visible</li><li>Validation requirements travel forward</li></ul></article>
          <article><span className={styles.systemNumber}>03</span><div className={styles.systemGlyph}>◎</div><h3>Human-in-the-Loop</h3><p>Generated work remains a proposal until a person evaluates evidence, warnings, rights, and the target-context reasoning.</p><ul><li>No implicit approval state</li><li>Review decisions are recorded</li><li>Export follows explicit approval</li></ul></article>
        </div>
        <div className={styles.systemBoundary}><strong>System guarantee</strong><span>CultureShift structures the decision process. It does not claim automated cultural validation or guaranteed campaign performance.</span></div>
      </section>
      <section className={styles.journeySection} id="workflow">
        <header className={styles.sectionHeader}><p className={styles.sectionLabel}>05 · End-to-end workflow</p><h2>From authorized input to accountable decision.</h2><p>Each stage narrows what the system may do while carrying provenance, uncertainty, and review state forward.</p></header>
        <ol className={styles.journeyFlow}>{journey.map(([number,title,text]) => <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{text}</p></div></li>)}</ol>
        <div className={styles.reviewLoop}><span>Quality loop</span><strong>Critique</strong><i>→</i><strong>Structured feedback</strong><i>→</i><strong>Revision</strong><i>→</i><strong>Re-review</strong><small>Revision preserves the same locked layers and never silently changes the contract.</small></div>
      </section>
      <section className={styles.architectureSection} id="architecture">
        <header className={styles.sectionHeader}><p className={styles.sectionLabel}>06 · Technical system</p><h2>System Architecture</h2><p>Typed contracts connect a responsive product surface to a provider-agnostic service layer, durable workflow state, and controlled temporary assets.</p></header>
        <div className={styles.architectureMap}>
          <div className={styles.architectureLane}><span>Experience</span><article><b>Next.js Studio</b><small>React · TypeScript</small><p>Fixture demo, Brand Lock confirmation, proposal evidence, review, and revision controls.</p></article></div>
          <div className={styles.archConnector}><span>Generated JSON contracts</span></div>
          <div className={styles.architectureLane}><span>Application</span><article><b>FastAPI application layer</b><small>Python · Typed endpoints</small><p>Ingestion, analysis orchestration, draft generation, composition, critique, and revision services.</p></article></div>
          <div className={styles.archConnector}><span>Explicit workflow states</span></div>
          <div className={`${styles.architectureLane} ${styles.architectureSplit}`}><span>State & assets</span><article><b>SQLite persistence</b><small>Runs · status · decisions</small><p>Durable workflow state with immutable artifacts and guarded state transitions.</p></article><article><b>Temporary asset store</b><small>24-hour intended expiry</small><p>Purpose-limited creative and composition assets with testable deletion.</p></article></div>
        </div>
        <div className={styles.crossCutting}><span>Cross-cutting controls</span><ul><li>Capability tokens</li><li>Rate limits</li><li>Provenance</li><li>Rights checks</li><li>Public boundary</li><li>Structured failures</li></ul></div>
      </section>
    </main>
  );
}
