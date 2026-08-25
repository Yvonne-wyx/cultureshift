# Day 14 Workflow State and Deterministic Critic Design

**Date:** 2026-08-25

**Issue:** [#13](https://github.com/Yvonne-wyx/cultureshift/issues/13)

**Plan item:** Day 14 / T09

**Roles:** Person A (Engineering/AI/Backend) and Person B (Product/Frontend/Research)

## Purpose

Day 14 adds the smallest trustworthy post-composition review stage to the existing Day 13 bilateral fixture pipeline. The increment makes workflow state and version counters explicit, persists the evidence needed for factual review, and introduces a deterministic Critic. The Critic reviews an already persisted composition and never creates a second visible result.

This design follows the repository's current modular-monolith structure. It does not replace the existing analysis, Brand Lock, draft, composition, export, capability, or asset-lifecycle services.

## Scope

### Person A

- Make post-composition workflow transitions explicit and testable.
- Persist initial-generation, human-revision, and technical-attempt counters.
- Backfill existing composed rows to one initial visible generation.
- Preserve draft fact references for Critic evidence checks.
- Define a pure retry-decision policy without adding a retry endpoint.
- Persist one immutable Critic report per Run and make repeated review calls idempotent.

### Person B

- Define structured Critic statuses and issue records.
- Implement deterministic checks for Brand Lock, facts, readability, cultural language, and safety.
- Add fixtures for brand mismatch, unsupported facts, unreadable copy, absolute cultural claims, possible stereotypes, safety refusal, and a clean pass.
- Preserve cultural uncertainty and require human review where evidence is incomplete.

## Explicit non-goals

- No `/feedback` or `/retry` endpoint.
- No second visible composition and no revision generation.
- No revision form, comparison page, or other new Studio UI.
- No live provider or paid call.
- No automatic cultural validation or claim that a target-market reviewer approved an output.
- No broad repository, API, or frontend refactor.

These items remain Day 15 or later work.

## Workflow model

### States

Extend both public `RunStatus` and internal `ProjectRunStatus` with:

- `ready`: composition and Critic report are available for display, export gating, or a later explicit feedback action.
- `failed_retryable`: a technical failure may be retried only under the stored retry decision.
- `failed_final`: the Run cannot proceed without a new Run or corrected source input.

Keep the existing `pending`, `in_progress`, `awaiting_brand_lock`, `blocked`, `completed`, and `failed` values for compatibility. Day 14 does not remove or reinterpret previously exported values.

### Relevant transitions

The state machine permits only these new transitions:

- `in_progress -> ready` after Critic returns `pass`, `revise`, or `needs_human_review`.
- `in_progress -> failed_retryable` after a retry-policy decision that requires explicit user action.
- `in_progress -> failed_final` after Critic returns `reject` or a non-retryable workflow failure occurs.
- `failed_retryable -> in_progress` is reserved for the Day 15 explicit retry operation.
- `ready -> in_progress` is reserved for the Day 15 explicit human revision operation.

Day 14 tests the reserved transitions but does not expose routes that invoke them. Terminal `completed` and `failed_final` states do not transition.

The current `ProjectRun.with_status` method remains the single domain enforcement point. Repository updates must use compare-and-set conditions so stale or concurrent writers cannot bypass the domain model.

## Counters and visible-version semantics

Store these non-negative integers in `project_run_contexts`:

- `initial_generation_count`, maximum 1.
- `human_revision_count`, maximum 1.
- `technical_attempt_count`, no visible-version effect.

`save_composition` atomically changes `initial_generation_count` from 0 to 1 when it stores the first composition. Returning the same stored composition is idempotent and does not increment the counter. A different composition remains an immutable conflict.

The SQLite initialization migration adds the columns with zero defaults, then backfills `initial_generation_count = 1` for rows whose `composition_json` is already present. This preserves truthful semantics for databases created before Day 14.

Day 14 never increments `human_revision_count`. The retry-policy tests prove that changing `technical_attempt_count` does not change either visible counter or create another composition.

## Persisted factual evidence

`DraftGenerator` already returns `fact_references`, but `DraftRecord` currently discards them. Add `draft_fact_references_json` to `project_run_contexts`, persist it atomically with the brief, copy, rules, and generation timestamp, and expose it through `DraftRecord`.

The persisted references must exactly match a subset of the confirmed Brand Lock's `verified_product_facts`. Missing, malformed, or unsupported references fail closed. Existing databases with a draft but no fact-reference column are backfilled from the confirmed Brand Lock because the current fixture generator required exact equality before saving; this migration fact is covered by a repository test.

## Critic contracts

### Status

`CritiqueStatus` contains:

- `pass`: no issue was found and no cultural hypothesis requires review.
- `revise`: the result can remain visible, but an explicit human feedback action is recommended.
- `needs_human_review`: the result remains a hypothesis-bearing concept and requires accountable review.
- `reject`: final export is blocked for Brand Lock, factual, or safety reasons.

### Issue

Each `CritiqueIssue` contains only public-safe structured data:

- `code`: stable machine-safe warning code.
- `category`: `brand_lock`, `fact`, `readability`, `culture`, or `safety`.
- `severity`: `warning` or `blocking`.
- `message`: bounded non-sensitive explanation.
- `requires_human_review`: boolean.

The report does not echo raw upload text, OCR, tokens, local paths, or provider payloads.

### Report

Expand `CritiqueReport` to contain:

- `status`.
- `issues` in deterministic category/code order.
- `brand_lock_preserved`.
- `requires_human_review`.
- `reviewed_at` as UTC.

Validation requires:

- `reject` when any blocking Brand Lock, fact, or safety issue exists.
- `needs_human_review` when cultural ambiguity or possible stereotype review is the highest issue.
- `revise` for non-blocking readability or absolute-claim corrections.
- `pass` only when `issues` is empty and `requires_human_review` is false.

## Deterministic Critic

Create `src/cultureshift/critic.py` with `Critic.review(CriticRequest) -> CritiqueReport`.

`CriticRequest` is assembled from trusted persisted records: analysis, confirmed Brand Lock, draft including fact references, composition evidence, and existing non-sensitive warning codes. The HTTP route never accepts these artifacts from the client.

The Critic evaluates checks in this order:

1. **Safety:** a persisted refusal or prohibited-content code produces blocking `safety_refusal` and `reject`.
2. **Brand Lock:** brief lock equality, CTA action meaning, logo source ID, product UI source ID, and fixed protected-layer evidence must match the confirmation. Any mismatch produces blocking `brand_lock_mismatch` and `reject`.
3. **Facts:** each persisted fact reference must exist in the confirmed verified-fact set. Unsupported or missing evidence produces blocking `unsupported_fact` and `reject`.
4. **Readability:** deterministic fixture limits and composition layer bounds check headline, body, and CTA fit. Failure produces `copy_unreadable` and `revise`.
5. **Culture:** bounded multilingual phrase rules detect absolute population-wide claims and known fixture stereotype patterns. Absolute claims produce `absolute_cultural_claim` and `revise`; a possible stereotype produces `possible_stereotype` and `needs_human_review`. These rules are guardrails, not cultural truth classifiers.
6. **Pending hypotheses:** any pending `CulturalHypothesis` produces `cultural_hypothesis_pending` and `needs_human_review`, unless a higher blocking status already applies.

The normal Day 13 fixture is expected to return `needs_human_review`, not `pass`, because its cultural hypotheses remain pending. The clean-pass unit fixture intentionally contains no cultural hypothesis. This distinction prevents the technical test fixture from being presented as culturally validated.

## Retry-decision policy

Create a pure policy in `src/cultureshift/workflow.py`. It returns a decision and never calls a provider:

- Proven connection failure before provider acceptance: `retry_once`.
- Provider-supported idempotency with a known call ID: `poll_existing`.
- Unknown acceptance after timeout and no pollable ID: `require_explicit_acknowledgement` and `failed_retryable`.
- Invalid schema: `repair_once`.
- Safety refusal: `do_not_retry` and `failed_final`.
- Brand Lock composition failure: `recompose_same_layers_once`; a repeated failure becomes `failed_final`.
- Cultural ambiguity: `require_human_review`; never retry or promote it to fact.

Client idempotency is never described as provider idempotency. Day 15 will consume this policy when it adds explicit retry integration.

## Persistence and idempotency

Add `critique_json` and `critic_reviewed_at` to `project_run_contexts`.

`save_critique` runs inside `BEGIN IMMEDIATE` and requires:

- Run status `in_progress`.
- Confirmed Brand Lock, draft, and composition all present.
- `initial_generation_count == 1`.
- no existing Critic report.

If the exact report already exists, return it without changing state or counters. If a different report is proposed, return a conflict. The report and status transition are stored in the same transaction.

## API

Add:

`POST /api/v1/runs/{run_id}/critic -> 200 CritiqueCompleted`

The endpoint:

- requires the existing Bearer capability with the Run's compose/read scope convention;
- accepts no body;
- loads all Critic input from the repository;
- returns the stored response on repeat calls;
- returns `401` for missing/invalid capability, `403` for scope or Run mismatch, `404` for absent Run, `409` for missing prerequisites or invalid state, and a generic `500` for unexpected storage errors;
- never exposes raw submitted content or internal exceptions.

`CritiqueCompleted` contains `run_id`, resulting `status`, the structured report, the three counters, and `reviewed_at`.

The endpoint does not require an `Idempotency-Key` because the Run has exactly one immutable Day 14 Critic report and the request body is empty. Day 15 feedback and retry requests will require payload fingerprints and explicit keys.

## Contract generation and frontend boundary

Pydantic remains the contract source of truth. Regenerate JSON Schema and TypeScript declarations after adding statuses, issue/report contracts, and `CritiqueCompleted`.

Person B's Day 14 frontend responsibility is limited to proving that generated declarations expose the structured Critic result safely. No component or page is added. A small TypeScript contract test may validate the status union and issue categories without duplicating backend business rules.

## Error handling and safety

- Missing or internally inconsistent persisted evidence fails closed.
- No endpoint accepts cultural verdicts or Critic evidence supplied by a browser.
- Machine codes are public-safe and bounded.
- Cultural checks are explicitly heuristic guardrails and never mark a hypothesis accepted.
- A `reject` report blocks the later export gate; Day 14 does not delete an already generated internal fixture artifact.
- No secret, personal information, private project context, or local absolute path enters contracts, logs, tests, fixtures, documentation, or Issue output.

## Test strategy

Use strict RED-GREEN-REFACTOR cycles.

### Person A tests

- Allowed and rejected state transitions.
- Counter validation and backfill.
- First composition increments once; identical replay does not increment.
- A new composition remains an immutable conflict.
- Technical-attempt changes do not create a visible version.
- Retry decision matrix covers every policy branch.
- Critic persistence is atomic and immutable.

### Person B tests

- Brand mismatch -> `reject`.
- Unsupported fact -> `reject`.
- Unreadable copy -> `revise`.
- Absolute cultural claim -> `revise`.
- Possible stereotype -> `needs_human_review`.
- Safety refusal -> `reject`.
- No issue and no hypothesis -> `pass`.
- Pending fixture hypothesis -> `needs_human_review`.

### API and contract tests

- Capability authentication and ownership isolation.
- Bodyless request validation.
- Prerequisite and state conflicts.
- Successful bilateral review.
- Repeated request returns identical payload and unchanged counters.
- Generated schema and TypeScript declarations are current.
- Existing Day 1-13 tests, Ruff, web tests, build, and public-boundary checks remain green.

## Delivery and evidence

The Day 14 delivery contains:

- one reviewable implementation commit series linked to Issue #13;
- generated contracts committed with their Pydantic source;
- fresh RED/GREEN and full-suite verification evidence;
- `Day14.docx` stored only in the private parent folder, matching the established Day document format;
- a fast-forward update of GitHub `main` after a final remote-head check.

Temporary test, spreadsheet, render, and document-QA directories are removed after verification. Only the repository changes and final `Day14.docx` remain.

## Acceptance boundary

Day 14 is complete when Issue #13's acceptance criteria pass, the deterministic Critic and state machine operate on both fixture directions, no second visible version can be created, the full local verification is clean, the final DOCX passes render inspection, and the verified commit is present on remote `main`.
