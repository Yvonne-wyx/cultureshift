# Day 11 Brief and Copy Generation Design

**Date:** 2026-08-20
**Task:** T07
**Owners:** Person A + Person B
**Status:** Approved product design; implementation pending

## Goal

Complete the smallest safe Day 11 vertical slice that turns a Day 10 run with
an immutable confirmed Brand Lock into a factual `CreativeBrief` and bilingual
`AdCopy`. The slice is deterministic and fixture-only, but preserves a narrow
provider boundary so a reviewed live copy provider can be introduced later.

The run remains `in_progress`: image composition, critique, revisions, and final
completion belong to later days.

## Approved product boundary

Day 11 includes:

- a deterministic creative-brief planner for both supported directions;
- a replaceable copywriter protocol and fixture implementation;
- exact directional rule mapping from the committed rule cards;
- a fact validator that fails closed on unsupported product claims;
- authenticated, idempotent draft generation for confirmed runs;
- atomic persistence of the brief, copy, rule IDs, and generation timestamp;
- generated JSON Schema and TypeScript contract updates;
- bilingual fixture inputs and tests for both directions;
- a static fixture UI that shows the generated brief, copy, traceable rule IDs,
  pending hypotheses, and explicit human-review limitations.

Day 11 excludes:

- live or paid model calls, provider credentials, and provider SDKs;
- image generation or composition;
- critique, scoring, revision loops, exports, or run completion;
- free-form user prompts or storage/logging of private prompt text;
- cultural assertions presented as verified facts;
- editing or replacing the confirmed Brand Lock.

## Architecture and data flow

The endpoint accepts no creative payload. It derives all inputs from the trusted
stored run:

1. Authenticate the update capability and require the token subject to match the
   requested run.
2. Load the run and require `in_progress`, a completed Day 9 analysis, and the
   exact Day 10 confirmed Brand Lock.
3. Pass the trusted stored run direction explicitly, then select its fixture prompt
   definition and exact rule IDs; never infer direction from provider-detected locale.
4. Build a `CreativeBrief` by copying the trusted Brand Lock and pending cultural
   hypotheses, then add only approved fixture narrative fields.
5. Ask the fixture copywriter for `AdCopy` through a provider-neutral protocol.
6. Validate locale, CTA action meaning, Brand Lock preservation, directional
   rule IDs, and every product claim against the confirmed verified facts.
7. Atomically persist the validated draft and return it. Repeating the request
   returns the same stored draft without regenerating it.

No image bytes, capability token, prompt transcript, local path, exception text,
or provider response is persisted in the draft record or returned in errors.

## Contracts

Add one public response contract, `DraftGenerated`, containing:

- `run_id`;
- `status`, fixed to `in_progress`;
- `brief: CreativeBrief`;
- `copy: AdCopy`;
- `rule_ids`, a unique bounded tuple of safe identifiers;
- `generated_at`, a timezone-aware timestamp.

`CreativeBrief` and `AdCopy` remain the existing public contracts. The public
response validates its own direction, locale, CTA, and rule mapping; the generator
validates it against trusted stored analysis and confirmation before constructing
the response. Together they require that:

- brief direction and target locale match;
- brief Brand Lock equals the confirmed analysis Brand Lock;
- copy locale equals the brief locale;
- copy CTA action meaning equals the locked CTA action meaning;
- rule IDs exactly equal the allowed set for the direction.

The bundled JSON Schema and generated TypeScript declarations remain committed
artifacts and must pass their existing freshness checks.

## Directional fixture and rule mapping

The implementation uses only the source-backed drafting constraints already
recorded in the repository:

| Direction | Locale | Drafting rule IDs | Pending hypothesis |
| --- | --- | --- | --- |
| China to UK | `en-GB` | `ZEU-S1`, `ZEU-S3` | `ZEU-H1` |
| UK to China | `zh-CN` | `EZC-S1`, `EZC-S3` | `EZC-H1` |

The hypothesis remains `pending` and is displayed as a human-review item. It is
not included in the verified rule list and cannot authorize a factual claim.

Fixture prompt definitions are structured internal data: direction, locale,
rule IDs, narrative guidance, use scenario, trust information, and expected copy
fields. They contain no secrets, user content, provider instructions, or chain of
thought. The visible trust label remains `Fixture Demo / 非实时模型`.

## Factual copy constraint

The fixture copywriter may use:

- the exact protected product name;
- exact verified product facts;
- approved non-product framing from the fixture definition;
- the locked CTA action meaning and a localized CTA label.

It may not introduce performance, accuracy, automation, market, compliance, or
cultural claims that are absent from `verified_product_facts`. Validation is
semantic by construction rather than an open-ended language classifier: each
fixture returns an explicit tuple of product-fact references, and the validator
requires that tuple to equal facts in the confirmed Brand Lock. Tests also feed
a forged output carrying an unsupported fact and require failure before storage.

## API and persistence

Add authenticated endpoint:

`POST /api/v1/runs/{run_id}/draft`

Successful first creation and identical replay return `200 DraftGenerated`.
There is no request body, avoiding client-controlled prompt or claim material.

Stable public failures use bounded codes and generic messages:

- `run_not_found`;
- `invalid_capability`;
- `invalid_run_state`;
- `brand_lock_unconfirmed`;
- `draft_output_invalid`;
- `draft_persistence_failed`.

The repository adds nullable draft columns using its existing forward-only SQLite
migration pattern. One transaction stores the canonical JSON for brief, copy,
rule IDs, and generated timestamp. An existing complete draft is immutable and is
returned for idempotent replay.

## Person B result experience

Both fixture result routes show a compact Day 11 section with:

- localized direction heading;
- creative narrative and use scenario;
- headline, body, and CTA label;
- the locked CTA action meaning;
- exact drafting-rule links or identifiers;
- the pending hypothesis and human-review requirement;
- the fixture-only trust label.

The UI consumes typed fixture data and performs no network call. It must not imply
that the displayed draft was produced by a live model or that cultural/legal/
performance validation has occurred.

## Testing strategy

Implementation follows test-driven development with observable RED then GREEN:

- contract tests for response validation and cross-artifact invariants;
- planner/copywriter tests for deterministic bilingual output;
- validator regressions for unsupported fact, wrong rule IDs, locale drift,
  Brand Lock drift, CTA drift, and pending-hypothesis promotion;
- repository migration, atomic storage, immutability, and replay tests;
- API authentication, state, success, replay, and sanitized failure tests;
- UI tests for both directions, semantic headings, rule traceability, trust label,
  and pending-review language;
- schema and generated-TypeScript freshness;
- the repository's complete Python, Web, lint, build, audit, and public-boundary
  gates before publication.

## Acceptance criteria

1. Both supported directions produce deterministic valid `CreativeBrief` and
   `AdCopy` artifacts from a confirmed Day 10 run.
2. Brand Lock, locale, CTA meaning, and exact directional rule IDs cannot drift.
3. Unsupported product facts and hypothesis-as-fact output fail before storage.
4. The authenticated endpoint is bodyless, idempotent, and returns only bounded
   public errors.
5. Draft data is atomically persisted without secrets, prompts, image bytes, or
   local paths, while the run remains `in_progress`.
6. Both fixture result routes visibly expose the brief, copy, rule traceability,
   fixture-only label, and human-review boundary.
7. All focused and repository-wide quality gates pass, and Day 11 is recorded in
   the local `Day11.docx` using the established daily format.
