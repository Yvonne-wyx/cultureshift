import Image from "next/image";

import type { FixtureComposition } from "../fixtures/types";

import styles from "./composition-evidence.module.css";

export function CompositionEvidence({
  composition,
}: {
  composition: Readonly<FixtureComposition>;
}) {
  const protectedLayers = composition.layers.filter(
    (layer) => layer.kind === "logo" || layer.kind === "product_ui",
  );
  return (
    <section className={styles.section} aria-labelledby="composition-heading">
      <div className={styles.statusRow}>
        <p className={styles.disclosure}>{composition.disclosure}</p>
        <strong>Fixture-only · Human review required</strong>
      </div>
      <h2 id="composition-heading">Deterministic composition / 确定性合成</h2>
      <Image
        className={styles.preview}
        src={composition.preview_path}
        alt="1600 x 900 fixture composition"
        width={composition.width}
        height={composition.height}
      />
      <dl className={styles.evidence}>
        <div><dt>Dimensions</dt><dd>{composition.width} × {composition.height} PNG</dd></div>
        <div><dt>Output SHA-256</dt><dd><code>{composition.rendered_sha256}</code></dd></div>
        <div><dt>Background</dt><dd><code>{composition.background_provenance}</code></dd></div>
        <div>
          <dt>Protected layers</dt>
          <dd><ul>{protectedLayers.map((layer) => (
            <li key={layer.kind}>{layer.kind}: <code>{layer.source_asset_id}</code></li>
          ))}</ul></dd>
        </div>
        <div>
          <dt>Font</dt>
          <dd><code>{composition.font.path}</code><br />commit <code>{composition.font.upstream_commit}</code></dd>
        </div>
      </dl>
      <p className={styles.limitation}>{composition.limitation}</p>
    </section>
  );
}
