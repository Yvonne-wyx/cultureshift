import chinaToUk from "./data/china-to-uk.json";
import ukToChina from "./data/uk-to-china.json";
import { validateFixture } from "./fixture-validation";
import type { FixtureBundle, FixtureId } from "./types";

const FIXTURES: Readonly<Record<FixtureId, unknown>> = Object.freeze({
  "china-to-uk": chinaToUk,
  "uk-to-china": ukToChina,
});

const FIXTURE_IDS = Object.freeze(["china-to-uk", "uk-to-china"] as const);

export function listFixtureIds(): readonly FixtureId[] {
  return FIXTURE_IDS;
}

export function loadFixture(id: FixtureId): Readonly<FixtureBundle> {
  if (!Object.prototype.hasOwnProperty.call(FIXTURES, id)) {
    throw new Error("Invalid fixture: unknown_id");
  }
  return validateFixture(FIXTURES[id], id);
}
