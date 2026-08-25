# Day 15 One-Revision and Safe Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one deterministic, Brand-Lock-preserving human revision and one server-authorized technical retry path for both fixture directions, with no extra visible result version.

**Architecture:** Keep Pydantic contracts as the public source of truth, add a small pure fixture revision engine, and isolate revision orchestration in `revision_service.py`. SQLite owns revision uniqueness and idempotency through two focused tables and `BEGIN IMMEDIATE`; FastAPI only authenticates, maps bounded errors, and delegates. Person B receives a pure TypeScript state machine rather than a Day 16 page or network client.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, SQLite, Pillow compositor, pytest, Ruff, JSON Schema, TypeScript 5, Vitest, ESLint, Next.js 16.

**Spec:** `docs/superpowers/specs/2026-08-25-day15-revision-retry-design.md`

## Global Constraints

- Work against GitHub Issue #14 and preserve the fetched Day 14 tree `967cd747aaa8ba094d596996f2df642ffe8b815d` as the baseline.
- Support only `shorten_headline` and `shorten_body`; one request contains one or both without duplicates.
- Raw feedback and raw idempotency keys are never persisted, returned, or logged; persist SHA-256 digests and canonical fingerprints only.
- Exactly one human revision is allowed: version 1 stays immutable, version 2 is unique, and no version 3 exists.
- A technical retry resumes only a stored server-authorized failed feedback operation; client reason text never grants eligibility.
- `initial_generation_count = 1`, `human_revision_count <= 1`, and only a newly accepted retry increments `technical_attempt_count`.
- Preserve confirmed Brand Lock, facts, CTA action meaning, locale, rule IDs, semantic layers, protected source IDs, 1600x900 dimensions, font, and `Fixture Demo / 非实时模型` disclosure.
- Cultural hypotheses remain pending human review; Critic output is a deterministic guardrail, never cultural approval.
- No Day 16 Studio/page/API client, arbitrary prompt execution, live provider, paid call, queue, polling, approval, publishing, or reviewer identity.
- Use a failing test before each production behavior and run the named RED command before implementation.
- Never commit secrets, capability tokens, raw feedback, private paths, temporary SQLite databases, generated artifacts, or fabricated review evidence.

## File structure

- Modify `src/cultureshift/contracts.py`: strict revision request/response and retry request contracts.
- Create `src/cultureshift/revision.py`: pure pinned bilateral copy transformation.
- Create `src/cultureshift/revision_service.py`: feedback/retry orchestration and artifact cleanup.
- Modify `src/cultureshift/repository.py`: chronology guard, operation claims, revision finalization, replay, and counters.
- Modify `src/cultureshift/app.py`: authenticated feedback/retry endpoints and bounded error mapping.
- Modify `tests/test_repository.py`: chronology, uniqueness, CAS, replay, and counter evidence.
- Create `tests/test_revision.py`: pure bilateral revision invariants.
- Create `tests/test_revision_service.py`: success, replay, retry, and orphan cleanup.
- Modify `tests/test_app.py`: public HTTP authentication, conflicts, bilateral success, and retry behavior.
- Modify `tests/test_contracts.py` and `tests/test_schema_export.py`: public contract invariants/currentness.
- Create `apps/web/src/revision/revision-flow.ts`: pure Person B state and transitions.
- Create `apps/web/src/revision/revision-flow.test.ts`: selection, conflict, retry, and visible-version acceptance tests.
- Modify `apps/web/scripts/generate-contracts.test.mjs`; regenerate JSON Schema and generated TypeScript declarations.
- Create private parent-folder `Day15.docx` only after all code gates pass; do not add it to Git.

---

### Task 1: Stabilize Critic chronology before revision work

**Files:**

- Modify: `src/cultureshift/repository.py`
- Modify: `tests/test_repository.py`

**Interfaces:**

- Produces: `save_critique(run_id, report)` rejects `report.reviewed_at < run.created_at` before either table is written.
- Consumed later by: revised Critic persistence, which must maintain the same chronological invariant.

- [ ] **Step 1: Write the failing atomic chronology test and repair the happy fixture**

Change the existing happy report time to `run.created_at + timedelta(seconds=1)`. Add a test that snapshots the run and confirms no critique exists after rejection:

```python
def test_repository_rejects_reverse_critic_chronology_atomically(repository) -> None:
    run = create_composed_run(repository)
    report = passing_report(reviewed_at=run.created_at - timedelta(seconds=1))

    with pytest.raises(InvalidRunStateError, match="Critic time precedes Run"):
        repository.save_critique(run.id, report)

    assert repository.get(run.id).status is ProjectRunStatus.IN_PROGRESS
    assert repository.get_critique(run.id) is None
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py::test_repository_rejects_reverse_critic_chronology_atomically -q
```

Expected: FAIL because `save_critique` currently attempts to persist the invalid earlier timestamp.

- [ ] **Step 3: Add the minimal pre-write guard**

Select `r.created_at` in the existing `BEGIN IMMEDIATE` query and reject before either `UPDATE`:

```python
created_at = datetime.fromisoformat(row["created_at"])
if report.reviewed_at < created_at:
    raise InvalidRunStateError("Critic time precedes Run creation")
```

- [ ] **Step 4: Run GREEN and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py -q
python -m ruff check src/cultureshift/repository.py tests/test_repository.py
```

- [ ] **Step 5: Commit**

```powershell
git add -- src/cultureshift/repository.py tests/test_repository.py
git commit -m "fix: enforce Critic chronology"
```

---

### Task 2: Define strict revision contracts and generated declarations

**Files:**

- Modify: `src/cultureshift/contracts.py`
- Modify: `tests/test_contracts.py`
- Modify: `tests/test_schema_export.py`
- Modify: `apps/web/scripts/generate-contracts.test.mjs`
- Regenerate: `contracts/json-schema/cultureshift.contracts.schema.json`
- Regenerate: the declaration file emitted by `apps/web/scripts/generate-contracts.mjs`

**Interfaces:**

- Produces: `RevisionChange(StrEnum)` values `SHORTEN_HEADLINE` and `SHORTEN_BODY`.
- Produces: `FeedbackRequest(run_id, feedback, requested_changes, submitted_at)` with unique 1-2 enum values.
- Produces: `RetryRequest(run_id, reason_category)` with the existing three bounded categories.
- Produces: `RevisionCompleted` with version 1 summary, revised artifacts, exact counters, and UTC `revised_at`.

- [ ] **Step 1: Write failing contract tests**

```python
def test_feedback_requires_one_or_two_unique_supported_changes(valid_run_id) -> None:
    common = {"run_id": valid_run_id, "feedback": "Please shorten copy.",
              "submitted_at": datetime.now(UTC)}
    assert FeedbackRequest(**common, requested_changes=["shorten_headline"]).requested_changes == (
        RevisionChange.SHORTEN_HEADLINE,
    )
    with pytest.raises(ValidationError):
        FeedbackRequest(**common, requested_changes=[])
    with pytest.raises(ValidationError):
        FeedbackRequest(**common, requested_changes=["shorten_body", "shorten_body"])
    with pytest.raises(ValidationError):
        FeedbackRequest(**common, requested_changes=["change_cta"])


def test_revision_completed_is_exactly_version_two(valid_revision_completed) -> None:
    assert valid_revision_completed.result_version == 2
    assert valid_revision_completed.initial_generation_count == 1
    assert valid_revision_completed.human_revision_count == 1
    with pytest.raises(ValidationError):
        RevisionCompleted(**{**valid_revision_completed.model_dump(), "result_version": 3})
```

Also assert the schema registry exposes `revision_change` and `revision_completed`, and generated TypeScript contains the two exact string literals.

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_contracts.py tests/test_schema_export.py -q
npm.cmd --prefix apps/web test -- scripts/generate-contracts.test.mjs
```

Expected: failures because the strict enum/response and generated declarations do not exist.

- [ ] **Step 3: Implement minimal contract validators**

```python
class RevisionChange(StrEnum):
    SHORTEN_HEADLINE = "shorten_headline"
    SHORTEN_BODY = "shorten_body"


class FeedbackRequest(ContractModel):
    run_id: UUID
    feedback: LongText
    requested_changes: tuple[RevisionChange, ...] = Field(min_length=1, max_length=2)
    submitted_at: UtcDatetime

    @field_validator("requested_changes")
    @classmethod
    def require_unique_changes(cls, value: tuple[RevisionChange, ...]) -> tuple[RevisionChange, ...]:
        if len(set(value)) != len(value):
            raise ValueError("requested changes must be unique")
        return value
```

Define `RevisionCompleted.status` as `Literal[RunStatus.READY, RunStatus.FAILED_FINAL]`, `result_version: Literal[2]`, and counters `initial_generation_count: Literal[1]`, `human_revision_count: Literal[1]`, `technical_attempt_count: int = Field(ge=0)`. Register both new types in `ContractRegistry`.

- [ ] **Step 4: Export and verify contracts**

```powershell
$env:PYTHONPATH='src'
python scripts/export_contracts.py
npm.cmd --prefix apps/web run contracts:generate
python -m pytest tests/test_contracts.py tests/test_schema_export.py -q
npm.cmd --prefix apps/web test -- scripts/generate-contracts.test.mjs
python -m ruff check src/cultureshift/contracts.py tests/test_contracts.py tests/test_schema_export.py
```

- [ ] **Step 5: Commit**

```powershell
git add -- src/cultureshift/contracts.py tests/test_contracts.py tests/test_schema_export.py contracts/json-schema apps/web/scripts apps/web/src/generated
git commit -m "feat: define revision contracts"
```

---

### Task 3: Build the pure bilateral fixture revision engine

**Files:**

- Create: `src/cultureshift/revision.py`
- Create: `tests/test_revision.py`

**Interfaces:**

- Consumes: persisted `DraftRecord`, `LocalizationDirection`, and `tuple[RevisionChange, ...]`.
- Produces: `RevisionArtifacts(brief, ad_copy, fact_references, rule_ids)`.
- Produces: `FixtureRevisionEngine.revise(direction, draft, requested_changes) -> RevisionArtifacts`.

- [ ] **Step 1: Write failing bilateral invariant tests**

```python
@pytest.mark.parametrize("direction", tuple(LocalizationDirection))
def test_fixture_revision_changes_only_selected_copy(direction, fixture_draft) -> None:
    original = fixture_draft(direction)
    revised = FixtureRevisionEngine().revise(
        direction, original, (RevisionChange.SHORTEN_HEADLINE,)
    )
    assert revised.ad_copy.headline != original.ad_copy.headline
    assert len(revised.ad_copy.headline) < len(original.ad_copy.headline)
    assert revised.ad_copy.body == original.ad_copy.body
    assert revised.ad_copy.cta_label == original.ad_copy.cta_label
    assert revised.ad_copy.cta_action_meaning == original.ad_copy.cta_action_meaning
    assert revised.brief == original.brief
    assert revised.fact_references == original.fact_references
    assert revised.rule_ids == original.rule_ids
```

Add the symmetric body-only test and a both-fields test for both directions. Assert pinned outputs contain no absolute cultural claim and retain `Fixture Demo / 非实时模型`.

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_revision.py -q
```

Expected: import failure because `revision.py` does not exist.

- [ ] **Step 3: Implement pinned transformations only**

Use one private immutable fixture per direction:

```python
@dataclass(frozen=True, slots=True)
class _RevisionFixture:
    headline: str
    body: str


_REVISIONS = {
    LocalizationDirection.CHINA_TO_UK: _RevisionFixture(
        headline="Turn approved notes into task summaries",
        body="Orbit AI organises approved notes into task summaries.",
    ),
    LocalizationDirection.UK_TO_CHINA: _RevisionFixture(
        headline="把已批准笔记整理为任务摘要",
        body="Orbit AI 将已批准笔记整理为任务摘要。",
    ),
}
```

Construct a new `AdCopy` with selected fields only; never interpret `feedback`, alter CTA fields, or mutate the input record.

- [ ] **Step 4: Run GREEN and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_revision.py tests/test_critic.py -q
python -m ruff check src/cultureshift/revision.py tests/test_revision.py
```

- [ ] **Step 5: Commit**

```powershell
git add -- src/cultureshift/revision.py tests/test_revision.py
git commit -m "feat: add deterministic fixture revision"
```

---

### Task 4: Add atomic revision and idempotency persistence

**Files:**

- Modify: `src/cultureshift/repository.py`
- Modify: `tests/test_repository.py`

**Interfaces:**

- Produces: `OperationKind`, `OperationState`, `OperationRecord`, and `RevisionRecord` internal dataclasses/enums.
- Produces: `claim_feedback_operation(run_id, key_digest, fingerprint, changes, feedback_digest, claimed_at) -> OperationRecord`.
- Produces: `claim_retry_operation(run_id, key_digest, fingerprint, claimed_at) -> OperationRecord`.
- Produces: `complete_revision(run_id, operation_id, revision, public_response) -> RevisionRecord`.
- Produces: `fail_revision_operation(run_id, operation_id, decision, failed_at) -> OperationRecord` and `get_revision(run_id)`.
- Raises focused repository errors: `IdempotencyConflictError`, `OperationInProgressError`, `RevisionLimitReachedError`, and existing `InvalidRunStateError`.

- [ ] **Step 1: Write failing migration, replay, conflict, and concurrency tests**

```python
def test_feedback_claim_distinguishes_replay_conflict_and_limit(repository, ready_run) -> None:
    first = repository.claim_feedback_operation(
        ready_run.id, "a" * 64, "f" * 64,
        (RevisionChange.SHORTEN_BODY,), "d" * 64, ready_run.updated_at,
    )
    with pytest.raises(OperationInProgressError):
        repository.claim_feedback_operation(
            ready_run.id, "a" * 64, "f" * 64,
            (RevisionChange.SHORTEN_BODY,), "d" * 64, ready_run.updated_at,
        )
    with pytest.raises(IdempotencyConflictError):
        repository.claim_feedback_operation(
            ready_run.id, "a" * 64, "e" * 64,
            (RevisionChange.SHORTEN_HEADLINE,), "c" * 64, ready_run.updated_at,
        )
```

Add tests for: two threads with different keys yield one claimed feedback operation; successful exact replay returns identical stored public response; a second key after version 2 raises `RevisionLimitReachedError`; retry claim increments technical count once; retry replay does not increment; a failed transaction writes no revision and leaves counters unchanged.

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py -q
```

Expected: failures for absent tables, records, and claim/finalize methods.

- [ ] **Step 3: Add constrained tables and serializers**

Create tables in `initialize()`:

```sql
CREATE TABLE IF NOT EXISTS project_run_revisions (
  run_id TEXT PRIMARY KEY,
  result_version INTEGER NOT NULL CHECK(result_version = 2),
  requested_changes_json TEXT NOT NULL,
  feedback_digest TEXT NOT NULL,
  creative_brief_json TEXT NOT NULL,
  ad_copy_json TEXT NOT NULL,
  fact_references_json TEXT NOT NULL,
  rule_ids_json TEXT NOT NULL,
  composition_json TEXT NOT NULL,
  critique_json TEXT NOT NULL,
  revised_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_run_operations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  operation_kind TEXT NOT NULL CHECK(operation_kind IN ('feedback','retry')),
  idempotency_key_digest TEXT NOT NULL,
  request_fingerprint TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('in_progress','succeeded','failed_retryable','failed_final')),
  requested_changes_json TEXT,
  feedback_digest TEXT,
  retry_condition TEXT,
  retry_action TEXT,
  public_response_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(run_id, operation_kind, idempotency_key_digest)
);
```

Use `BEGIN IMMEDIATE` for every claim/finalize path. Digest format is lowercase 64-character hex. Canonical request fingerprints use sorted compact JSON with UUIDs/timestamps serialized deterministically. Never accept or store raw feedback/key in these methods.

- [ ] **Step 4: Implement exact CAS transitions**

Feedback claim changes `ready -> in_progress` only after checking no revision row and resolving same-key replay/conflict. Completion inserts the unique revision, updates `human_revision_count` from `0 -> 1`, sets terminal status, and stores the exact public response in one transaction. Retry claim requires the unfinished feedback operation to be `failed_retryable` with stored retry condition/action, inserts/claims the retry key, increments `technical_attempt_count` once, and moves `failed_retryable -> in_progress`.

- [ ] **Step 5: Run GREEN and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py -q
python -m ruff check src/cultureshift/repository.py tests/test_repository.py
```

- [ ] **Step 6: Commit**

```powershell
git add -- src/cultureshift/repository.py tests/test_repository.py
git commit -m "feat: persist one revision atomically"
```

---

### Task 5: Orchestrate feedback and safe retry with artifact cleanup

**Files:**

- Create: `src/cultureshift/revision_service.py`
- Create: `tests/test_revision_service.py`
- Modify: `src/cultureshift/composition_service.py` only if a narrow reusable compose helper is required by the tests.

**Interfaces:**

- Produces: `RevisionServiceErrorCode` values `INVALID_RUN_STATE`, `IDEMPOTENCY_CONFLICT`, `OPERATION_IN_PROGRESS`, `REVISION_LIMIT_REACHED`, `INVALID_REVISION_REQUEST`, `REVISION_FAILED`, `RETRY_FAILED`.
- Produces: `RevisionService.submit_feedback(request, idempotency_key, now=None) -> RevisionCompleted`.
- Produces: `RevisionService.retry(request, idempotency_key, now=None) -> RevisionCompleted`.
- Consumes: Task 3 engine; Task 4 operation/revision repository API; existing compositor, artifact store, Critic, and Day 14 `decide_retry` policy.

- [ ] **Step 1: Write failing service acceptance tests**

Cover both directions and assert immutable v1 plus one v2:

```python
@pytest.mark.parametrize("direction", tuple(LocalizationDirection))
def test_first_feedback_creates_exactly_one_preserving_revision(service_fixture, direction) -> None:
    service, repository, store, request = service_fixture(direction)
    original = repository.get_composition(request.run_id)
    result = service.submit_feedback(request, "safe_key_12345678")
    revised = repository.get_revision(request.run_id)

    assert result.result_version == 2
    assert result.human_revision_count == 1
    assert repository.get_composition(request.run_id) == original
    assert revised.composition.artifact_id != original.artifact_id
    assert revised.composition.width == original.width == 1600
    assert revised.composition.height == original.height == 900
    assert [layer.kind for layer in revised.composition.layers] == [
        layer.kind for layer in original.layers
    ]
```

Add tests for exact replay, same-key/different-body conflict, second-key revision limit, retryable injected composition persistence failure with no v2/human count, accepted retry success with technical count one, retry replay, exhausted/unsafe retry rejection, and artifact deletion when final DB persistence raises or loses a race.

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_revision_service.py -q
```

Expected: import failure because the service does not exist.

- [ ] **Step 3: Implement safe hashing and validation**

Validate `Idempotency-Key` against `^[A-Za-z0-9_-]{16,128}$`. Compute:

```python
key_digest = sha256(idempotency_key.encode("ascii")).hexdigest()
feedback_digest = sha256(request.feedback.encode("utf-8")).hexdigest()
fingerprint = sha256(canonical_public_request_json).hexdigest()
```

Do not place raw values into exceptions. Require a ready v1 composition and a non-reject v1 Critic before claiming feedback.

- [ ] **Step 4: Implement compose-review-finalize and retry resume**

After claim, load trusted v1 analysis/Brand Lock/draft, call `FixtureRevisionEngine`, render to a fresh UUID using the existing fixed compositor and protected asset IDs, save the artifact, and run `Critic` on revised inputs. Call `complete_revision` only after all artifacts validate. On any finalize conflict/failure, call `CompositionArtifactStore.delete(new_artifact_id)` before mapping the bounded error.

For retry, load the stored failed feedback operation and its structured changes; never accept new feedback. Call `decide_retry` using the stored server condition/attempts/call ID. Only `RETRY_ONCE` continues; all other actions fail closed. Do not create a visible version until the resumed finalize succeeds.

- [ ] **Step 5: Run GREEN and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_revision_service.py tests/test_revision.py tests/test_workflow.py -q
python -m ruff check src/cultureshift/revision_service.py src/cultureshift/composition_service.py tests/test_revision_service.py
```

- [ ] **Step 6: Commit**

```powershell
git add -- src/cultureshift/revision_service.py src/cultureshift/composition_service.py tests/test_revision_service.py
git commit -m "feat: orchestrate revision and retry"
```

---

### Task 6: Expose authenticated feedback/retry APIs and Person B state behavior

**Files:**

- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_app.py`
- Create: `apps/web/src/revision/revision-flow.ts`
- Create: `apps/web/src/revision/revision-flow.test.ts`

**Interfaces:**

- Produces: `POST /api/v1/runs/{run_id}/feedback` and `/retry`, both requiring exact update capability and `Idempotency-Key`.
- Produces: `RevisionFlowState` phases `idle`, `submitting`, `succeeded`, `conflict`, `retryable_failure`, `final_failure`.
- Produces: `selectRevisionChange`, `beginRevision`, `resolveRevision`, and `failRevision` pure functions.

- [ ] **Step 1: Write failing HTTP tests**

Test missing/malformed/wrong-subject capability; missing/invalid idempotency key; body/path mismatch; bilateral success; exact replay; the three distinct 409 codes; 422 unsupported changes; retryable and final service errors; and a public-boundary assertion that serialized responses/errors contain no feedback, idempotency key, token, local path, or exception text.

```python
def test_feedback_requires_path_body_match_and_exact_update_capability(client, ready_run) -> None:
    response = client.post(
        f"/api/v1/runs/{ready_run.id}/feedback",
        headers={"Authorization": f"Bearer {ready_run.update_token}",
                 "Idempotency-Key": "revision_key_1234"},
        json={**feedback_payload(ready_run.id), "run_id": str(uuid4())},
    )
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "invalid_run_state"}}
```

- [ ] **Step 2: Run HTTP RED**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_app.py -q
```

Expected: route-not-found failures.

- [ ] **Step 3: Wire the service and bounded error mapping**

Add an injectable `revision_service` to `create_app`. Reuse the existing exact update-capability verification pattern. Map service codes exactly:

```python
status_by_code = {
    "invalid_run_state": 409,
    "idempotency_conflict": 409,
    "operation_in_progress": 409,
    "revision_limit_reached": 409,
    "invalid_revision_request": 422,
    "revision_failed": 500,
    "retry_failed": 500,
}
```

Never pass exception strings into `HTTPException.detail`.

- [ ] **Step 4: Write failing Person B state tests**

```typescript
it("keeps conflicts distinct and never appends version three", () => {
  const selected = selectRevisionChange(idleRevisionState(), "shorten_body");
  expect(canSubmitRevision(selected)).toBe(true);
  const succeeded = resolveRevision(beginRevision(selected), revisionFixture);
  const replayed = resolveRevision(succeeded, revisionFixture);
  expect(replayed.visibleVersions).toEqual([1, 2]);
  expect(failRevision(beginRevision(selected), "revision_limit_reached").conflictCode)
    .toBe("revision_limit_reached");
  expect(failRevision(beginRevision(selected), "operation_in_progress").conflictCode)
    .toBe("operation_in_progress");
});
```

Add tests that selection deduplicates and caps at two; empty/active submission is disabled; retryable technical failure enables retry; culture/safety/final failure does not.

- [ ] **Step 5: Run TypeScript RED**

```powershell
npm.cmd --prefix apps/web test -- src/revision/revision-flow.test.ts
```

Expected: module-not-found failure.

- [ ] **Step 6: Implement the pure discriminated union**

Use a discriminated union with exact phase literals. Store only generated contract values, `selectedChanges`, `visibleVersions: readonly [1] | readonly [1, 2]`, optional bounded `conflictCode`, and `canRetry`; add no fetch, React, route, browser storage, or free-text execution.

- [ ] **Step 7: Run GREEN, typecheck, and lint**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_app.py -q
python -m ruff check src/cultureshift/app.py tests/test_app.py
npm.cmd --prefix apps/web test -- src/revision/revision-flow.test.ts
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
```

- [ ] **Step 8: Commit**

```powershell
git add -- src/cultureshift/app.py tests/test_app.py apps/web/src/revision
git commit -m "feat: expose revision flow"
```

---

### Task 7: Run bilateral release gates, document Day 15, and publish safely

**Files:**

- Modify if required by test evidence only: Day 15 files from Tasks 1-6.
- Create outside Git: `D:\create\Diversity\Day15.docx`
- Do not create committed test logs, screenshots, rendered pages, SQLite files, or upload staging directories.

**Interfaces:**

- Consumes: all Tasks 1-6.
- Produces: verified Day 15 tree, visually checked private record, non-force remote `main`, and successful GitHub Actions evidence.

- [ ] **Step 1: Add and run the bilateral public-HTTP journey**

For both localization directions, use only public endpoints to progress v1 Critic -> feedback -> v2 Critic, then assert another feedback key is rejected and retry replay cannot create a third version. Keep this in `tests/test_app.py` and run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_app.py -q
```

- [ ] **Step 2: Run the complete local release gate**

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
python -m ruff check .
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run build
git diff --check
```

Expected: every command exits 0. If any fails, invoke `superpowers:systematic-debugging`, add a reproducing test, and repair only Day 15 scope before rerunning the whole gate.

- [ ] **Step 3: Scan the public boundary and repository hygiene**

```powershell
rg -n -i "feedback.*(log|print)|idempotency.*(log|print)|Bearer |CULTURESHIFT_CAPABILITY_SECRET|[A-Z]:\\\\" src tests apps/web
git status --short
git diff --check
```

Expected: no raw feedback/key/token/private path in production logs or public payloads; only intentional secret-name configuration/test fixtures appear; no temporary Day 15 directories are tracked.

- [ ] **Step 4: Create and visually verify `Day15.docx`**

Invoke the `documents:documents` skill, copy the Day 14 document's section order and styling, and record: Issue #14, approved scope, Person A/Person B outputs, commit SHAs, exact gate commands/results, bilateral journey evidence, limitations, and remote publication evidence. Render every page with `render_docx.py`, inspect the PNGs, correct clipping/overflow, and keep only the final DOCX in `D:\create\Diversity`.

- [ ] **Step 5: Commit the final repository-only evidence**

```powershell
git add -- docs/superpowers/specs/2026-08-25-day15-revision-retry-design.md docs/superpowers/plans/2026-08-25-day15-revision-retry.md src tests contracts apps/web
git diff --cached --check
git commit -m "feat: complete Day 15 revision flow"
```

- [ ] **Step 6: Verify partner state before publishing**

Test `github.com:443` and `api.github.com:443`, fetch `origin/main`, and compare the fetched remote commit/tree to the recorded Day 14 baseline. If the partner moved `main`, stop and reconcile without force. If normal Git transport works, use `git push origin HEAD:main`; if the connection resets, immediately use the previously verified GitHub Git Data API path with the same expected-old-SHA guard. Never use force push or repeat browser uploads.

- [ ] **Step 7: Verify remote tree and Actions**

Confirm remote `main` points to the local commit and has the same tree SHA. Wait for the workflow created by that commit, then verify every required job succeeds. A queued or running workflow is not completion evidence.

- [ ] **Step 8: Clean temporary Day 15 artifacts**

List only explicitly named `.day15-*` test/render/API-upload directories under `D:\create\Diversity`; verify each resolved path remains inside that folder and is not the repo/worktree, then remove those temporary directories. Preserve `Day15.docx`, the repo, the worktree, partner files, and all unrelated user files.
