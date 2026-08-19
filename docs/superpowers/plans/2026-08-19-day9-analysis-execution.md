# Day 9 Analysis Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a fixture-only authenticated analysis endpoint that reaches `awaiting_brand_lock` with one schema-repair attempt, plus a non-interactive Brand Lock UX preparation surface.

**Architecture:** Extend the existing closed contracts and Day 8 pipeline, keep image bytes only in the temporary asset store and in-memory call path, and persist only validated request/result JSON beside run state. The Next.js result page consumes a typed immutable field specification and renders all Day 10 controls as read-only or disabled.

**Tech Stack:** Python 3.11+; FastAPI; Pydantic v2; SQLite; pytest; Next.js 16.3; React 19; TypeScript; Vitest; Testing Library.

**Spec:** `docs/superpowers/specs/2026-08-19-day9-analysis-execution-design.md`

## Global Constraints

- Execution remains `fixture` only; no provider SDK, credential, live call, or new dependency.
- Only China-to-UK and UK-to-China static AI software/application ads are supported.
- Provider-controlled cultural claims remain pending hypotheses requiring human review.
- Never persist or emit image bytes, local paths, capability tokens, raw provider output, prompts, or provider exceptions.
- Repair is attempted exactly once and only after schema-invalid provider output.
- Editing and Brand Lock confirmation remain unavailable until Day 10.

---

### Task 1: Contracts, run state, and one-repair pipeline

**Files:**
- Modify: `src/cultureshift/contracts.py`
- Modify: `src/cultureshift/domain.py`
- Modify: `src/cultureshift/analysis_provider.py`
- Modify: `src/cultureshift/analysis_pipeline.py`
- Modify: `tests/test_contracts.py`
- Modify: `tests/test_domain.py`
- Modify: `tests/test_analysis_provider.py`
- Modify: `tests/test_analysis_pipeline.py`

**Interfaces:**
- Produces: `RunStatus.AWAITING_BRAND_LOCK`, `ProjectRunStatus.AWAITING_BRAND_LOCK`.
- Produces: `AnalysisCompleted(run_id, status, analysis, repair_attempted, completed_at)`.
- Produces: `AnalysisOutcome(analysis: AdAnalysis, repair_attempted: bool)`.
- Produces: `VisionProvider.analyze(request, *, attempt: Literal["initial", "repair"] = "initial")`.
- Produces: `FakeProvider(result, *, repair_result=None)` with `attempts` and `call_count` observations.

- [ ] **Step 1: Write failing contract and transition tests**

```python
def test_analysis_completed_requires_awaiting_brand_lock(valid_analysis) -> None:
    completed = AnalysisCompleted(
        run_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        status="awaiting_brand_lock",
        analysis=valid_analysis,
        repair_attempted=False,
        completed_at=datetime(2026, 8, 19, tzinfo=UTC),
    )
    assert completed.status is RunStatus.AWAITING_BRAND_LOCK


def test_run_can_reach_awaiting_brand_lock_only_from_in_progress() -> None:
    active = ProjectRun(direction="china_to_uk").with_status("in_progress")
    assert active.with_status("awaiting_brand_lock").status == "awaiting_brand_lock"
    with pytest.raises(ValueError):
        ProjectRun(direction="china_to_uk").with_status("awaiting_brand_lock")
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m pytest tests/test_contracts.py tests/test_domain.py -q`
Expected: collection or validation failure because `awaiting_brand_lock` and `AnalysisCompleted` do not exist.

- [ ] **Step 3: Add the minimal statuses, transition rules, and closed response contract**

```python
class AnalysisCompleted(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.AWAITING_BRAND_LOCK]
    analysis: AdAnalysis
    repair_attempted: bool
    completed_at: UtcDatetime
```

- [ ] **Step 4: Run the contract/transition tests and verify GREEN**

Run: `python -m pytest tests/test_contracts.py tests/test_domain.py -q`
Expected: all selected tests pass.

- [ ] **Step 5: Write failing repair tests**

```python
def test_schema_invalid_output_is_repaired_once(request, valid_result) -> None:
    provider = FakeProvider({"unexpected": True}, repair_result=valid_result)
    outcome = AnalysisPipeline(provider).analyze(request)
    assert outcome.repair_attempted is True
    assert provider.attempts == ("initial", "repair")


def test_safety_failure_is_not_repaired(request, unsafe_result) -> None:
    provider = FakeProvider(unsafe_result, repair_result=unsafe_result)
    with pytest.raises(AnalysisPipelineError):
        AnalysisPipeline(provider).analyze(request)
    assert provider.attempts == ("initial",)
```

- [ ] **Step 6: Run repair tests and verify RED**

Run: `python -m pytest tests/test_analysis_provider.py tests/test_analysis_pipeline.py -q`
Expected: failure because attempt selection, repair result, and `AnalysisOutcome` are absent.

- [ ] **Step 7: Implement one schema-only repair and preserve all safety checks**

```python
@dataclass(frozen=True, slots=True)
class AnalysisOutcome:
    analysis: AdAnalysis
    repair_attempted: bool

# Initial schema validation failure calls provider once with attempt="repair".
# Repair validation failure raises PROVIDER_OUTPUT_INVALID; safety failures never repair.
```

- [ ] **Step 8: Run focused pipeline tests and verify GREEN**

Run: `python -m pytest tests/test_analysis_provider.py tests/test_analysis_pipeline.py -q`
Expected: all selected tests pass with exactly one initial call and at most one repair call.

- [ ] **Step 9: Commit Task 1**

```bash
git add src/cultureshift/contracts.py src/cultureshift/domain.py src/cultureshift/analysis_provider.py src/cultureshift/analysis_pipeline.py tests/test_contracts.py tests/test_domain.py tests/test_analysis_provider.py tests/test_analysis_pipeline.py
git commit -m "feat: define Day 9 analysis state and repair"
```

### Task 2: Safe run context and temporary asset reads

**Files:**
- Modify: `src/cultureshift/asset_storage.py`
- Modify: `src/cultureshift/repository.py`
- Modify: `tests/test_asset_storage.py`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: `RunCreate`, `AdAnalysis`, `ProjectRunStatus.AWAITING_BRAND_LOCK`.
- Produces: `LoadedAsset(asset: SourceAdAssetRef, content: bytes)`.
- Produces: `TemporaryAssetStore.load(asset_id: UUID, *, now: datetime | None = None) -> LoadedAsset`.
- Produces: repository `create(run, request=None)`, `get_request`, `get_analysis`, `complete_analysis`, and `record_failure`.

- [ ] **Step 1: Write failing asset retrieval tests**

```python
def test_load_verifies_public_metadata_and_bytes(tmp_path) -> None:
    store = TemporaryAssetStore(tmp_path)
    stored = store.store(PNG, declared_media_type="image/png", provenance_ref="fixture:x", rights_ref="rights:x")
    loaded = store.load(stored.asset.asset_id, now=stored.created_at)
    assert loaded.asset == stored.asset
    assert loaded.content == PNG


def test_load_rejects_corrupt_or_closed_asset_without_path_echo(tmp_path) -> None:
    # Corrupt the private file and separately tombstone an asset.
    # Assert AssetStorageError/AssetLifecycleClosedError messages contain no path or bytes.
```

- [ ] **Step 2: Run asset tests and verify RED**

Run: `python -m pytest tests/test_asset_storage.py -q`
Expected: `TemporaryAssetStore.load` is missing.

- [ ] **Step 3: Implement bounded UUID lookup, metadata validation, signature/size/hash checks, and sanitized errors**

```python
@dataclass(frozen=True, slots=True)
class LoadedAsset:
    asset: SourceAdAssetRef
    content: bytes
```

- [ ] **Step 4: Run asset tests and verify GREEN**

Run: `python -m pytest tests/test_asset_storage.py -q`
Expected: valid reads pass; missing, expired, closed, and corrupt assets fail closed.

- [ ] **Step 5: Write failing repository round-trip and atomic completion tests**

```python
def test_repository_binds_request_and_validated_analysis(tmp_path, request, analysis) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run = repository.create(ProjectRun(direction=request.direction), request=request)
    repository.update_status(run.id, ProjectRunStatus.IN_PROGRESS)
    completed = repository.complete_analysis(run.id, analysis)
    assert completed.status is ProjectRunStatus.AWAITING_BRAND_LOCK
    assert repository.get_request(run.id) == request
    assert repository.get_analysis(run.id) == analysis
```

- [ ] **Step 6: Run repository tests and verify RED**

Run: `python -m pytest tests/test_repository.py -q`
Expected: request/result repository methods are missing.

- [ ] **Step 7: Add the companion table and atomic validated-result completion**

```sql
CREATE TABLE IF NOT EXISTS project_run_contexts (
  run_id TEXT PRIMARY KEY,
  request_json TEXT NOT NULL,
  analysis_json TEXT
)
```

Only `model_dump_json()` from validated contracts may enter this table.

- [ ] **Step 8: Run storage/repository tests and verify GREEN**

Run: `python -m pytest tests/test_asset_storage.py tests/test_repository.py -q`
Expected: all selected tests pass and persisted JSON contains no token, bytes, or path field.

- [ ] **Step 9: Commit Task 2**

```bash
git add src/cultureshift/asset_storage.py src/cultureshift/repository.py tests/test_asset_storage.py tests/test_repository.py
git commit -m "feat: bind Day 9 runs to safe analysis context"
```

### Task 3: Authenticated `/analyze` endpoint

**Files:**
- Modify: `src/cultureshift/capability_tokens.py`
- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_capability_tokens.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: Task 1 `AnalysisOutcome` and Task 2 run/asset methods.
- Produces: `Capability.ANALYZE_PROJECT_RUN`.
- Produces: `create_app(..., analysis_provider: VisionProvider | None = None)`.
- Produces: `POST /api/v1/runs/{run_id}/analyze -> AnalysisCompleted`.

- [ ] **Step 1: Write failing API success, idempotence, and authorization tests**

```python
def test_analyze_moves_fixture_run_to_awaiting_brand_lock(client, uploaded_run) -> None:
    run_id, token = uploaded_run
    response = client.post(
        f"/api/v1/runs/{run_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_brand_lock"
    assert response.json()["analysis"]["hypotheses"][0]["review_status"] == "pending"


def test_analyze_rejects_read_only_or_wrong_subject_capability(client, uploaded_run) -> None:
    # Assert 401/403 stable codes and absence of submitted bytes, token, and local path.
```

- [ ] **Step 2: Run API tests and verify RED**

Run: `python -m pytest tests/test_capability_tokens.py tests/test_app.py -q`
Expected: analyze capability and route are absent.

- [ ] **Step 3: Add analyze capability, fixture provider injection, run-request persistence, and endpoint orchestration**

```python
@application.post(
    "/api/v1/runs/{run_id}/analyze",
    response_model=AnalysisCompleted,
    tags=["runs"],
)
def analyze_run(run_id: UUID, request: Request) -> AnalysisCompleted:
    # verify subject/capability, handle idempotent success, transition,
    # load bound asset, execute pipeline, atomically complete, sanitize failures
```

- [ ] **Step 4: Add failing failure-mapping tests before each minimal branch**

Cover one literal expected response per failure class:

```python
assert response.json() == {"detail": {"code": "provider_output_invalid"}}
assert snapshot["status"] == "failed"
```

Also cover blocked lifecycle/safety failures, asset mismatch, bilateral success,
one repair, exhausted repair, and no echo of bytes/path/provider exception.

- [ ] **Step 5: Implement only the tested status/error mappings and verify GREEN**

Run: `python -m pytest tests/test_capability_tokens.py tests/test_app.py -q`
Expected: all selected tests pass; retry after success does not increment provider calls.

- [ ] **Step 6: Regenerate and check public contracts**

Run: `python scripts/export_contracts.py`
Run: `npm --prefix apps/web run contracts:generate`
Run: `python scripts/export_contracts.py --check`
Run: `npm --prefix apps/web run contracts:check`
Expected: both freshness checks report current output.

- [ ] **Step 7: Commit Task 3**

```bash
git add src/cultureshift/capability_tokens.py src/cultureshift/app.py tests/test_capability_tokens.py tests/test_app.py contracts/json-schema/cultureshift.contracts.schema.json apps/web/src/generated/contracts.ts
git commit -m "feat: execute fixture analysis through API"
```

### Task 4: Person B Brand Lock UX preparation

**Files:**
- Create: `apps/web/src/brand-lock/brand-lock-form-spec.ts`
- Create: `apps/web/src/components/brand-lock-preparation.tsx`
- Create: `apps/web/src/components/brand-lock-preparation.module.css`
- Create: `apps/web/src/components/brand-lock-preparation.test.tsx`
- Modify: `apps/web/src/app/results/[fixtureId]/page.tsx`
- Modify: `apps/web/src/app/results/[fixtureId]/page.test.tsx`

**Interfaces:**
- Consumes: generated `BrandLock` and the existing bilateral `FixtureBundle`.
- Produces: immutable `BRAND_LOCK_FORM_SPEC` with all `keyof BrandLock` fields.
- Produces: `BrandLockPreparation({ fixture })` server-compatible component.

- [ ] **Step 1: Write failing specification and component tests**

```tsx
expect(BRAND_LOCK_FORM_SPEC.map((field) => field.key)).toEqual([
  "logo_asset_id", "product_name", "verified_product_facts",
  "product_ui_asset_ids", "benefit_order", "cta_action_meaning",
  "layout_template_asset_id", "localizable_fields",
]);

expect(screen.getByText("awaiting_brand_lock")).toBeInTheDocument();
expect(screen.getByRole("button", { name: "Confirm Brand Lock — available Day 10" })).toBeDisabled();
expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
```

- [ ] **Step 2: Run focused web tests and verify RED**

Run: `npm --prefix apps/web test -- brand-lock-preparation.test.tsx page.test.tsx`
Expected: imports/components are missing.

- [ ] **Step 3: Implement typed field data and semantic read-only rendering**

```ts
export interface BrandLockFieldSpec {
  key: keyof BrandLock;
  label: string;
  help: string;
  control: "asset_preview" | "text" | "ordered_text" | "ordered_assets" | "reorder" | "multi_select";
  preview: boolean;
}
```

Render descriptions and previews with headings/lists; render only a native
disabled confirmation button, no `<form>`, client state, or event handler.

- [ ] **Step 4: Add the component to both static result routes and verify GREEN**

Run: `npm --prefix apps/web test -- brand-lock-preparation.test.tsx page.test.tsx`
Expected: both directions show all eight groups, preview context, pending-human-review copy, and disabled confirmation.

- [ ] **Step 5: Run TypeScript and accessibility-oriented focused checks**

Run: `npm --prefix apps/web run typecheck`
Expected: generated Brand Lock keys and component props typecheck without casts that bypass the contract.

- [ ] **Step 6: Commit Task 4**

```bash
git add apps/web/src/brand-lock apps/web/src/components/brand-lock-preparation.tsx apps/web/src/components/brand-lock-preparation.module.css apps/web/src/components/brand-lock-preparation.test.tsx apps/web/src/app/results/[fixtureId]/page.tsx apps/web/src/app/results/[fixtureId]/page.test.tsx
git commit -m "feat: prepare Day 9 Brand Lock review UX"
```

### Task 5: Full verification and evidence record

**Files:**
- Create locally outside Git: `D:\create\Diversity\Day9.docx`
- Modify only if a real gate exposes a regression: the failing production file and its focused regression test.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: clean commits, verified DOCX, remote-main publication, and green CI.

- [ ] **Step 1: Run one complete local gate**

```text
python -m pytest -q
python -m ruff check .
python scripts/export_contracts.py --check
npm --prefix apps/web run contracts:check
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
NEXT_TELEMETRY_DISABLED=1 npm --prefix apps/web run build
npm --prefix apps/web audit --audit-level=high
pwsh ./scripts/verify-public-boundary.ps1
git diff --check
```

Expected: every command exits 0; only the already known Starlette deprecation warning may remain.

- [ ] **Step 2: Create and visually/structurally verify `Day9.docx`**

Record the approved scope, Issue #8, RED/GREEN evidence, commits, gate counts,
remote commit, CI URL, limitations, and Day 10 handoff. Match the established
Day 8 document style and keep the file only in `D:\create\Diversity`.

- [ ] **Step 3: Check remote `main` before publication**

First test `github.com` and `api.github.com`. Read remote `main` and compare its
commit/tree with the verified Day 8 base. Stop if a partner commit appeared.

- [ ] **Step 4: Publish using the proven route**

Use normal `git push` when GitHub transport works. On network reset, immediately
use the existing Git Credential-backed GitHub API tree/commit/ref workflow with
non-forced compare-and-swap against the freshly read remote SHA.

- [ ] **Step 5: Verify remote state and CI**

Confirm the remote commit tree exactly equals the local Day 9 tree, wait for the
corresponding GitHub Actions run, and record its final conclusion in
`Day9.docx`. Do not claim completion until the run is green.
