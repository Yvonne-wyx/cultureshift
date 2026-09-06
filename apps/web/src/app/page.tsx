import Image from "next/image";
import Link from "next/link";

import styles from "./portfolio.module.css";
import fontStyles from "./font.module.css";

function Arrow() {
  return <span aria-hidden="true">↗</span>;
}

export default function Home() {
  return (
    <main className={`${styles.siteShell} ${fontStyles.calibri}`}>
      <nav className={styles.nav} aria-label="Primary navigation">
        <Link className={styles.wordmark} href="/">CultureShift<span>.</span></Link>
        <div className={styles.navLinks}>
          <Link href="#product-boundaries">Product boundaries</Link>
          <Link className={styles.navCta} href="/studio">Enter Studio <Arrow /></Link>
        </div>
      </nav>
      <section className={styles.homeHero}>
        <div className={styles.heroCopy}>
          <p className={styles.kicker}><span /> AI product design · China ↔ UK</p>
          <h1>CultureShift</h1>
          <p className={styles.subheadline}>Human-in-the-Loop Cross-Cultural Creative Reasoning System</p>
          <p className={styles.lede}>A constrained workflow for adapting AI-product advertising between China and the UK—while preserving verified brand truth, exposing uncertainty, and keeping people accountable.</p>
          <div className={styles.heroActions}>
            <Link className={styles.primaryButton} href="/studio">Start adapting <Arrow /></Link>
            <Link className={styles.textButton} href="#product-boundaries">View product boundaries <span aria-hidden="true">↓</span></Link>
          </div>
          <dl className={styles.heroMeta}>
            <div><dt>Format</dt><dd>Static advertising</dd></div>
            <div><dt>System</dt><dd>Next.js + FastAPI</dd></div>
            <div><dt>Decision model</dt><dd>Human-in-the-loop</dd></div>
          </dl>
        </div>
        <div className={styles.heroVisual} aria-label="CultureShift product preview">
          <div className={styles.visualGlow} />
          <div className={styles.productFrame}>
            <div className={styles.frameBar}><span><i /> CultureShift Studio</span><span className={styles.frameStatus}>Proposal · Review required</span></div>
            <Image src="/fixtures/orbit-ai/composed-china-to-uk.png" alt="Orbit AI localized creative proposal" width={1600} height={900} priority />
          </div>
          <div className={`${styles.signalCard} ${styles.signalLock}`}><span className={styles.signalIcon}>✓</span><span><strong>Brand Lock</strong><small>7 immutable fields preserved</small></span></div>
          <div className={`${styles.signalCard} ${styles.signalReview}`}><span className={styles.signalIcon}>◇</span><span><strong>Human review</strong><small>Approval remains explicit</small></span></div>
        </div>
      </section>
      <div className={styles.boundaryStrip} id="product-boundaries"><span>Constrained generation</span><span>Traceable hypotheses</span><span>Fail-closed safeguards</span><span>Accountable review</span></div>
    </main>
  );
}
