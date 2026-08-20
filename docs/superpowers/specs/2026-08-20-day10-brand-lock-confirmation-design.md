# Day 10 Brand Lock Confirmation Design

**Date:** 2026-08-20

**Plan row:** Day 10 / T06

**Tracking:** GitHub Issue #9

https://github.com/Yvonne-wyx/cultureshift/issues/9

## Goal

Complete Day 10 with the smallest safe vertical slice that confirms a reviewed
Brand Lock through an authenticated backend API, freezes the confirmed value,
and replaces the Day 9 preparation surface with a tested interactive form. The
confirmed run returns to `in_progress` so Day 11 can consume an explicit,
immutable Brand Lock.

## Approved product boundary

The form submits a complete `BrandLock` snapshot so the backend can detect
client-side tampering. Before confirmation, users may change only:

- `benefit_order`, as a complete permutation of the analyzed benefits; and
- `localizable_fields`, as a non-empty unique subset of the analyzed allowlist.

The following fields remain locked to the validated Day 9 analysis:

- `logo_asset_id`;
- `product_name`;
- `verified_product_facts`, including their approved order;
- `product_ui_asset_ids`, including their approved order;
- `cta_action_meaning`; and
- `layout_template_asset_id`.

After the first successful confirmation, the whole resulting `BrandLock` is
immutable. An identical retry is idempotent; a different retry is rejected.

## Scope and non-goals

Day 10 includes:

- authenticated `POST /api/v1/runs/{run_id}/brand-lock/confirm`;
- full-snapshot validation against the stored Day 9 `AdAnalysis`;
- atomic confirmation persistence and
  `awaiting_brand_lock -> in_progress` transition;
- idempotent replay for an identical confirmed snapshot;
- immutable conflict handling for any later different snapshot;
- generated JSON Schema and TypeScript contracts;
- an accessible client-side `BrandLockForm` for the two fixture directions;
- benefit reordering, localizable-field selection, locked-field previews, and
  explicit pending/success/error UI states;
- fixture-only form submission through an injected confirmation function.

Day 10 excludes:

- live API credentials or browser token storage;
- direct fixture-page calls to the backend;
- draft persistence, autosave, undo history, or multi-step approval;
- replacement or upload of logo, product UI, or layout assets;
- editing product name, facts, CTA meaning, or other locked fields;
- creation of creative briefs, copy, images, exports, or Day 11 behavior;
- automated cultural validation or presentation of hypotheses as facts;
- new frontend or backend dependencies.

## Person A design

### Public contracts

Add `BrandLockConfirmation` with one field:

```python
brand_lock: BrandLock
```

The complete snapshot is deliberate: the backend validates every locked field
instead of trusting disabled or read-only browser controls.

Add `BrandLockConfirmed` with:

```python
run_id: UUID
status: Literal[RunStatus.IN_PROGRESS]
brand_lock: BrandLock
confirmed_at: UtcDatetime
```

No path, token, raw image, private evidence, or unvalidated text is returned.
Both contracts are registered in `ContractRegistry`, exported to JSON Schema,
and regenerated into TypeScript.

### Confirmation validator

Create a focused backend module that compares the proposed snapshot with the
stored analysis lock. It returns a validated `BrandLock` or raises one of three
bounded domain errors:

- `locked_field_changed` when a read-only field differs;
- `benefit_order_invalid` unless the proposed values are an exact permutation
  of the analyzed benefits; and
- `localizable_fields_invalid` unless the proposal is a non-empty subset of
  the analyzed allowlist.

Pydantic already rejects duplicate values, unknown fields, invalid UUIDs,
oversized sequences, and unsupported localizable-field enum values. The
validator never includes proposed or stored values in an exception message.

### Capability boundary

The existing run capability token gains `project_run:update` in addition to
read and analyze capabilities. The confirmation endpoint requires
`Capability.UPDATE_PROJECT_RUN` and an exact token-subject/run-ID match.

The endpoint reuses the existing stable authentication behavior:

- missing, malformed, expired, or insufficient token: `401 invalid_capability`;
- valid token for another run: `403 capability_subject_mismatch`;
- unknown run: `404 run_not_found`.

No new token is issued and no capability token is persisted.

### Repository and immutability

Extend `project_run_contexts` with nullable columns:

- `confirmed_brand_lock_json TEXT`;
- `brand_lock_confirmed_at TEXT`.

`initialize()` performs additive migration for existing Day 9 databases. A
repository method loads the stored validated analysis and performs validation,
persistence, and state transition inside one SQLite transaction.

First confirmation requires:

- run status exactly `awaiting_brand_lock`;
- a stored validated analysis;
- no existing confirmed Brand Lock; and
- a proposal accepted by the confirmation validator.

The transaction stores only the validated final `BrandLock` and UTC confirmation
time, then conditionally changes the run from `awaiting_brand_lock` to
`in_progress`. Any failed conditional update rolls back both writes.

If a confirmed record already exists:

- an equal proposal returns the original record and timestamp without another
  write; and
- a different proposal raises `brand_lock_immutable`.

SQLite write serialization plus conditional status/update predicates ensure
that two concurrent first confirmations cannot both win.

### Endpoint behavior

`POST /api/v1/runs/{run_id}/brand-lock/confirm` accepts
`BrandLockConfirmation` and returns `BrandLockConfirmed`.

Stable application results are:

- `200` for first confirmation or identical idempotent retry;
- `409 invalid_run_state` when the run has not reached
  `awaiting_brand_lock` and no confirmation exists;
- `409 brand_lock_immutable` for a different post-confirmation snapshot;
- `422 locked_field_changed`, `benefit_order_invalid`, or
  `localizable_fields_invalid` for a bounded confirmation violation; and
- `500 brand_lock_persistence_failed` for unexpected repository failure.

Error bodies contain only stable codes. They do not echo submitted values,
local paths, provider output, database text, or exception details.

## Person B design

### Component boundaries

Replace `BrandLockPreparation` with a focused client component:

```typescript
type ConfirmBrandLock = (
  brandLock: BrandLock,
) => Promise<BrandLockConfirmed>;
```

`BrandLockForm` receives the initial fixture lock, preview metadata, direction
label, and injected `confirmBrandLock` function. This keeps rendering and form
state independent from transport and makes component tests deterministic.

A small fixture-only client wrapper supplies a deterministic offline confirmer.
The results page passes only serializable fixture data into that wrapper. The
fixture wrapper does not call `fetch`, read a capability token, or claim that a
real backend record was changed.

### Form behavior

The form preserves the Day 9 field order and previews.

Locked fields render as text, lists, and images, not editable controls. Benefit
order renders with native buttons to move each item up or down. Localizable
fields render as checkboxes constrained to the Day 9 allowlist; the component
prevents submitting an empty selection.

The submit button:

- is enabled only when the current client state is valid;
- is disabled while confirmation is pending;
- sends the complete reconstructed `BrandLock` snapshot;
- shows a neutral alert for stable errors without echoing raw error objects;
- changes to a confirmed state after success; and
- disables all mutation controls after success.

The success surface displays `in_progress` and states that the Brand Lock is
confirmed and immutable. The existing pending-human-review notice remains,
because Brand Lock confirmation does not approve cultural hypotheses.

### Accessibility and fixture truthfulness

Every move button includes the benefit name and direction in its accessible
name. Each checkbox is associated with its field label. The form uses native
`disabled`, `fieldset`, `status`, and `alert` semantics. Preview images keep the
direction-specific accessible names introduced on Day 9.

The existing `Fixture Demo / 非实时模型` watermark remains visible. Offline
confirmation is explicitly labeled as fixture behavior and never claims that a
production backend or human reviewer was contacted.

## Testing strategy

Implementation follows small RED-to-GREEN batches.

Focused Python tests cover:

- public contract closure, aliases, literal status, and generated output;
- locked-field tampering for all six locked categories;
- exact benefit permutation requirements;
- localizable-field subset requirements;
- additive database migration;
- atomic first confirmation and `in_progress` transition;
- equal retry preserving the original timestamp;
- different retry returning an immutable conflict;
- two concurrent confirmations with exactly one winning value;
- missing analysis and invalid-state rollback;
- authentication, subject isolation, sanitized validation, and generic errors.

Focused web tests cover:

- exact eight-field order and locked/editable boundary;
- benefit move-up/move-down behavior;
- non-empty localizable selection;
- complete submitted snapshot;
- pending, successful, immutable, and stable-error states;
- post-success control disabling;
- both fixture directions, previews, watermark, and pending-hypothesis copy;
- absence of network calls in the fixture wrapper.

After focused GREEN, run the complete Python/Ruff/schema/TypeScript/Vitest/
typecheck/lint/build/audit/public-boundary gate. Publication requires a clean
worktree, a fresh remote-main comparison, an exact remote tree match, and green
GitHub Actions.

## Acceptance criteria

Day 10 is complete when:

1. Issue #9 and this approved design define the scope.
2. A capability-authorized run in `awaiting_brand_lock` can confirm one valid
   full Brand Lock snapshot and returns `in_progress`.
3. Only benefit ordering and localizable-field selection may differ from the
   analyzed lock; all other changes fail closed with stable codes.
4. The confirmed Brand Lock and timestamp are stored atomically and never
   include sensitive data.
5. Identical retries are idempotent and any different retry is rejected as
   immutable, including under concurrent requests.
6. The fixture UI provides accessible controls and previews without making a
   real network call or implying cultural approval.
7. Full local gates pass, `Day10.docx` records observed evidence, remote main is
   updated without overwriting partner work, and GitHub CI is green.
