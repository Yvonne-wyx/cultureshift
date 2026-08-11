# Day 4 Person B Bilateral Fixture Foundation Design

**Status:** Approved specification
**Date:** 2026-08-11  
**Owner:** Person B (Product / Frontend / Research)  
**Tracking:** GitHub Issue #3, task T03A  
**Depends on:** Day 3 bilateral rule cards and the reviewed Day 4 Person A contracts at `12acb82`

## Goal

Build the Person B portion of Day 4: a deterministic, rights-cleared fixture foundation for both supported localization directions, plus the first read-only renderer component. The work must leave Day 5 with a stable base for deterministic composition, a fixture watermark, the result page, and the three-minute walkthrough.

The Day 4 deliverable is not an end-to-end product flow. It loads and presents approved synthetic artifacts without calling a model, provider, backend job, analytics service, or external asset host.

## Scope

Day 4 includes one minimal fixture for each supported direction:

- China to UK (`china_to_uk`, `zh-CN` source, `en-GB` proposal).
- UK to China (`uk_to_china`, `en-GB` source, `zh-CN` proposal).

Both fixtures use the same fictional product, **Orbit AI**, so reviewers can compare directional localization choices without introducing a second product or a second Brand Lock. Every visual asset is project-created SVG content containing no real brand, customer, person, private material, or third-party creative.

Day 4 produces:

- machine-readable fixture JSON for both directions;
- project-created SVG logo, product-UI reference, and source-ad assets;
- expanded rights/provenance records for every fixture asset;
- a pure `FixtureLoader` that validates the public safety boundary and returns immutable fixture data;
- a read-only `FixturePreview` renderer start;
- an updated foundation page that presents both fixtures and preserves the permanent disclosure `Fixture Demo / 非实时模型`;
- unit and component tests for the loader, bilateral data, safety labels, Brand Lock, and human-review state.

## Explicit exclusions

The following remain Day 5 work:

- pixel-precise or canvas-based deterministic composition;
- a visual watermark burned into exported artwork;
- a full result route or result-version comparison page;
- a guided three-minute walkthrough;
- export, download, feedback, retry, revision, or backend retrieval;
- live AI, OCR, upload, storage, analytics, or provider calls.

The Day 4 preview may visually label the fixture, but it must not claim to be the final Day 5 watermark or compositor.

## Fixture assets and rights

Canonical public assets live under `apps/web/public/fixtures/orbit-ai/`:

- `orbit-ai-logo.svg`: language-neutral fictional logo.
- `orbit-ai-product-ui.svg`: fictional, non-functional UI reference.
- `source-zh-cn.svg`: synthetic Chinese source static ad.
- `source-en-gb.svg`: synthetic English source static ad.

The assets use only SVG shapes and system-font text. They contain no external image, font, tracking pixel, network reference, embedded script, or executable content.

`demo/assets/manifest.json` remains the rights source of record. It is upgraded from the metadata-only placeholder to individual asset records whose paths, project-created provenance, permitted repository/public-demo use, derivative permission, public-display permission, and attribution requirements are explicit. `demo/assets/RIGHTS.md` continues to state that synthetic status does not establish cultural validity or real-world performance.

Unknown, incomplete, private, third-party, or ambiguous rights fail closed and are never loaded by the fixture layer.

## Fixture data contract

JSON files live under `apps/web/src/fixtures/data/`:

- `china-to-uk.json`
- `uk-to-china.json`

Each document contains:

- a stable fixture ID and direction;
- the permanent disclosure string;
- a `RunCreate`-compatible fixture request with `execution_mode: "fixture"`;
- public asset paths and their approved `fixture:`, `rights:`, or `evidence:` references;
- source and target locales;
- source headline/body and localized proposal headline/body/CTA;
- the unchanged Brand Lock values;
- source-backed rule IDs from the corresponding Day 3 rule card;
- one or more `CulturalHypothesis` records with `review_status: "pending"`;
- warning codes that require accountable human review;
- a plain-language limitation that the proposal is not cultural, legal, or performance validation.

The Chinese-to-UK fixture may use `ZEU-S1` and `ZEU-S3` as source-backed drafting constraints and `ZEU-H1` as a pending hypothesis. The UK-to-China fixture may use `EZC-S1` and `EZC-S3` plus pending `EZC-H1`. Rule IDs remain traceable to the committed rule cards; fixture JSON does not copy or strengthen the source claims.

The two fixtures share identical protected Orbit AI Brand Lock values: logo, product name, verified product fact, product UI reference, benefit order, CTA action meaning, and layout-template identifier. Only the approved narrative, use scenario, trust information, and language fields differ.

## Loader architecture

`apps/web/src/fixtures/types.ts` defines the fixture-only composition around generated public contract types. It does not redefine `RunCreate`, `BrandLock`, `AssetRef`, or `CulturalHypothesis`.

`apps/web/src/fixtures/fixture-loader.ts` owns loading and validation. Its public interface is deliberately small:

```ts
export type FixtureId = "china-to-uk" | "uk-to-china";

export function listFixtureIds(): readonly FixtureId[];
export function loadFixture(id: FixtureId): Readonly<FixtureBundle>;
```

The implementation statically imports the two JSON artifacts so the Day 4 page has no runtime fetch or network dependency. The loader validates the safety-critical fields that TypeScript alone cannot prove at runtime:

- the requested ID matches the document ID;
- direction and locale pair are one of the two approved mappings;
- execution mode is exactly `fixture`;
- source asset kind is `source_ad`;
- the permanent disclosure is exact;
- rights/provenance/evidence references use approved public-reference schemes;
- every asset path is repository-public and contains no absolute path, backslash, URL scheme, or traversal segment;
- Brand Lock is present and identical across request and preview;
- cultural hypotheses remain `pending` and contain evidence and validation requirements.

Validation throws a stable `Invalid fixture: <code>` error. It does not include raw fixture values, local paths, absolute paths, or internal exception text.

Returned fixture objects are deeply frozen. The renderer therefore cannot mutate the approved fixture or Brand Lock accidentally.

## Renderer start

`apps/web/src/components/fixture-preview.tsx` is a presentational server-compatible component. It receives an already validated `FixtureBundle`; it does not load files, fetch data, mutate state, or interpret cultural rules.

For each fixture it renders:

- direction and source-to-target locale labels;
- the source-ad SVG using a repository-public path;
- proposed localized headline, body, and CTA;
- protected Brand Lock facts as a compact checklist;
- rule IDs and pending hypothesis labels;
- a visible human-review warning;
- the permanent `Fixture Demo / 非实时模型` disclosure.

The component is a preview of deterministic data, not the Day 5 compositor. It does not place editable layers, rasterize output, produce a downloadable artifact, or claim that the displayed proposal is approved.

The home page changes from the contract-only placeholder to a bilateral fixture lab. It retains a concise contract-foundation explanation and renders both fixtures without client-side state. A two-card layout is sufficient for Day 4 and keeps both directions visible to reviewers.

## Data flow

1. Build imports the two committed JSON artifacts.
2. The home page asks `FixtureLoader` for the stable fixture IDs.
3. `FixtureLoader` validates and deeply freezes each fixture.
4. The page passes each validated fixture to `FixturePreview`.
5. The component renders only validated values and repository-public SVG paths.

There is no browser fetch, API request, model call, cookie, token, database access, or telemetry in this flow.

## Failure behavior

The system fails closed during import/render when fixture data violates an approved invariant. Unknown fixture IDs are not accepted. The loader reports only stable error codes such as `unknown_id`, `live_execution`, `unsafe_asset_path`, `rights_missing`, `brand_lock_mismatch`, or `hypothesis_not_pending`.

A fixture failure must not fall back to arbitrary data, live execution, or an unlabelled preview. The page may surface a generic non-sensitive fixture-unavailable message in later work; Day 4 tests exercise the loader directly.

## Testing

Loader tests cover:

- exactly two stable fixture IDs;
- successful loading of both directions;
- exact direction/locale mappings;
- immutable returned data;
- identical bilateral Brand Lock values;
- approved rights/provenance and repository-public asset paths;
- source-backed rule IDs and pending hypotheses;
- rejection of live execution, unsafe paths, missing rights, Brand Lock drift, and approved-state cultural claims;
- stable non-sensitive error messages.

Component/page tests cover:

- both directional previews are present;
- the permanent disclosure appears for every preview;
- source and target locales are visible;
- Brand Lock and human-review labels are visible;
- fixture source assets use local public paths;
- no wording claims cultural correctness, legal compliance, or performance uplift.

The existing JSON Schema/TypeScript freshness, typecheck, Next build, public-boundary scan, and npm audit gates remain required.

## Exit criteria

Person B Day 4 is complete when:

- both authorized fixture bundles load deterministically;
- all committed visual assets have explicit rights/provenance records;
- the preview renders both directions with Brand Lock and pending-review context;
- `Fixture Demo / 非实时模型` is permanent and visible;
- tests, typecheck, production build, generated-contract checks, and public-boundary verification pass;
- no Day 5 composition/result-page work or live-provider behavior is included.
