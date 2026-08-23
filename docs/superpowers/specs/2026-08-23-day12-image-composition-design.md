# Day 12 Fixture Image Composition Design

**Date:** 2026-08-23
**Task:** T08 Day 12
**Issue:** [#11](https://github.com/Yvonne-wyx/cultureshift/issues/11)
**Owners:** Person A + Person B
**Status:** Approved product design; implementation pending

## Goal

Complete the smallest safe Day 12 slice that turns a confirmed Day 11 fixture run into a
deterministic 1600 x 900 composed static advertisement. Person A provides the constrained
background-provider and authenticated orchestration boundary. Person B provides the Pillow
compositor, verified bilingual font integration, bilateral fixture previews, and visible
layer evidence.

The run remains `in_progress`. Full PNG/JSON download endpoints, final locked-layer golden
verification, wrapping polish, and the complete upload-to-export path belong to Day 13.

## Approved product boundary

Day 12 includes:

- a provider-neutral `ImageProvider` protocol and deterministic `FixtureImageProvider`;
- a structured background request that forbids Logo, brand name, product UI, statistics,
  claims, and long rendered text;
- a single fixed, Brand-locked 1600 x 900 composition template;
- separate background, Logo, product-UI, headline, body, and CTA layers;
- deterministic bilingual text rendering with a repository-bundled Noto CJK font;
- a bodyless authenticated composition endpoint derived only from trusted stored run data;
- idempotent temporary storage of the composed PNG and bounded public metadata;
- bilateral committed fixture previews and a typed result-page evidence component;
- generated JSON Schema and TypeScript contract updates;
- source, licence, SHA-256, rights, and fixture-asset manifest records.

Day 12 excludes:

- live or paid image providers, provider SDKs, credentials, and network calls at runtime;
- accepting free-form prompts, layout coordinates, copy, or asset identifiers from the API
  caller;
- model-generated Logo, product name, UI, statistics, or claim-bearing text;
- arbitrary templates, responsive canvas variants, image editing, or SVG rendering at runtime;
- critique, revision, approval, run completion, and public PNG/JSON export endpoints;
- claims of automated cultural, legal, brand, or performance validation.

## Architecture and data flow

The public endpoint is:

`POST /api/v1/runs/{run_id}/composition`

It has no request body. The flow is:

1. Authenticate the update capability and require its subject to equal `run_id`.
2. Load the stored run request, analysis, confirmed Brand Lock, and immutable Day 11 draft.
3. Require fixture execution, `in_progress`, a confirmed Brand Lock, and a complete draft.
4. Select the exact bilateral fixture definition from the trusted run direction.
5. Build a structured background request from approved narrative fields. Reject any request
   containing a protected product term or instruction to render text, Logo, UI, statistics,
   or claims.
6. Ask `FixtureImageProvider` for its deterministic direction-specific background.
7. Resolve the Brand Lock's Logo and product-UI IDs only through a closed fixture registry.
   Runtime callers cannot supply paths or substitute assets.
8. Pass background bytes, locked raster assets, approved Day 11 copy, fixed layout ID, and the
   verified font path to `PillowCompositor`.
9. Validate dimensions, media type, source IDs, layer hashes, output hash, and fixture mode.
10. Atomically persist bounded composition metadata and write the PNG into TTL-scoped temporary
    storage. A replay returns the existing immutable summary without regenerating it.

No capability token, prompt transcript, local path, private source bytes, exception text, or
provider internals are persisted or returned.

## Public contracts

Add the following frozen Pydantic contracts:

- `BackgroundRequest`: direction, target locale, narrative, use scenario, width fixed to 1600,
  height fixed to 900, and a fixed tuple of prohibited-content categories;
- `GeneratedBackground`: fixture execution mode, PNG media type, dimensions, SHA-256,
  provenance reference, and PNG bytes kept internal rather than serialized publicly;
- `CompositionLayer`: layer kind, source asset ID when Brand-locked, decoded-RGBA SHA-256,
  pixel bounds, and dimensions;
- `CompositionGenerated`: run ID, status fixed to `in_progress`, fixture execution mode,
  1600 x 900 dimensions, rendered-ad SHA-256, ordered public layer evidence, artifact ID,
  fixture disclosure, and UTC generation time.

Binary provider results remain internal dataclasses. Public contracts contain bounded metadata
only. The bundled JSON Schema and generated TypeScript declarations remain committed artifacts
and must pass their freshness checks.

## Fixture image provider

`ImageProvider.generate_background(BackgroundRequest) -> GeneratedBackground` is the only
provider interface. The fixture implementation is deterministic, offline, and selected
explicitly; normal mode never falls back to it.

Its structured request must not contain the protected product name or verified product facts.
The validator also rejects terms or instructions for Logo, brand name, UI, screenshots,
statistics, percentages, claims, captions, typography, or long text. Provider output must be a
decodable 1600 x 900 PNG whose hash and provenance match the selected fixture definition.

No image-provider ADR selecting a live vendor is implied. Day 12 records the decision as
`fixture-only` and preserves the adapter boundary for later authorized research.

## Deterministic Pillow composition

`PillowCompositor.compose(ComposeRequest) -> ComposedAd` supports one exact layout template.
Semantic regions and z-order are fixed:

1. background;
2. product UI;
3. Logo;
4. headline;
5. body;
6. CTA;
7. fixture disclosure.

The compositor converts each input to RGBA, uses high-quality aspect-preserving resizing, and
places every Brand-locked asset on its own transparent layer. It never redraws or synthesizes a
missing Logo or UI layer. The approved copy is rendered separately and cannot change CTA action
meaning or product facts.

Day 12 verifies decoded pixel identity after the approved resize, aspect ratio, alpha bounds,
source asset IDs, fixed dimensions, deterministic output hash, and successful rendering of all
characters used by both fixture directions. Broader line-wrapping and golden-layer polish remain
Day 13 work.

## Font provenance and licence

The only runtime font is:

- upstream: `https://github.com/notofonts/noto-cjk`;
- pinned commit: `f8d157532fbfaeda587e826d4cd5b21a49186f7c`;
- upstream path: `Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf`;
- repository path: `assets/fonts/NotoSansCJKsc-Regular.otf`;
- licence: SIL Open Font License 1.1 from `Sans/LICENSE` at the same commit;
- expected upstream size: approximately 15.7 MB;
- SHA-256: computed after download and recorded consistently in the font README, third-party
  notice, data-source record, and asset manifest before commit.

The official Noto CJK repository identifies the Simplified Chinese OTF and the OFL 1.1 licence.
There is no system-font fallback. A download, licence, font-load, or hash-verification failure
blocks composition rather than silently changing typography.

## Fixture assets and Person B experience

The existing authorized Orbit AI SVGs remain canonical public source assets. Day 12 adds
deterministic PNG derivatives for the Logo and product UI, recording their source paths and
hashes in the public demo-asset manifest. Runtime Pillow composition uses only these registered
raster derivatives; it does not add an SVG rendering dependency.

Both fixture JSON files gain a typed `composition` section with:

- 1600 x 900 dimensions and fixture execution mode;
- committed preview path and rendered-ad SHA-256;
- ordered layer kinds, bounds, hashes, and protected source IDs;
- background provenance and font provenance;
- permanent `Fixture Demo / 非实时模型` disclosure;
- limitation text requiring human review.

The result pages display the actual committed preview plus compact evidence for dimensions,
layer provenance, output hash, protected IDs, font, and fixture-only status. The UI performs no
provider call and does not present the preview as culturally validated or production-approved.

## Persistence and failure handling

SQLite adds nullable composition metadata columns using the existing forward-only migration
pattern. Temporary output bytes live below the configured CultureShift temporary root, use an
opaque artifact ID, inherit a 24-hour TTL, and are never returned as local paths. Metadata and
artifact creation use an all-or-nothing service boundary; incomplete results are removed.

Stable public failures are:

- `run_not_found`;
- `invalid_capability`;
- `invalid_run_state`;
- `brand_lock_unconfirmed`;
- `draft_unavailable`;
- `composition_output_invalid`;
- `composition_persistence_failed`.

Errors never contain asset bytes, paths, submitted text, prompts, credentials, stack traces, or
provider output.

## Testing strategy

Implementation follows observable RED then GREEN:

- contract tests for fixed dimensions, media type, fixture disclosure, layer uniqueness, and
  protected source IDs;
- provider tests for deterministic output and rejection of Logo, brand, UI, statistics, claims,
  or text instructions;
- compositor tests for decoded-RGBA hashes, approved resize, aspect ratio, alpha bounds,
  optional UI refusal, z-order, bilingual glyph coverage, and deterministic PNG output;
- repository and temporary-store tests for migration, atomic creation, immutable replay, TTL,
  missing artifacts, and sanitized failures;
- API tests for authentication, trusted-state derivation, success, replay, invalid state, and
  bounded errors;
- fixture-loader and result-page tests for both directions, preview evidence, protected IDs,
  font provenance, disclosure, and human-review limitations;
- schema and generated-TypeScript freshness;
- the complete Python, Web, lint, typecheck, build, dependency-audit, manifest, and public-boundary
  gates before publication.

## Acceptance criteria

1. Both supported directions produce deterministic fixture backgrounds and composed 1600 x 900
   PNG artifacts from trusted Day 11 data.
2. Background generation cannot receive or render Brand-locked assets, product claims,
   statistics, or long text.
3. Logo and UI layers preserve registered source IDs, approved resized decoded pixels, aspect
   ratio, and alpha bounds; missing locked inputs fail closed.
4. English and Simplified Chinese fixture text loads from the pinned repository font and renders
   without missing-glyph boxes.
5. The authenticated bodyless endpoint is idempotent, keeps the run `in_progress`, and exposes
   bounded metadata rather than binary data or paths.
6. Both fixture result pages show the real deterministic preview, layer evidence, font/source
   provenance, fixture-only disclosure, and human-review boundary.
7. Live providers, final export endpoints, critique, revision, and Day 13 wrapping/golden polish
   remain out of scope.
8. All focused and repository-wide quality gates pass, and Day 12 is recorded locally in
   `Day12.docx` using the established daily format.
