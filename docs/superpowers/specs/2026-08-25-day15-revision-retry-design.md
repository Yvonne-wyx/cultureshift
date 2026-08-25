# Day 15 One-Revision and Safe Retry Design

**Date:** 2026-08-25
**Plan item:** Day 15 / T09
**Issue:** [#14](https://github.com/Yvonne-wyx/cultureshift/issues/14)
**Roles:** Person A (Engineering/AI/Backend) and Person B (Product/Frontend/Research)

## Summary

Day 15 completes the smallest trustworthy feedback, revision, and retry loop on top of the Day 14 workflow and deterministic Critic. A `ready` fixture Run may accept exactly one structured human revision and produce exactly one visible version 2. A technical retry may resume only a server-recorded retryable operation and never creates another visible version by itself.

The implementation remains bilateral, fixture-only, deterministic, and Brand-Lock preserving. It does not accept free-form text as executable instructions, call a model, add a complete Studio page, or introduce Day 16 API wiring.

## Approved product boundary

### Person A

- Add authenticated feedback/revision and retry API integration.
- Require explicit idempotency keys and canonical request fingerprints.
- Persist one revision record and operation replay evidence atomically.
- Enforce `human_revision_count <= 1` under repeat and concurrent requests.
- Increment `technical_attempt_count` only for a new accepted technical retry.
- Preserve version 1 and generate one deterministic version 2 with the same protected Brand Lock layers.
- Resolve conflicts with bounded public errors and without leaking request content.

### Person B

- Restrict revision intent to a closed set of supported fixture changes.
- Define a small TypeScript revision-flow state model and acceptance tests.
- Prove that version 1 and version 2 metadata can be presented distinctly.
- Provide useful conflict/retry states without building the Day 16 Studio or comparison page.

### Explicit non-goals

- No arbitrary natural-language rewriting or prompt execution.
- No second human revision and no visible version 3.
- No approval, completion, publishing, reviewer identity, collaboration, or audit dashboard.
- No live or paid provider, provider credential, background worker, queue, webhook, or polling UI.
- No complete Studio page, result comparison page, or browser-to-backend session integration.
- No automated cultural, legal, brand, compliance, market, or performance validation claim.

## Day 14 baseline correction

The Day 15 baseline exposed a time-dependent Day 14 defect. The Critic repository test supplied `2026-08-25T09:00:00Z`, while a Run created after that time received the earlier review timestamp as `updated_at`. `ProjectRun` correctly rejected the persisted reverse chronology.

The fix is part of the Day 15 prerequisite work:

- `save_critique` rejects a report whose `reviewed_at` precedes the stored Run `created_at`.
- The happy-path repository test derives its review time from `run.created_at + 1 second`.
- A new negative test proves reverse chronology fails before any Critic report or state change is persisted.

This corrects the production invariant rather than merely moving a fixed test timestamp.

## Revision contract

### Supported changes

Define a public `RevisionChange` enum with the initial fixture-only values:

- `shorten_headline`
- `shorten_body`

A request contains one or both values, with no duplicates. CTA meaning is not editable. The first release deliberately excludes free-form layout, visual, claim, Brand Lock, cultural-verdict, and CTA operations.

### Feedback request

Keep the existing `FeedbackRequest` name for compatibility, but strengthen it:

- `run_id` must match the path Run.
- `feedback` is bounded human context.
- `requested_changes` is a unique tuple of one or two `RevisionChange` values.
- `submitted_at` must be UTC and cannot determine server ordering.

The server never treats `feedback` as an instruction. It computes a SHA-256 request fingerprint over canonical public fields, uses only `requested_changes` to select deterministic behavior, and does not persist or return raw feedback. The persisted revision record stores only the feedback digest, structured changes, server timestamps, and public result artifacts.

### Revision response

Add `RevisionCompleted` with:

- `run_id`
- `status`, limited to `ready` or `failed_final`
- `result_version = 2`
- `previous_composition` public summary
- revised `brief`, `copy`, `composition`, and `critique`
- `initial_generation_count = 1`
- `human_revision_count = 1`
- current `technical_attempt_count`
- server `revised_at`

The response contains no raw feedback, idempotency key, local path, prompt, provider detail, or internal exception.

## Deterministic revision generation

Add a focused `FixtureRevisionEngine`. It consumes only trusted persisted version-1 analysis, confirmed Brand Lock, draft fact references, and requested structured changes.

- Each localization direction has a pinned revised-copy fixture.
- `shorten_headline` selects the shorter pinned headline.
- `shorten_body` selects the shorter pinned body.
- Unselected fields remain byte-for-byte equal to version 1.
- Locale, rule IDs, fact references, benefit order, CTA action meaning, and Brand Lock remain unchanged.
- The existing fixed compositor is reused to create a new temporary artifact with identical protected Logo/UI source IDs, semantic layer order, canvas size, font, disclosure, and layout rules.
- The deterministic Critic reviews the revised persisted inputs before the revision becomes visible.

Version 1 remains immutable and available. Version 2 receives a distinct artifact ID and hash. A revision never overwrites version-1 draft, composition, or Critic evidence.

## Persistence and operation state

Add two SQLite tables rather than widening the already dense context row.

### `project_run_revisions`

One row per Run, constrained to version 2. It stores:

- Run ID and result version.
- Structured changes and feedback digest.
- Revised draft, composition, and Critic JSON.
- Server `revised_at`.

The Run ID is unique, making a second revision impossible at the database boundary.

### `project_run_operations`

One row per logical `feedback` or `retry` operation. It stores:

- Run ID and operation kind.
- SHA-256 digest of the idempotency key, never the raw key.
- Canonical request fingerprint.
- operation state: `in_progress`, `succeeded`, `failed_retryable`, or `failed_final`.
- bounded retry condition/action when applicable.
- serialized public response after success.
- server timestamps.

Uniqueness is `(run_id, operation_kind, idempotency_key_digest)`. The repository uses `BEGIN IMMEDIATE` and compare-and-set transitions so concurrent requests cannot create two revisions or double-increment counters.

## Idempotency behavior

Both mutation endpoints require `Idempotency-Key` containing 16-128 URL-safe characters.

- Same Run, operation kind, key digest, and request fingerprint returns the stored public response.
- Same key digest with a different fingerprint returns `409 idempotency_conflict`.
- A different feedback key after version 2 exists returns `409 revision_limit_reached`.
- An in-progress duplicate returns `409 operation_in_progress`; it does not start parallel work.
- Raw keys and raw feedback are never logged or returned.

Client idempotency remains distinct from any future provider idempotency.

## Feedback/revision API

`POST /api/v1/runs/{run_id}/feedback`

- Requires the existing exact Run update capability.
- Requires `Idempotency-Key`.
- Accepts `FeedbackRequest` and validates the path/body Run match.
- Requires Day 14 `ready`, version 1 composition, and a non-reject Critic report.
- Claims the one revision operation, transitioning `ready -> in_progress`.
- Produces revised copy and composition, runs Critic, and atomically persists version 2, `human_revision_count = 1`, and the stored response.
- Returns the Run to `ready` for pass, revise, or needs-human-review; a reject becomes `failed_final`.

If a deterministic technical failure is explicitly classified as retryable, the service stores the server retry decision and moves the Run to `failed_retryable` without incrementing `human_revision_count` or exposing version 2. Non-retryable and safety failures become `failed_final`.

## Retry API

`POST /api/v1/runs/{run_id}/retry`

- Requires the exact Run update capability and `Idempotency-Key`.
- Accepts the existing bounded `RetryRequest`; body `run_id` must match the path.
- Requires `failed_retryable` and a stored server-side retry decision for the unfinished feedback operation.
- The client reason category is audit context only and never overrides the stored eligibility or action.
- A new accepted retry atomically increments `technical_attempt_count` and transitions to `in_progress`.
- The service resumes the exact stored structured revision operation; it cannot accept new feedback or new changes.
- Success produces the same single version 2 and sets `human_revision_count = 1`.
- Idempotent retry replay does not increment the technical count again.
- Exhausted, unknown-acceptance, safety, and cultural-human-review decisions fail closed according to the Day 14 matrix.

The retry endpoint never creates a visible result merely by counting an attempt. A visible version appears only if the resumed revision completes and is atomically persisted.

## Artifact failure safety

Revised composition bytes are written to a fresh temporary artifact before the database finalization transaction. If database persistence loses a race or fails, the service deletes that unreferenced artifact. Existing version-1 and version-2 artifacts are never deleted by a retry conflict.

No response exposes artifact filesystem paths. Integrity, TTL, media type, dimensions, SHA-256, protected source IDs, and fixed disclosure remain enforced by the existing composition and export boundaries.

## Person B revision-flow behavior

Add a pure TypeScript module, not a page or network client. Its public state is:

- `idle`
- `submitting`
- `succeeded`
- `conflict`
- `retryable_failure`
- `final_failure`

It consumes generated `FeedbackRequest`, `RevisionCompleted`, and bounded API error codes. Tests prove:

- one or two supported changes can be selected without duplicates;
- submit is disabled when no change is selected or an operation is active;
- success exposes version 1 and version 2 identifiers plus `human_revision_count = 1`;
- `revision_limit_reached`, `idempotency_conflict`, and `operation_in_progress` remain distinct;
- retryable technical failure enables retry, while culture/safety/final failure does not;
- replayed success does not append a third visible version.

## Error handling

Public status mapping:

- `401 invalid_capability`: missing, malformed, expired, or wrong-scope capability.
- `403 capability_subject_mismatch`: valid capability for a different Run.
- `404 run_not_found`: absent Run.
- `409 invalid_run_state`: prerequisites or server retry eligibility are missing.
- `409 idempotency_conflict`: one key is reused for different input.
- `409 operation_in_progress`: the same logical operation is active.
- `409 revision_limit_reached`: version 2 already exists under another feedback operation.
- `422 invalid_revision_request`: unsupported or contradictory structured change.
- `500 revision_failed` or `retry_failed`: generic bounded unexpected failure.

Errors never echo feedback, keys, tokens, paths, exception text, or stored private data.

## Test strategy

Use strict RED-GREEN-REFACTOR cycles.

### Person A

- Reverse Critic chronology is rejected atomically; relative-time happy path is stable.
- First feedback creates version 2 and increments human revision once.
- Exact replay returns identical response and unchanged counters.
- Different request under the same key conflicts.
- Different key after success reaches the revision limit.
- Concurrent feedback calls produce only one revision row and one visible version 2.
- Brand Lock, facts, CTA meaning, protected layer IDs, dimensions, and disclosure remain exact.
- Technical failure stores only a retryable operation, with no version 2 and no human count.
- One accepted retry increments technical attempts once and resumes the same operation.
- Retry replay does not increment again; exhausted or unsafe decisions fail closed.
- Orphan revised artifacts are cleaned after persistence conflict/failure.

### Person B

- Bilateral shortened-copy fixtures remain readable and fact-supported.
- Generated schema and TypeScript declarations include revision contracts and literals.
- Pure revision-flow states cover success, three conflict classes, retryable failure, and final failure.
- No test or response treats cultural hypotheses as accepted facts.

### Release gate

- Full Python suite and Ruff.
- Contract export/check and generated TypeScript test.
- Full Vitest, ESLint, TypeScript, and webpack production build.
- Public-boundary scan and `git diff --check`.
- Both directions complete version-1 Critic -> one feedback -> version-2 Critic through public HTTP APIs.

## Delivery

The Day 15 delivery contains:

- one Issue with approved acceptance criteria;
- the design and implementation plan;
- focused implementation commits and generated contracts;
- `Day15.docx` in the private parent folder, following the established Day 14 format;
- a non-force update of GitHub `main` only after verifying the partner has not moved it;
- successful GitHub Actions evidence;
- removal of Day 15 test, render, and API-upload temporary directories.

## Acceptance boundary

Day 15 is complete when both fixture directions retain immutable version 1, accept exactly one structured human revision, expose exactly one version 2, reject any further human revision, allow only server-authorized technical retry without double-counting or extra visible versions, pass the complete release gate, produce a visually verified `Day15.docx`, and publish the verified tree to remote `main` without force.
