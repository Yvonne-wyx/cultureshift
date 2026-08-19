# Day 9 Analysis Execution and Brand Lock UX Preparation Design

**Date:** 2026-08-19

**Plan row:** Day 9 / T05 + T06

**Tracking:** GitHub Issue #8

https://github.com/Yvonne-wyx/cultureshift/issues/8

## Goal

Complete Day 9 with the smallest fixture-only vertical slice that executes the
Day 8 analysis pipeline through an authenticated API, validates and repairs one
schema-invalid provider response at most once, and reliably moves a successful
run to `awaiting_brand_lock`. Prepare the complete Brand Lock form information
architecture and read-only preview without implementing Day 10 confirmation.

## Scope and non-goals

Day 9 includes:

- authenticated `POST /api/v1/runs/{run_id}/analyze`;
- public-safe request and validated analysis persistence tied to a run;
- temporary asset retrieval with lifecycle and metadata binding checks;
- `pending -> in_progress -> awaiting_brand_lock` on success;
- exactly one repair attempt for schema-invalid provider output;
- deterministic bilateral fixture behavior through the offline provider;
- stable, non-sensitive failure states and API codes;
- a machine-readable Brand Lock UX field specification;
- a fixture-only, accessible, read-only preparation component for both
  localization directions.

Day 9 excludes:

- live providers, network model calls, provider SDKs, credentials, paid calls,
  OCR, prompt persistence, or raw provider payload persistence;
- automated cultural validation or presentation of hypotheses as facts;
- editable Brand Lock controls, confirmation, immutability enforcement, or a
  confirmation API, which belong to Day 10;
- queues, workers, deployment, creative generation, or unrelated redesign;
- real reviewer recruitment or any identity, contact, consent, response, or
  research-participant data.

## Person A design

### Run input and result storage

The existing `project_runs` table remains the source of non-sensitive run
status. A companion table stores the validated `RunCreate` JSON and, after a
successful analysis, the validated public `AdAnalysis` JSON. It never stores
image bytes, filesystem paths, capability tokens, provider exceptions, prompts,
or unvalidated provider output.

Run creation writes the run row and its validated request in one repository
operation. Existing repository callers that create status-only test runs remain
supported. Analysis may start only when a stored request exists.

The validated analysis is stored so that a repeated analyze request after
success is idempotent: it returns the existing public result without calling the
provider again or changing timestamps unnecessarily.

### Temporary asset retrieval

`TemporaryAssetStore` gains a bounded read operation keyed only by UUID. It:

1. rejects tombstoned, absent, expired, or malformed assets;
2. loads the public metadata and image bytes from the private temporary store;
3. verifies the file media signature, byte count, and SHA-256 against metadata;
4. verifies the stored metadata exactly matches the run's `source_asset`;
5. returns bytes only in memory for the duration of analysis.

Errors expose a stable code only. Paths, bytes, metadata text, and OS errors are
not returned or logged.

### Capability and endpoint

Run creation issues one short-lived token with both read-run and analyze-run
capabilities. `POST /api/v1/runs/{run_id}/analyze` requires the analyze
capability and exact subject match.

On the first valid call the endpoint:

1. loads the run and stored validated request;
2. requires status `pending`;
3. changes status to `in_progress`;
4. retrieves and verifies the temporary source asset;
5. invokes the analysis pipeline;
6. persists only the validated `AdAnalysis`;
7. changes status to `awaiting_brand_lock`;
8. returns `AnalysisCompleted` with run ID, final status, validated analysis,
   whether repair was attempted, and a UTC completion time.

An already successful run returns its persisted response without another
provider call. Other invalid state conflicts return a stable 409 code.

### Repair semantics

The provider boundary supports an explicit initial attempt and repair attempt.
The repair call receives the trusted analysis request but not the invalid raw
output. The pipeline attempts repair exactly once and only when Pydantic rejects
the initial provider result as schema-invalid.

No repair occurs for:

- provider exceptions;
- invalid request or asset state;
- instruction-like or prohibited content;
- unsafe target markets, review states, or evidence references;
- unsupported product scope.

The repaired output passes the same closed schema and safety gate as the first
output. If it is still invalid, the result is `provider_output_invalid`.
`AnalysisOutcome` records only the validated `AdAnalysis` and a boolean
`repair_attempted`; raw outputs and validation detail are discarded.

### State and failure behavior

Add `awaiting_brand_lock` to both domain and public run status contracts.
Allowed transitions are:

- `pending -> in_progress | blocked | failed`;
- `in_progress -> awaiting_brand_lock | blocked | failed`;
- `awaiting_brand_lock -> in_progress | failed` as a Day 10-compatible path;
- existing completed and failed terminal behavior remains unchanged.

Input, lifecycle, instruction, prohibited-content, and unsafe-hypothesis
failures move an in-progress run to `blocked`. Provider exceptions and exhausted
schema repair move it to `failed`. The stable failure code is stored only in the
bounded warning-code field and returned in a generic error body. No submitted or
provider-controlled text is echoed.

If persistence fails before a successful result is committed, the endpoint
fails closed. A validated analysis and `awaiting_brand_lock` status are committed
as one repository operation so clients cannot observe the final state without
its result.

## Person B design

### Machine-readable UX specification

Add a typed, immutable `BrandLockFormSpec` in the web application. It defines
the exact Day 10 field order and preparation behavior:

1. logo asset — read-only asset preview;
2. product name — single-line text control;
3. verified product facts — ordered repeatable text controls;
4. product UI assets — ordered asset previews;
5. benefit order — explicit ordering controls;
6. CTA action meaning — semantic action text, distinct from localized label;
7. layout template — read-only template preview;
8. localizable fields — constrained multi-select.

Each entry declares its label, help text, control kind, required or constrained
behavior, and preview requirement. The specification uses generated Brand Lock
field names so contract drift fails TypeScript checks.

### Read-only preparation component

Add `BrandLockPreparation` to each bilateral fixture result page. It consumes
the existing fixture Brand Lock and source/target previews, and displays:

- the exact `awaiting_brand_lock` state;
- all eight field groups in specification order;
- source and target preview context;
- a clear notice that hypotheses remain pending human review;
- a disabled `Confirm Brand Lock — available Day 10` action.

The component has no client state, form submission, event handler, API call,
editable input, or persistence. Native disabled semantics and accessible names
must make the non-interactive boundary testable.

## Contract and generated-output changes

Add these public contracts:

- `RunStatus.AWAITING_BRAND_LOCK`;
- `AnalysisCompleted`, containing `run_id`,
  `status: awaiting_brand_lock`, `analysis`, `repair_attempted`, and
  `completed_at`.

The JSON Schema and generated TypeScript are regenerated from Python. Tests
must prove the status is a literal in `AnalysisCompleted`, generated output is
current, and no duplicate type aliases appear.

## Testing strategy

Implementation follows RED-to-GREEN in small slices.

Focused Python tests cover:

- new status contract and legal/illegal transitions;
- request/result repository round trips without forbidden fields;
- asset retrieval, expiry, tombstone, corruption, and metadata mismatch;
- initial valid output with no repair;
- initial invalid output followed by one valid repair;
- two invalid outputs with exactly two total provider calls;
- no repair for provider, request, lifecycle, or safety failures;
- endpoint authentication, subject isolation, state transitions, idempotence,
  bilateral success, and sanitized failures.

Focused web tests cover:

- exact eight-field specification order and generated-contract field names;
- both fixture directions;
- visible `awaiting_brand_lock` and pending-human-review language;
- all Brand Lock values and both preview contexts;
- disabled confirmation and absence of enabled form submission.

After focused GREEN, run one complete Python/Ruff/schema/generated-TypeScript/
Vitest/typecheck/lint/build/audit/public-boundary verification. The final remote
publication also requires a clean worktree, a fresh remote-main check, and a
successful GitHub Actions run.

## Acceptance criteria

Day 9 is complete when:

1. Issue #8 and this approved design remain the traceable source of scope.
2. A capability-authorized bilateral fixture analysis reaches
   `awaiting_brand_lock` and returns only validated public output.
3. Schema-invalid output receives at most one repair attempt and all other
   failure classes receive none.
4. Run, request, source asset, and returned analysis remain bound without
   persisting or emitting sensitive data.
5. The Brand Lock preparation UI covers all required controls and previews but
   cannot edit or confirm anything before Day 10.
6. Cultural hypotheses remain visibly pending human review and no automated
   cultural-validation claim is introduced.
7. Focused and full local gates pass, `Day9.docx` records observed evidence,
   remote `main` has not been overwritten, and GitHub CI is green.
