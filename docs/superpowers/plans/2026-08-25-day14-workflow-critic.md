# Day 14 Workflow State and Deterministic Critic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit post-composition workflow state, truthful result counters, a deterministic Critic, and an idempotent authenticated Critic API for both fixture directions.

**Architecture:** Extend the existing Pydantic/domain contracts and SQLite context row instead of adding a new service or database. A focused `workflow.py` owns retry decisions, while `critic.py` evaluates only trusted persisted artifacts; `app.py` assembles those artifacts and the repository atomically stores the immutable report and state transition.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, SQLite, pytest, Ruff, JSON Schema, TypeScript/Vitest.

**Spec:** `docs/superpowers/specs/2026-08-25-day14-workflow-critic-design.md`

## Global Constraints

- Work against GitHub Issue #13 and preserve the Day 13 tree as the baseline.
- Do not add `/feedback`, `/retry`, a second composition, revision UX, a live provider, or paid calls.
- `initial_generation_count` and `human_revision_count` have a server-enforced maximum of 1; technical attempts never create a visible version.
- Critic cultural checks are heuristic guardrails and never approve a `CulturalHypothesis`.
- The normal bilateral fixtures remain `Fixture Demo / 非实时模型` and require human review.
- Pydantic contracts remain the source of truth for JSON Schema and TypeScript declarations.
- Never commit secrets, private paths, raw uploads, OCR, provider payloads, personal data, or fabricated review evidence.
- Use a failing test before each production behavior and run the named RED command before implementation.

## File structure

- Modify `src/cultureshift/domain.py`: internal states, counters on `ProjectRun`, and transition rules.
- Modify `src/cultureshift/contracts.py`: public states and structured Critic response contracts.
- Create `src/cultureshift/workflow.py`: pure retry-decision policy only.
- Create `src/cultureshift/critic.py`: deterministic Critic and trusted request model.
- Modify `src/cultureshift/repository.py`: migrations, draft evidence, counters, critique persistence.
- Modify `src/cultureshift/app.py`: bodyless authenticated Critic route and dependency wiring.
- Modify `tests/test_domain.py`: transition and counter validation.
- Create `tests/test_workflow.py`: retry-policy matrix.
- Create `tests/test_critic.py`: seven required Critic fixtures plus pending-hypothesis truthfulness.
- Modify `tests/test_repository.py`: migrations, backfill, and immutable critique persistence.
- Modify `tests/test_app.py`: authentication, prerequisites, bilateral success, and idempotency.
- Modify `tests/test_contracts.py`: Critic contract invariants.
- Modify `tests/test_schema_export.py`: schema presence/currentness.
- Modify `apps/web/scripts/generate-contracts.test.mjs`: generated TypeScript status/category assertions.
- Regenerate `contracts/json-schema/cultureshift.contracts.schema.json` and the existing generated TypeScript declaration target.

---

### Task 1: Make workflow states and counters explicit

**Files:**

- Modify: `src/cultureshift/domain.py`
- Modify: `src/cultureshift/contracts.py`
- Modify: `tests/test_domain.py`
- Modify: `tests/test_contracts.py`

**Interfaces:**

- Produces: `ProjectRunStatus.READY`, `FAILED_RETRYABLE`, `FAILED_FINAL`.
- Produces: `ProjectRun.initial_generation_count`, `human_revision_count`, `technical_attempt_count`.
- Produces: matching public `RunStatus` values.
- Consumed later by: repository migration/persistence and `CritiqueCompleted`.

- [ ] **Step 1: Write failing domain transition and counter tests**

Add tests that construct an in-progress Run, transition it to `ready`, reject `pending -> ready`, allow reserved `ready -> in_progress` and `failed_retryable -> in_progress`, and reject a second initial generation or human revision:

```python
def test_post_composition_transitions_are_explicit() -> None:
    run = ProjectRun(direction=LocalizationDirection.CHINA_TO_UK)
    in_progress = run.with_status(ProjectRunStatus.IN_PROGRESS)
    ready = in_progress.with_status(ProjectRunStatus.READY)
    assert ready.status is ProjectRunStatus.READY
    assert ready.with_status(ProjectRunStatus.IN_PROGRESS).status is ProjectRunStatus.IN_PROGRESS
    with pytest.raises(ValueError, match="invalid status transition"):
        run.with_status(ProjectRunStatus.READY)


@pytest.mark.parametrize(
    ("field", "value"),
    [("initial_generation_count", 2), ("human_revision_count", 2),
     ("technical_attempt_count", -1)],
)
def test_workflow_counters_fail_closed(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        ProjectRun(direction="china_to_uk", **{field: value})
```

- [ ] **Step 2: Run the RED tests**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_domain.py tests/test_contracts.py -q
```

Expected: failures because the new enum members and counter fields do not exist.

- [ ] **Step 3: Implement minimal domain and public contract changes**

Add enum values to both status enums. Add constrained counter fields to `ProjectRun`:

```python
initial_generation_count: int = Field(default=0, ge=0, le=1)
human_revision_count: int = Field(default=0, ge=0, le=1)
technical_attempt_count: int = Field(default=0, ge=0)
```

Update `_ALLOWED_TRANSITIONS` exactly as the design specifies. Ensure `with_status()` preserves all counters through `model_dump()`.

- [ ] **Step 4: Run GREEN tests and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_domain.py tests/test_contracts.py -q
python -m ruff check src/cultureshift/domain.py src/cultureshift/contracts.py tests/test_domain.py tests/test_contracts.py
```

Expected: all selected tests pass and Ruff exits 0.

- [ ] **Step 5: Commit the state model**

```powershell
git add -- src/cultureshift/domain.py src/cultureshift/contracts.py tests/test_domain.py tests/test_contracts.py
git commit -m "feat: define Day 14 workflow state"
```

---

### Task 2: Persist factual evidence and truthful counters

**Files:**

- Modify: `src/cultureshift/repository.py`
- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_repository.py`
- Modify: `tests/test_app.py`

**Interfaces:**

- Produces: `DraftRecord.fact_references: tuple[str, ...]`.
- Produces: atomic first-composition counter increment and migration backfill.
- Produces: `SQLiteProjectRunRepository.increment_technical_attempt(run_id) -> ProjectRun` for later retry integration.
- Consumes: Task 1 counter fields.

- [ ] **Step 1: Write failing repository migration and composition tests**

Cover a fresh row, an existing pre-Day-14 composed row, an identical composition replay, and a technical attempt:

```python
def test_first_composition_counts_once(repository, composed_run, composition) -> None:
    repository.save_composition(composed_run.id, composition)
    first = repository.get(composed_run.id)
    repository.save_composition(composed_run.id, composition)
    replay = repository.get(composed_run.id)
    assert first.initial_generation_count == replay.initial_generation_count == 1
    assert replay.human_revision_count == 0


def test_technical_attempt_never_changes_visible_counts(repository, composed_run) -> None:
    before = repository.get(composed_run.id)
    after = repository.increment_technical_attempt(composed_run.id)
    assert after.technical_attempt_count == before.technical_attempt_count + 1
    assert after.initial_generation_count == before.initial_generation_count
    assert after.human_revision_count == before.human_revision_count
```

Add a repository test proving `save_draft` round-trips exact verified fact references and rejects an unsupported reference before writing.

- [ ] **Step 2: Run repository RED tests**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py -q
```

Expected: failures for absent columns, fields, or methods.

- [ ] **Step 3: Implement the SQLite migration and atomic writes**

Add columns to `project_run_contexts`:

```sql
draft_fact_references_json TEXT,
initial_generation_count INTEGER NOT NULL DEFAULT 0 CHECK(initial_generation_count BETWEEN 0 AND 1),
human_revision_count INTEGER NOT NULL DEFAULT 0 CHECK(human_revision_count BETWEEN 0 AND 1),
technical_attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(technical_attempt_count >= 0)
```

For an existing table, use the repository's current `PRAGMA table_info` migration style, then execute:

```sql
UPDATE project_run_contexts
SET initial_generation_count = 1
WHERE composition_json IS NOT NULL AND initial_generation_count = 0
```

Backfill `draft_fact_references_json` from the confirmed Brand Lock only when a legacy row already has a complete draft and the new column is null. Parse and validate before returning `DraftRecord`.

Change `save_draft` to accept `fact_references`, and change the Day 11 app call to pass `artifacts.fact_references`. In `save_composition`, update `composition_json` and set `initial_generation_count = 1` in the same compare-and-set statement.

Update repository `get()` to join `project_run_contexts` and hydrate all three counters into `ProjectRun`; `create()` continues to initialize them through the context-row defaults.

- [ ] **Step 4: Run GREEN repository and affected API tests**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py tests/test_app.py -q
python -m ruff check src/cultureshift/repository.py src/cultureshift/app.py tests/test_repository.py tests/test_app.py
```

Expected: all selected tests pass with no schema/backfill regression.

- [ ] **Step 5: Commit persistence changes**

```powershell
git add -- src/cultureshift/repository.py src/cultureshift/app.py tests/test_repository.py tests/test_app.py
git commit -m "feat: persist workflow counters and fact evidence"
```

---

### Task 3: Add the pure retry-decision policy

**Files:**

- Create: `src/cultureshift/workflow.py`
- Create: `tests/test_workflow.py`

**Interfaces:**

- Produces: `RetryCondition`, `RetryDecision`, and `decide_retry(condition, attempt_count, provider_call_id) -> RetryDecision`.
- Does not consume repository or provider objects.
- Consumed by: Day 15 explicit retry integration, not by a Day 14 HTTP route.

- [ ] **Step 1: Write the failing decision-table test**

```python
@pytest.mark.parametrize(
    ("condition", "attempts", "call_id", "action", "status"),
    [
        ("connection_before_acceptance", 0, None, "retry_once", "in_progress"),
        ("accepted_with_call_id", 1, "job-1", "poll_existing", "in_progress"),
        ("acceptance_unknown", 1, None, "require_explicit_acknowledgement", "failed_retryable"),
        ("invalid_schema", 0, None, "repair_once", "in_progress"),
        ("safety_refusal", 0, None, "do_not_retry", "failed_final"),
        ("brand_lock_failure", 0, None, "recompose_same_layers_once", "in_progress"),
        ("cultural_ambiguity", 0, None, "require_human_review", "ready"),
    ],
)
def test_retry_policy_is_explicit(condition, attempts, call_id, action, status):
    decision = decide_retry(RetryCondition(condition), attempts, call_id)
    assert decision.action == action
    assert decision.next_status.value == status
```

Add boundary tests proving the second pre-acceptance retry and second same-layer recompose become `do_not_retry/failed_final`.

- [ ] **Step 2: Run the RED test**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_workflow.py -q
```

Expected: import failure because `workflow.py` does not exist.

- [ ] **Step 3: Implement the minimal pure policy**

Use frozen dataclasses and `StrEnum`; validate `attempt_count >= 0` and require a call ID only for `accepted_with_call_id`. Do not import FastAPI, SQLite, or provider adapters.

- [ ] **Step 4: Run GREEN test and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_workflow.py -q
python -m ruff check src/cultureshift/workflow.py tests/test_workflow.py
```

Expected: decision matrix and boundary tests pass.

- [ ] **Step 5: Commit the policy**

```powershell
git add -- src/cultureshift/workflow.py tests/test_workflow.py
git commit -m "feat: encode safe retry decisions"
```

---

### Task 4: Implement structured Critic contracts and deterministic checks

**Files:**

- Modify: `src/cultureshift/contracts.py`
- Create: `src/cultureshift/critic.py`
- Create: `tests/test_critic.py`
- Modify: `tests/test_contracts.py`

**Interfaces:**

- Produces: `CritiqueStatus`, `CritiqueCategory`, `CritiqueSeverity`, `CritiqueIssue`, expanded `CritiqueReport`.
- Produces: `CriticRequest` and `Critic.review(request) -> CritiqueReport`.
- Consumes: persisted `AdAnalysis`, `BrandLock`, `DraftRecord`, and `CompositionGenerated` data supplied by the route.

- [ ] **Step 1: Write seven failing Critic fixture tests**

Build one safe request helper, then modify only the signal under test. Assert exact status and code:

```python
@pytest.mark.parametrize(
    ("fixture_name", "status", "code"),
    [
        ("brand_mismatch", "reject", "brand_lock_mismatch"),
        ("unsupported_fact", "reject", "unsupported_fact"),
        ("unreadable_copy", "revise", "copy_unreadable"),
        ("absolute_cultural_claim", "revise", "absolute_cultural_claim"),
        ("possible_stereotype", "needs_human_review", "possible_stereotype"),
        ("safety_refusal", "reject", "safety_refusal"),
    ],
)
def test_critic_fixture(fixture_name, status, code, critic_requests):
    report = Critic().review(critic_requests[fixture_name])
    assert report.status.value == status
    assert code in {issue.code for issue in report.issues}


def test_clean_request_passes(critic_requests):
    report = Critic().review(critic_requests["clean"])
    assert report.status.value == "pass"
    assert report.issues == ()
```

Add a separate test proving a pending hypothesis returns `needs_human_review` and remains `pending`.

- [ ] **Step 2: Run Critic RED tests**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_critic.py tests/test_contracts.py -q
```

Expected: missing contracts/module or old `CritiqueReport` shape failures.

- [ ] **Step 3: Implement contracts and ordered Critic checks**

Use tuples and frozen Pydantic models. Collect issues in fixed category/code order. Determine final status with this precedence:

```python
if any(issue.severity is CritiqueSeverity.BLOCKING for issue in issues):
    status = CritiqueStatus.REJECT
elif any(issue.code in {"possible_stereotype", "cultural_hypothesis_pending"} for issue in issues):
    status = CritiqueStatus.NEEDS_HUMAN_REVIEW
elif issues:
    status = CritiqueStatus.REVISE
else:
    status = CritiqueStatus.PASS
```

Keep phrase guardrails in named immutable sets. They detect only the documented English/Chinese absolute or fixture-stereotype phrases. Do not add a general cultural classifier.

- [ ] **Step 4: Run GREEN Critic tests and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_critic.py tests/test_contracts.py -q
python -m ruff check src/cultureshift/contracts.py src/cultureshift/critic.py tests/test_critic.py tests/test_contracts.py
```

Expected: all eight Critic scenarios pass and no hypothesis is promoted.

- [ ] **Step 5: Commit Critic behavior**

```powershell
git add -- src/cultureshift/contracts.py src/cultureshift/critic.py tests/test_critic.py tests/test_contracts.py
git commit -m "feat: add deterministic Critic gates"
```

---

### Task 5: Persist Critic atomically and expose the authenticated API

**Files:**

- Modify: `src/cultureshift/repository.py`
- Modify: `src/cultureshift/app.py`
- Modify: `src/cultureshift/contracts.py`
- Modify: `tests/test_repository.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_contracts.py`

**Interfaces:**

- Produces: `CritiqueRecord(report, reviewed_at)`.
- Produces: `SQLiteProjectRunRepository.get_critique(run_id)` and `save_critique(run_id, report)`.
- Produces: `POST /api/v1/runs/{run_id}/critic -> CritiqueCompleted`.
- Consumes: Task 2 persisted artifacts/counters and Task 4 `Critic`.

- [ ] **Step 1: Write failing persistence and API tests**

Repository test:

```python
def test_critique_is_atomic_and_immutable(repository, reviewable_run, report):
    first = repository.save_critique(reviewable_run.id, report)
    replay = repository.save_critique(reviewable_run.id, report)
    assert replay == first
    assert repository.get(reviewable_run.id).status is ProjectRunStatus.READY
    with pytest.raises(CritiqueImmutableError):
        repository.save_critique(reviewable_run.id, changed_report(report))
```

API tests must cover missing token `401`, wrong Run token `403`, missing composition `409`, request body `422`, both directions `200`, and identical replay:

```python
first = client.post(path, headers=capability_headers(token))
second = client.post(path, headers=capability_headers(token))
assert first.status_code == second.status_code == 200
assert second.json() == first.json()
assert second.json()["initial_generation_count"] == 1
assert second.json()["human_revision_count"] == 0
```

- [ ] **Step 2: Run the API RED tests**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py tests/test_app.py -q
```

Expected: missing critique columns/methods/route failures.

- [ ] **Step 3: Implement atomic persistence and route wiring**

Add `critique_json` and `critic_reviewed_at` through the existing migration mechanism. `save_critique` starts `BEGIN IMMEDIATE`, loads prerequisites and counters, returns an exact stored report on replay, and otherwise writes the report plus the compare-and-set state transition in one transaction.

The route loads request, analysis, confirmation, draft, and composition from the repository, calls `Critic.review`, persists it, and returns `CritiqueCompleted`. Configure `create_app` with an injectable `critic` default to keep tests deterministic. Reuse the existing capability helper and error-envelope patterns.

Define `CritiqueCompleted` in `contracts.py` with `run_id`, resulting `RunStatus`, `critique`, the three integer counters, and `reviewed_at`. Register it in `ContractRegistry` so schema generation includes the response without changing `schema_export.py`.

- [ ] **Step 4: Run GREEN API tests and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py tests/test_app.py tests/test_critic.py tests/test_contracts.py -q
python -m ruff check src/cultureshift/repository.py src/cultureshift/app.py src/cultureshift/contracts.py tests/test_repository.py tests/test_app.py tests/test_contracts.py
```

Expected: persistence and route tests pass with identical replay payloads.

- [ ] **Step 5: Commit Critic integration**

```powershell
git add -- src/cultureshift/repository.py src/cultureshift/app.py src/cultureshift/contracts.py tests/test_repository.py tests/test_app.py tests/test_contracts.py
git commit -m "feat: review compositions through Critic API"
```

---

### Task 6: Regenerate contracts and run the Day 14 release gate

**Files:**

- Modify: `tests/test_schema_export.py`
- Modify: `apps/web/scripts/generate-contracts.test.mjs`
- Regenerate: `contracts/json-schema/cultureshift.contracts.schema.json`
- Regenerate: `apps/web/src/generated/contracts.ts`.
- Create outside Git: `D:\create\Diversity\Day14.docx`.

**Interfaces:**

- Consumes: all previous tasks.
- Produces: synchronized backend/frontend contracts and final verification evidence.

- [ ] **Step 1: Write failing schema and TypeScript assertions**

Assert that schema definitions include `CritiqueCompleted`, `CritiqueIssue`, and the four status values. In the existing Node test, assert generated declarations contain:

```javascript
assert.match(output, /"pass" \| "revise" \| "needs_human_review" \| "reject"/);
assert.match(output, /"brand_lock" \| "fact" \| "readability" \| "culture" \| "safety"/);
```

- [ ] **Step 2: Run contract RED tests**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_schema_export.py -q
npm.cmd --prefix apps/web test -- scripts/generate-contracts.test.mjs
```

Expected: assertions fail against stale generated artifacts.

- [ ] **Step 3: Export current contracts**

```powershell
python scripts/export_contracts.py
npm.cmd --prefix apps/web run contracts:generate
```

Use only the existing scripts; do not hand-edit generated JSON or TypeScript.

- [ ] **Step 4: Run the full fresh verification gate**

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='.cultureshift/day14-assets'
python -m pytest -q
python -m ruff check .
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run build
powershell -ExecutionPolicy Bypass -File scripts/verify-public-boundary.ps1
git diff --check
```

Expected: every command exits 0, with no failed Python/Vitest tests, Ruff or ESLint findings, build errors, public-boundary violations, or whitespace errors.

- [ ] **Step 5: Commit generated artifacts and verification tests**

```powershell
git add -- src/cultureshift/contracts.py tests/test_schema_export.py apps/web/scripts/generate-contracts.test.mjs contracts/json-schema/cultureshift.contracts.schema.json apps/web/src/generated/contracts.ts
git commit -m "test: verify Day 14 Critic contracts"
```

- [ ] **Step 6: Create and visually verify `Day14.docx`**

Copy the established Day 13 document structure and record only verified facts: Issue #13, approved scope, commits, RED/GREEN commands and outputs, full verification, limitations, and push result. Use the bundled document renderer to render every page to PNG, inspect every page for clipping/overlap/font/table defects, scrub personal metadata, re-render, and keep only the final DOCX after delivery.

- [ ] **Step 7: Re-check remote and push only the verified commit**

```powershell
Test-NetConnection github.com -Port 443 -InformationLevel Quiet
Test-NetConnection api.github.com -Port 443 -InformationLevel Quiet
git ls-remote https://github.com/Yvonne-wyx/cultureshift.git refs/heads/main
git status -sb
git push origin HEAD:main
```

If GitHub network reset occurs, stop repeating browser uploads and use the already verified GitHub Git Data API path. In either path, require the remote `main` parent to remain the Day 13 commit/tree before updating it, then verify the resulting remote SHA and CI status.

- [ ] **Step 8: Remove only Day 14 temporary directories**

Delete exact top-level `.day14-*` test, sheet, render, and DOCX-QA directories after verifying that `Day14.docx` is outside them. Do not touch the repository, any Git worktree, plan workbook, or `Day*.docx` deliverables.
