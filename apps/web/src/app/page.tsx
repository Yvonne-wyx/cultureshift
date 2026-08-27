import Link from "next/link";

import { FixturePreview } from "../components/fixture-preview";
import { listFixtureIds, loadFixture } from "../fixtures/fixture-loader";

const fixtures = listFixtureIds().map(loadFixture);

export default function Home() {
  return (
    <main className="fixture-lab">
      <header className="fixture-lab__header">
        <p className="fixture-lab__eyebrow">Static bilateral fixture lab</p>
        <h1>CultureShift bilateral fixture lab</h1>
        <p className="fixture-lab__introduction">
          Two AI software advertising-localization fixtures for China and UK
          directions. Each proposal remains subject to human review.
        </p>
        <Link className="fixture-lab__studio-link" href="/studio">
          Open connected Studio
        </Link>
      </header>

      <section className="fixture-lab__previews" aria-label="Bilateral fixture previews">
        {fixtures.map((fixture) => (
          <FixturePreview key={fixture.fixture_id} fixture={fixture} />
        ))}
      </section>
    </main>
  );
}
