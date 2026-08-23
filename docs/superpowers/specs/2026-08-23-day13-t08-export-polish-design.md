# Day 13 T08 Export and Composition Polish Design

**Date:** 2026-08-23
**Task:** T08 Day 13
**Issue:** [#12](https://github.com/Yvonne-wyx/cultureshift/issues/12)
**Owners:** Person A + Person B
**Status:** Approved product design; implementation pending

## Goal

Complete the smallest safe T08 integration slice by turning the immutable Day 12 fixture
composition into integrity-checked PNG and canonical JSON downloads. Harden the fixed compositor
with deterministic English and Simplified Chinese wrapping and golden verification for protected
Logo and product-UI pixels. Prove both supported directions through the public fixture workflow.

The implementation remains fixture-only and keeps runs `in_progress`. Critique, revision,
approval, workflow completion, live providers, and claims of automated cultural validation remain
Day 14 or later work.

## Approved product boundary

Day 13 includes:

- authenticated read-only PNG and JSON export routes for an existing immutable composition;
- TTL, artifact-ID, media-type, byte-size, and SHA-256 verification before PNG delivery;
- canonical bounded JSON containing only the existing public `CompositionGenerated` evidence;
- safe attachment filenames derived from the server-validated run ID;
- deterministic word-aware English and character-aware Simplified Chinese line wrapping;
- fixed text boxes, bounded font reduction, explicit line limits, and fail-closed overflow;
- golden protected-layer tests over decoded RGBA pixels, bounds, aspect ratio, alpha bounds,
  source IDs, and z-order;
- bilateral API integration tests from authorized upload through composition export;
- fixture preview regeneration only if the approved deterministic compositor output changes;
- an update to ADR-0008 recording the fixture-only export and verification boundary.

Day 13 excludes:

- ZIP archives, export history, cloud storage, signed URLs, share links, or a download centre;
- new Web application flows or live runtime calls from the static fixture result pages;
- live or paid image providers, credentials, SDKs, provider comparison, or fallback behavior;
- caller-supplied filenames, paths, output formats, layout coordinates, copy, or prompts;
- SVG, JPEG, PDF, responsive layouts, arbitrary templates, or image editing;
- critique, revision, approval, run completion, or production-readiness claims.

## Export architecture

The two public routes are:

- `GET /api/v1/runs/{run_id}/composition.png`
- `GET /api/v1/runs/{run_id}/composition.json`

Both routes require a bearer capability whose subject exactly matches `run_id` and whose scope
contains `read_project_run`. They never accept a request body or query-controlled path.

The PNG route:

1. loads the persisted immutable `CompositionGenerated` summary for the run;
2. loads the artifact by its server-stored opaque ID from `CompositionArtifactStore`;
3. rejects expired, missing, malformed, oversized, non-PNG, or hash-mismatched content;
4. cross-checks stored artifact ID, SHA-256, dimensions, and media type against the summary;
5. returns the verified bytes as `image/png` with `Content-Disposition: attachment` and
   `X-Content-Type-Options: nosniff`.

The JSON route serializes the persisted `CompositionGenerated` contract with sorted keys,
compact separators, UTF-8, and a trailing newline. It returns `application/json` as an
attachment. It does not read or embed the PNG and cannot expose local paths, temporary metadata,
capability tokens, prompts, or provider internals.

No export mutates the run, extends TTL, regenerates an artifact, or changes composition state.
Stable public failures are `invalid_capability`, `capability_subject_mismatch`, `run_not_found`,
`composition_unavailable`, and `composition_artifact_unavailable`.

## Deterministic bilingual wrapping

Text layout remains inside the fixed Day 12 semantic regions. Wrapping is a pure function of the
font bytes, text, box width, maximum lines, and font size:

- normalize supported whitespace without changing visible words or CJK characters;
- split English at whitespace, preserving punctuation with its adjacent word;
- allow breaks between CJK characters while keeping contiguous Latin/number sequences together;
- greedily choose the longest prefix whose measured advance fits the available width;
- never hyphenate, truncate, add ellipses, or rewrite approved copy;
- reduce font size in fixed two-pixel steps until all lines fit the width, height, and line limit;
- fail with `composition_output_invalid` when the minimum approved size cannot contain the copy.

Headline, body, CTA, and fixture disclosure use explicit maximum line counts. Rendering positions
are derived only from fixed box geometry and measured line bounds. The same request must produce
byte-identical PNG and layer hashes across repeated execution in the pinned environment.

## Locked-layer verification

Logo and product UI remain registered project fixtures. Tests independently reconstruct the
approved resize with Pillow and compare the compositor layer against it using decoded RGBA bytes.
For each protected layer they verify:

- the `source_asset_id` equals the confirmed Brand Lock value;
- aspect ratio and alpha bounds match the registered source after approved containment resizing;
- width, height, placement bounds, semantic order, and decoded-RGBA SHA-256 are exact;
- no text, background, disclosure, or later layer alters the protected layer artifact;
- a changed asset ID, content hash, kind, or missing protected input fails closed.

This is technical pixel preservation evidence only. It does not claim legal, cultural, brand, or
performance approval.

## Bilateral integration path

One parametrized integration test covers `china_to_uk` and `uk_to_china` using only authorized
fixture assets and offline providers:

1. upload registered Logo, product UI, and layout assets through the secure asset boundary;
2. create a fixture run and analyze it;
3. confirm the exact Brand Lock;
4. generate the deterministic brief and factual copy;
5. generate the fixture background and composed advertisement;
6. download JSON evidence and PNG bytes using the read capability;
7. prove contract equality, hashes, dimensions, disclosure, protected IDs, and repeatable export.

The test uses public HTTP routes for workflow behavior and may inspect the test repository only
to establish independent assertions. It performs no network or live-provider operation.

## ADR and public evidence

ADR-0008 remains the authoritative provider decision. Day 13 updates it to record that exports
serve only already-generated fixture artifacts, that verification precedes delivery, and that
export support does not approve a live provider. A separate vendor ADR is intentionally not
created because no vendor decision exists.

If wrapping changes committed fixture previews, the build script regenerates both PNGs and all
recorded hashes deterministically. The asset manifest, fixture JSON, rights record, and Web
evidence must stay mutually consistent. The permanent `Fixture Demo / 非实时模型` disclosure and
human-review limitation remain visible.

## Testing and verification

Implementation follows observable RED then GREEN:

- export-service and API tests for authentication, exact subject/scope, canonical JSON,
  headers, TTL, missing data, tampering, hash mismatch, and sanitized failures;
- pure wrapping tests for English, Simplified Chinese, mixed content, punctuation, newlines,
  deterministic sizing, exact-fit boundaries, and fail-closed overflow;
- golden protected-layer tests for both directions and negative Brand Lock drift cases;
- bilateral public-flow integration tests with repeatable PNG and JSON exports;
- generated JSON Schema and TypeScript contract freshness checks;
- complete Python and Web tests, Ruff, TypeScript typecheck, production build, dependency audit,
  demo-manifest verification, and public-boundary scanning.

## Acceptance criteria

1. Both supported directions can export an existing deterministic composition as verified PNG
   and canonical bounded JSON through authenticated public routes.
2. Export routes use read capability scope, exact run subjects, safe server-derived filenames,
   correct media types, attachment headers, and no secret or local-path disclosure.
3. Missing, expired, corrupted, oversized, or hash-mismatched artifacts fail with bounded stable
   errors and are never returned.
4. English, Simplified Chinese, and mixed copy wrap deterministically within fixed boxes without
   rewriting, truncation, hidden overflow, or machine-font fallback.
5. Golden tests prove Logo and product-UI decoded pixels, aspect ratios, alpha bounds, source IDs,
   bounds, and semantic order remain exact after approved resizing.
6. A bilateral public integration test proves the upload-to-analysis-to-lock-to-draft-to-
   composition-to-export workflow without live providers.
7. ADR-0008 and all affected fixture evidence accurately state the fixture-only, human-review
   boundary.
8. All focused and repository-wide gates pass, the approved changes are pushed without
   overwriting remote work, and `Day13.docx` is recorded locally in the established format.
