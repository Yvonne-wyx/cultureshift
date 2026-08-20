# Day 10 Brand Lock Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Confirm one validated Brand Lock atomically through the backend and replace the Day 9 read-only preparation with a safe, fixture-only interactive form.

**Architecture:** The API accepts a complete Brand Lock snapshot, compares it with the stored Day 9 analysis, permits only benefit reordering and a non-empty localizable-field subset, then stores the confirmed lock and moves the run back to `in_progress` in one SQLite transaction. The web form owns only local UI state and receives an injected offline confirmer, so fixture pages remain deterministic and do not store credentials or call the backend.

**Tech Stack:** Python 3.13+, FastAPI, Pydantic v2, SQLite, pytest, Ruff, Next.js 16, React 19, TypeScript, Vitest, Testing Library.

**Spec:** `docs/superpowers/specs/2026-08-20-day10-brand-lock-confirmation-design.md`

## Global Constraints

- Work only against Day 10 Issue #9 and its acceptance criteria.
- Preserve the static-ad AI software/application MVP and both existing localization directions.
- Submit a complete `BrandLock`, but allow changes only to `benefit_order` and `localizable_fields` before confirmation.
- Keep logo, product name, verified facts, product UI assets, CTA meaning, and layout template equal to the stored analysis.
- Persist only the validated confirmed Brand Lock and UTC timestamp; never persist tokens, private bytes, paths, or unvalidated payloads.
- Identical confirmation retries are idempotent; any different retry is immutable conflict.
- Use the existing `UPDATE_PROJECT_RUN` capability; add no credential, provider, dependency, draft, autosave, or Day 11 behavior.
- Fixture UI makes no network call and retains the `Fixture Demo / 非实时模型` and pending-human-review boundaries.
- Every implementation task follows RED, observed failure, minimal GREEN, focused verification, and an explicit-path commit.

---

### Task 1: Confirmation contracts and invariant validator

**Files:**
- Create: `src/cultureshift/brand_lock_confirmation.py`
- Create: `tests/test_brand_lock_confirmation.py`
- Modify: `src/cultureshift/contracts.py`
- Modify: `tests/test_contracts.py`
- Modify: `tests/test_schema_export.py`
- Regenerate: `contracts/json-schema/cultureshift.contracts.schema.json`
- Regenerate: `apps/web/src/generated/contracts.ts`
- Modify: `apps/web/src/generated/contracts.test.ts`

**Interfaces:**
- Consumes: `BrandLock`, `RunStatus.IN_PROGRESS`, `ContractRegistry`.
- Produces: `BrandLockConfirmation(brand_lock: BrandLock)`.
- Produces: `BrandLockConfirmed(run_id, status: Literal[in_progress], brand_lock, confirmed_at)`.
- Produces: `BrandLockConfirmationError(code: ConfirmationErrorCode)`.
- Produces: `validate_brand_lock_confirmation(proposed: BrandLock, analyzed: BrandLock) -> BrandLock`.

- [ ] **Step 1: Write failing contract tests**

Add tests that construct `BrandLockConfirmation`, require
`BrandLockConfirmed.status == RunStatus.IN_PROGRESS`, reject an extra field,
and require both models in `ContractRegistry.model_json_schema()`.

```python
def test_brand_lock_confirmation_contracts(valid_brand_lock) -> None:
    request = BrandLockConfirmation(brand_lock=BrandLock.model_validate(valid_brand_lock))
    response = BrandLockConfirmed(
        run_id=uuid4(),
        status=RunStatus.IN_PROGRESS,
        brand_lock=request.brand_lock,
        confirmed_at=datetime(2026, 8, 20, tzinfo=UTC),
    )
    assert response.status is RunStatus.IN_PROGRESS
    with pytest.raises(ValidationError):
        BrandLockConfirmation.model_validate({"brand_lock": valid_brand_lock, "note": "x"})
```

- [ ] **Step 2: Run the contract RED**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_contracts.py tests/test_schema_export.py -q
```

Expected: collection/import failure because the two confirmation contracts do not exist.

- [ ] **Step 3: Add public contracts and registry fields**

Add closed Pydantic models in `contracts.py`:

```python
class BrandLockConfirmation(ContractModel):
    brand_lock: BrandLock


class BrandLockConfirmed(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.IN_PROGRESS]
    brand_lock: BrandLock
    confirmed_at: UtcDatetime
```

Register them as `brand_lock_confirmation` and `brand_lock_confirmed` in
`ContractRegistry`.

- [ ] **Step 4: Write validator RED cases**

In `tests/test_brand_lock_confirmation.py`, use one approved lock and prove:

```python
@pytest.mark.parametrize(
    "field",
    [
        "logo_asset_id",
        "product_name",
        "verified_product_facts",
        "product_ui_asset_ids",
        "cta_action_meaning",
        "layout_template_asset_id",
    ],
)
def test_locked_fields_cannot_change(field, approved_lock, changed_value) -> None:
    proposed = BrandLock.model_validate({**approved_lock.model_dump(), field: changed_value})
    with pytest.raises(BrandLockConfirmationError) as caught:
        validate_brand_lock_confirmation(proposed, approved_lock)
    assert caught.value.code is ConfirmationErrorCode.LOCKED_FIELD_CHANGED
```

Add separate cases proving a reversed complete benefit list passes, a missing
or unknown benefit fails `benefit_order_invalid`, a non-empty analyzed subset of
localizable fields passes, and an empty/out-of-allowlist proposal fails
`localizable_fields_invalid`.

- [ ] **Step 5: Run validator RED**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_brand_lock_confirmation.py -q
```

Expected: import failure because `brand_lock_confirmation.py` does not exist.

- [ ] **Step 6: Implement the minimal invariant validator**

Define stable codes and compare values without incorporating either value into
the exception text:

```python
class ConfirmationErrorCode(StrEnum):
    LOCKED_FIELD_CHANGED = "locked_field_changed"
    BENEFIT_ORDER_INVALID = "benefit_order_invalid"
    LOCALIZABLE_FIELDS_INVALID = "localizable_fields_invalid"


def validate_brand_lock_confirmation(proposed: BrandLock, analyzed: BrandLock) -> BrandLock:
    locked_fields = (
        "logo_asset_id",
        "product_name",
        "verified_product_facts",
        "product_ui_asset_ids",
        "cta_action_meaning",
        "layout_template_asset_id",
    )
    if any(getattr(proposed, name) != getattr(analyzed, name) for name in locked_fields):
        raise BrandLockConfirmationError(ConfirmationErrorCode.LOCKED_FIELD_CHANGED)
    if len(proposed.benefit_order) != len(analyzed.benefit_order) or set(
        proposed.benefit_order
    ) != set(analyzed.benefit_order):
        raise BrandLockConfirmationError(ConfirmationErrorCode.BENEFIT_ORDER_INVALID)
    if not proposed.localizable_fields or not set(proposed.localizable_fields) <= set(
        analyzed.localizable_fields
    ):
        raise BrandLockConfirmationError(ConfirmationErrorCode.LOCALIZABLE_FIELDS_INVALID)
    return proposed
```

- [ ] **Step 7: Regenerate and verify public artifacts**

Run:

```powershell
$env:PYTHONPATH='src'
python scripts/export_contracts.py
npm.cmd --prefix apps/web run contracts:generate
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
```

Expected: both freshness checks report `current`, and TypeScript exports one
`BrandLockConfirmation` and one `BrandLockConfirmed`.

- [ ] **Step 8: Run focused GREEN and Ruff**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_contracts.py tests/test_brand_lock_confirmation.py tests/test_schema_export.py -q
python -m ruff check src/cultureshift/contracts.py src/cultureshift/brand_lock_confirmation.py tests/test_contracts.py tests/test_brand_lock_confirmation.py tests/test_schema_export.py
npm.cmd --prefix apps/web test -- contracts.test.ts
```

Expected: all focused tests and Ruff pass.

- [ ] **Step 9: Commit Task 1**

```powershell
git add -- src/cultureshift/contracts.py src/cultureshift/brand_lock_confirmation.py tests/test_contracts.py tests/test_brand_lock_confirmation.py tests/test_schema_export.py contracts/json-schema/cultureshift.contracts.schema.json apps/web/src/generated/contracts.ts apps/web/src/generated/contracts.test.ts
git commit -m "feat: define Day 10 Brand Lock confirmation"
```

### Task 2: Atomic confirmation repository

**Files:**
- Modify: `src/cultureshift/repository.py`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: `BrandLock`, stored `AdAnalysis`, `validate_brand_lock_confirmation`, and `ProjectRunStatus.AWAITING_BRAND_LOCK`.
- Produces: frozen `BrandLockConfirmationRecord(brand_lock: BrandLock, confirmed_at: datetime)`.
- Produces: `BrandLockImmutableError` and `InvalidRunStateError` without private detail.
- Produces: `SQLiteProjectRunRepository.confirm_brand_lock(run_id, proposed, *, confirmed_at=None) -> BrandLockConfirmationRecord`.
- Produces: `SQLiteProjectRunRepository.get_confirmed_brand_lock(run_id) -> BrandLockConfirmationRecord | None`.

- [ ] **Step 1: Write migration and first-confirmation RED tests**

Create a Day 9-shaped database without the two new columns, run `initialize()`,
and assert `PRAGMA table_info(project_run_contexts)` contains
`confirmed_brand_lock_json` and `brand_lock_confirmed_at`.

Add a run with stored analysis and `awaiting_brand_lock`, confirm a permitted
snapshot, and assert:

```python
assert repository.get(run.id).status is ProjectRunStatus.IN_PROGRESS
assert repository.get_confirmed_brand_lock(run.id) == record
assert record.brand_lock.benefit_order == tuple(reversed(original.benefit_order))
assert record.confirmed_at == confirmed_at
```

- [ ] **Step 2: Run repository RED**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py -q
```

Expected: failures because confirmation columns and methods do not exist.

- [ ] **Step 3: Add additive columns and record reader**

Extend the create-table statement and use `PRAGMA table_info` plus two additive
`ALTER TABLE` statements for existing databases. Parse stored JSON only through
`BrandLock.model_validate_json` and parse timestamps with timezone validation.

- [ ] **Step 4: Implement transactional first confirmation**

Inside one `_connect()` context:

1. select run status, analysis JSON, existing confirmed JSON, and timestamp;
2. return an equal existing confirmation unchanged;
3. reject a different existing confirmation with `BrandLockImmutableError`;
4. require status `awaiting_brand_lock` and a stored analysis;
5. validate the proposal against `analysis.brand_lock`;
6. conditionally update the context only when confirmation is null; and
7. conditionally update the run only when status is `awaiting_brand_lock`.

Require both update row counts to be one; raise `InvalidRunStateError` so the
context write rolls back when the status claim is lost.

- [ ] **Step 5: Add idempotence, immutability, concurrency, and rollback tests**

Tests must prove:

- an equal retry preserves the first `confirmed_at`;
- a different retry raises `BrandLockImmutableError` and changes no row;
- two threads proposing different valid benefit orders produce exactly one
  stored value while the loser receives immutable/invalid-state failure; and
- a trigger that changes the run status between context and run updates causes
  a full rollback with no confirmed lock.

- [ ] **Step 6: Run repository GREEN and Ruff**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py -q
python -m ruff check src/cultureshift/repository.py tests/test_repository.py
```

Expected: all repository tests pass and Ruff is clean.

- [ ] **Step 7: Commit Task 2**

```powershell
git add -- src/cultureshift/repository.py tests/test_repository.py
git commit -m "feat: persist immutable Brand Lock confirmation"
```

### Task 3: Capability-protected confirmation API

**Files:**
- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_capability_tokens.py`

**Interfaces:**
- Consumes: `Capability.UPDATE_PROJECT_RUN`, `BrandLockConfirmation`, `BrandLockConfirmed`, and repository confirmation errors.
- Produces: `POST /api/v1/runs/{run_id}/brand-lock/confirm -> BrandLockConfirmed`.
- Produces stable error codes from the approved design.

- [ ] **Step 1: Write API RED tests**

Extend the uploaded/analyzed-run helper so a fixture run reaches
`awaiting_brand_lock`. Test a valid payload with reversed benefits and a
localizable subset, then assert `200`, `status == "in_progress"`, exact returned
lock, repository persistence, and no capability token in the response.

Add focused cases for:

- missing/insufficient token -> `401 invalid_capability`;
- another run's token -> `403 capability_subject_mismatch`;
- unknown run -> `404 run_not_found`;
- pending run -> `409 invalid_run_state`;
- locked field tampering -> `422 locked_field_changed`;
- invalid benefit permutation -> `422 benefit_order_invalid`;
- invalid localizable subset -> `422 localizable_fields_invalid`;
- equal retry -> identical response and timestamp;
- different retry -> `409 brand_lock_immutable`; and
- a repository exception containing a private marker -> generic
  `500 brand_lock_persistence_failed` without the marker.

- [ ] **Step 2: Run API RED**

Run:

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='.cultureshift/assets'
python -m pytest tests/test_app.py tests/test_capability_tokens.py -q
```

Expected: valid confirmation fails because the route and update capability on
new run tokens are absent.

- [ ] **Step 3: Add update capability to run tokens**

Keep the existing enum value and include it when creating a run:

```python
capabilities={
    Capability.READ_PROJECT_RUN,
    Capability.ANALYZE_PROJECT_RUN,
    Capability.UPDATE_PROJECT_RUN,
}
```

Do not persist or reissue the token.

- [ ] **Step 4: Implement the endpoint**

Follow the existing authorization parser and subject check. Call
`runs.confirm_brand_lock(run_id, confirmation.brand_lock)` and map only known
bounded exceptions to the approved 404/409/422 codes. Map any other exception
to `500 brand_lock_persistence_failed` without stringifying it.

- [ ] **Step 5: Verify OpenAPI and sanitized validation locations**

Extend the OpenAPI test to require `BrandLockConfirmation` and
`BrandLockConfirmed`. Submit an unknown JSON key containing an absolute private
path and assert the safe validation handler replaces it with `unknown_field`.

- [ ] **Step 6: Run API GREEN and Ruff**

Run:

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='.cultureshift/assets'
python -m pytest tests/test_app.py tests/test_capability_tokens.py -q
python -m ruff check src/cultureshift/app.py tests/test_app.py tests/test_capability_tokens.py
```

Expected: all focused API/capability tests pass and Ruff is clean.

- [ ] **Step 7: Commit Task 3**

```powershell
git add -- src/cultureshift/app.py tests/test_app.py tests/test_capability_tokens.py
git commit -m "feat: confirm Brand Lock through authenticated API"
```

### Task 4: Interactive fixture BrandLockForm

**Files:**
- Create: `apps/web/src/components/brand-lock-form.tsx`
- Create: `apps/web/src/components/brand-lock-form.module.css`
- Create: `apps/web/src/components/brand-lock-form.test.tsx`
- Create: `apps/web/src/components/fixture-brand-lock-form.tsx`
- Create: `apps/web/src/components/fixture-brand-lock-form.test.tsx`
- Modify: `apps/web/src/app/results/[fixtureId]/page.tsx`
- Modify: `apps/web/src/app/results/[fixtureId]/page.test.tsx`
- Retire: `apps/web/src/components/brand-lock-preparation.tsx`
- Retire: `apps/web/src/components/brand-lock-preparation.module.css`
- Retire: `apps/web/src/components/brand-lock-preparation.test.tsx`
- Reuse: `apps/web/src/brand-lock/brand-lock-form-spec.ts`

**Interfaces:**
- Consumes: generated `BrandLock`, `BrandLockConfirmed`, the Day 9 form spec, and fixture preview data.
- Produces: `ConfirmBrandLock = (brandLock: BrandLock) => Promise<BrandLockConfirmed>`.
- Produces: `BrandLockForm` with locked previews, benefit controls, localizable checkboxes, and confirmation states.
- Produces: `FixtureBrandLockForm`, an offline wrapper with no `fetch` call.

- [ ] **Step 1: Write component RED tests**

Use `fireEvent` and an injected `vi.fn()` confirmer. For each fixture direction,
assert all eight field labels and three field previews remain visible. Assert
locked fields have no textbox/file input and mutation controls exist only for
benefits and localizable fields.

Move the second benefit upward, uncheck one localizable field, submit, and
assert the injected function receives a complete snapshot:

```typescript
expect(confirmBrandLock).toHaveBeenCalledWith({
  ...fixture.preview.brand_lock,
  benefit_order: ["Organize", "Summarize"],
  localizable_fields: ["narrative", "use_scenario", "trust_information"],
});
```

Add tests for empty selection disabling submission, pending state, stable error
alert, successful `in_progress`/immutable copy, and disabled mutation controls
after success.

- [ ] **Step 2: Run component RED**

Run:

```powershell
npm.cmd --prefix apps/web test -- brand-lock-form.test.tsx fixture-brand-lock-form.test.tsx
```

Expected: import failure because the two components do not exist.

- [ ] **Step 3: Implement BrandLockForm state and accessible controls**

Mark only the form component as `"use client"`. Clone the initial arrays into
state, use pure `moveBenefit(index, offset)` logic, and reconstruct a full
`BrandLock` on submit. Use native button/checkbox/fieldset/status/alert
semantics. Catch unknown rejection values and show only
`Unable to confirm Brand Lock.`

- [ ] **Step 4: Implement the offline fixture wrapper**

The wrapper provides an async function that returns:

```typescript
{
  run_id: fixture.request.source_asset.asset_id,
  status: "in_progress",
  brand_lock: submitted,
  confirmed_at: "2026-08-20T00:00:00Z",
}
```

The deterministic fixture UUID is a display-only contract value. Do not call
`fetch`, read storage, or imply a production record changed. Show explicit
`Fixture confirmation only` copy.

- [ ] **Step 5: Replace the Day 9 preparation on result pages**

Render `FixtureBrandLockForm` in the same result-page location and retain the
existing watermark and pending-hypothesis traceability section. Update page
tests to require an enabled confirmation form rather than the Day 9 disabled
button.

- [ ] **Step 6: Run web GREEN, typecheck, and lint**

Run:

```powershell
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
```

Expected: all web tests, TypeScript, and ESLint pass.

- [ ] **Step 7: Commit Task 4**

```powershell
git add -- apps/web/src/brand-lock/brand-lock-form-spec.ts apps/web/src/components/brand-lock-form.tsx apps/web/src/components/brand-lock-form.module.css apps/web/src/components/brand-lock-form.test.tsx apps/web/src/components/fixture-brand-lock-form.tsx apps/web/src/components/fixture-brand-lock-form.test.tsx apps/web/src/app/results/[fixtureId]/page.tsx apps/web/src/app/results/[fixtureId]/page.test.tsx
git rm -- apps/web/src/components/brand-lock-preparation.tsx apps/web/src/components/brand-lock-preparation.module.css apps/web/src/components/brand-lock-preparation.test.tsx
git commit -m "feat: implement Day 10 Brand Lock form"
```

### Task 5: Full convergence, documentation, and publish readiness

**Files:**
- Modify only files required by observed gate failures.
- Create outside repository: `D:\create\Diversity\Day10.docx` using `Day9.docx` as the retained format reference.

**Interfaces:**
- Consumes: all Day 10 commits and the approved Issue/spec.
- Produces: a clean verified tree, independent review evidence, and local Day 10 completion record.

- [ ] **Step 1: Run the complete backend and contract gate**

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='.cultureshift/assets'
python -m pytest -q -p no:cacheprovider
python -m ruff check src tests scripts
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
```

Expected: all Python tests/Ruff pass and both generated artifacts are current.

- [ ] **Step 2: Run the complete web and safety gate**

```powershell
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
$env:NEXT_TELEMETRY_DISABLED='1'
npm.cmd --prefix apps/web run build
npm.cmd --prefix apps/web audit --audit-level=high
powershell -ExecutionPolicy Bypass -File .\scripts\verify-public-boundary.ps1
git diff --check
git status --short
```

Expected: all web/build/audit/public-boundary gates pass and the worktree is clean.

- [ ] **Step 3: Request independent read-only review**

Review the full Day 10 range against the Issue, design, and plan. Treat only
Critical/Important correctness, privacy, immutability, concurrency, contract,
or accessibility findings as blocking. Reproduce every accepted finding with a
failing test before applying a minimal fix, then rerun affected and full gates.

- [ ] **Step 4: Create and structurally verify Day10.docx**

Use the Documents skill, retain `D:\create\Diversity\Day9.docx` as the format
authority, record Person A/B deliverables, RED/GREEN evidence, all observed gate
counts, Issue/commit data, residual warnings, and the Day 11 boundary. Run the
canonical render workflow; if LibreOffice remains unavailable, record that
limitation and run section/style/accessibility/package-preservation audits.

- [ ] **Step 5: Recheck remote main before publication**

Test `github.com` and `api.github.com`, then read remote main. Require its commit
and tree to equal the recorded Day 9 baseline. Stop if a partner commit changed
the remote tree; do not overwrite or force push.

- [ ] **Step 6: Publish only after explicit push authorization**

When normal Git transport works, publish a fast-forward commit whose parent is
the current remote main and whose tree is the verified Day 10 tree. If transport
resets, immediately use the previously verified credential-backed GitHub API
tree/commit/ref path with compare-and-swap semantics. Never force update main.

- [ ] **Step 7: Verify remote tree and GitHub Actions**

Fetch/read the new remote commit, require its tree SHA to equal the local Day 10
tree, then wait for the matching GitHub Actions run to complete successfully.
Update `Day10.docx` with the observed remote commit, tree, and CI URL/conclusion.
