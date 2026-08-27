# Day 16 Connected Fixture Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect one fixture-only Next.js Studio to the complete Day 15 FastAPI workflow for both localization directions, including one revision, versioned export, and explicit source deletion.

**Architecture:** The browser uses one typed `StudioApiClient` to call FastAPI directly and holds all capabilities in React memory. A pure Studio state machine controls legal transitions while a single `/studio` client surface composes the existing fixture, Brand Lock, evidence, and revision primitives. FastAPI receives only strict local CORS configuration and version-aware composition export; no new authentication or persistence subsystem is introduced.

**Tech Stack:** Python 3.14, FastAPI, Pydantic v2, SQLite, Pillow, pytest, Ruff, TypeScript 5, React 19, Next.js 16, Vitest, Testing Library, ESLint.

**Spec:** `docs/superpowers/specs/2026-08-27-day16-studio-integration-design.md`

## Global Constraints

- Work only against GitHub Issue #15 and the verified Day 15 tree `34d72510396a2dad540b5e7dc1df105d92dee011`.
- Keep the product fixture-only, bilateral, static-ad-only, and limited to the existing authorized Orbit AI assets.
- Keep Run and asset-delete capabilities in React memory only; never persist, log, render, or place them in URLs.
- Preserve Brand Lock, verified facts, benefit order, CTA meaning, protected logo/UI IDs, layout template, rule IDs, 1600 x 900 output, and `Fixture Demo / 非实时模型` disclosure.
- Treat raw files, metadata, response bodies, and feedback as untrusted data; free-form feedback is context and never executable instruction.
- Permit only explicit local CORS origins; no wildcard, credentialed CORS, or arbitrary origin reflection.
- Allow exactly one human revision and no visible version 3; technical retry resumes only a stored server-authorized operation.
- Delete only the uploaded source asset addressed by the exact delete capability; do not claim Run or generated-record deletion.
- No live provider, account/session service, browser persistence, queue, polling, websocket, analytics, deployment, cultural approval, or Day 17 browser E2E.
- Use a failing test before every production behavior and make focused commits after each independently reviewable task.
- Use one explicitly named writable pytest base temp and remove it with every other Day 16 temporary artifact before delivery.

## File structure

- Modify `src/cultureshift/composition_export.py`: select and integrity-check immutable composition version 1 or 2.
- Modify `src/cultureshift/app.py`: strict CORS configuration and bounded export version query.
- Modify `tests/test_composition_export.py`: version resolution and integrity evidence.
- Modify `tests/test_app.py`: CORS, query validation, capability isolation, and HTTP export evidence.
- Create `apps/web/src/studio/studio-api.ts`: typed JSON/binary HTTP boundary and sanitized error mapping.
- Create `apps/web/src/studio/studio-api.test.ts`: exact request and token non-disclosure tests.
- Create `apps/web/src/studio/studio-state.ts`: pure legal Studio transitions and action guards.
- Create `apps/web/src/studio/studio-state.test.ts`: bilateral state and failure-transition tests.
- Create `apps/web/src/app/studio/studio-client.tsx`: connected fixture-only Studio presentation and orchestration.
- Create `apps/web/src/app/studio/studio-client.test.tsx`: accessible connected-flow component tests.
- Create `apps/web/src/app/studio/page.tsx`: route wrapper.
- Create `apps/web/src/app/studio/studio.module.css`: route-scoped visual hierarchy.
- Modify `apps/web/src/app/page.tsx`: visible link to the connected Studio.
- Modify `apps/web/src/app/page.test.tsx`: Studio-link navigation evidence.
- Create outside Git: `../Day16.docx`: private delivery record using the Day 15 format.

---

### Task 1: Add strict local CORS and version-aware export (Person A)

**Files:**

- Modify: `src/cultureshift/composition_export.py`
- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_composition_export.py`
- Modify: `tests/test_app.py`

**Interfaces:**

- Produces: `CompositionExportService.export_png(run_id, result_version=1) -> ExportedComposition`.
- Produces: `CompositionExportService.export_json(run_id, result_version=1) -> bytes`.
- Produces: `GET /api/v1/runs/{run_id}/composition.png?result_version=1|2` and the matching JSON endpoint; omission selects version 1.
- Produces: `_cors_origins_from_environment() -> tuple[str, ...]` with exact-origin validation.
- Consumes: `SQLiteProjectRunRepository.get_composition(run_id)` for version 1 and `get_revision(run_id).composition` for version 2.

- [ ] **Step 1: Write failing service tests for immutable version selection**

Extend the test repository double so it exposes both summaries and add these exact expectations:

```python
class SummaryRepository:
    def __init__(self, initial, revision=None, *, run_exists=True):
        self._initial = initial
        self._revision = revision
        self._run_exists = run_exists

    def get_composition(self, run_id: UUID):
        if not self._run_exists:
            raise ProjectRunNotFoundError(str(run_id))
        return self._initial

    def get_revision(self, run_id: UUID):
        if not self._run_exists:
            raise ProjectRunNotFoundError(str(run_id))
        return self._revision


def test_export_service_selects_version_one_and_two(tmp_path) -> None:
    service, initial, revised = versioned_export_fixture(tmp_path)
    assert json.loads(service.export_json(initial.run_id, 1))["artifact_id"] == str(
        initial.artifact_id
    )
    assert json.loads(service.export_json(initial.run_id, 2))["artifact_id"] == str(
        revised.artifact_id
    )


def test_export_service_rejects_absent_or_unknown_version(tmp_path) -> None:
    service, initial, _ = versioned_export_fixture(tmp_path, include_revision=False)
    with pytest.raises(CompositionExportError) as missing:
        service.export_png(initial.run_id, 2)
    assert missing.value.code is CompositionExportErrorCode.COMPOSITION_UNAVAILABLE
    with pytest.raises(ValueError):
        service.export_json(initial.run_id, 3)
```

- [ ] **Step 2: Run service RED**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_composition_export.py -q --basetemp .day16-pytest
```

Expected: version-argument failures because the service accepts only `run_id`.

- [ ] **Step 3: Implement the minimal version resolver**

Use a literal public boundary and keep artifact verification shared:

```python
from typing import Literal

ResultVersionNumber = Literal[1, 2]

def _summary(
    self, run_id: UUID, result_version: ResultVersionNumber
) -> CompositionGenerated:
    if result_version == 1:
        summary = self._repository.get_composition(run_id)
    elif result_version == 2:
        revision = self._repository.get_revision(run_id)
        summary = None if revision is None else revision.composition
    else:
        raise ValueError("unsupported result version")
    if summary is None:
        raise CompositionExportError(
            CompositionExportErrorCode.COMPOSITION_UNAVAILABLE
        )
    return summary
```

Pass `result_version` through `export_png` and `export_json`; do not duplicate load/hash/dimension checks.

- [ ] **Step 4: Run service GREEN and Ruff**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_composition_export.py -q --basetemp .day16-pytest
python -m ruff check src/cultureshift/composition_export.py tests/test_composition_export.py
```

- [ ] **Step 5: Write failing HTTP tests for CORS and version queries**

Add tests that assert:

```python
def test_local_studio_cors_is_exact_and_noncredentialed(client) -> None:
    allowed = client.options(
        "/api/v1/assets",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-provenance-ref,x-rights-ref",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert allowed.headers.get("access-control-allow-credentials") != "true"

    denied = client.options(
        "/api/v1/assets",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in denied.headers


@pytest.mark.parametrize("suffix", ["composition.png", "composition.json"])
def test_export_selects_persisted_revision_by_query(client, ready_revised_run, suffix):
    response = client.get(
        f"/api/v1/runs/{ready_revised_run.id}/{suffix}?result_version=2",
        headers={"Authorization": f"Bearer {ready_revised_run.read_token}"},
    )
    assert response.status_code == 200
    if suffix.endswith("json"):
        assert response.json()["artifact_id"] == str(
            ready_revised_run.revised_artifact_id
        )
    else:
        assert response.content == ready_revised_run.revised_png
```

Also assert default version 1 remains byte-for-byte compatible, `result_version=3` returns 422 without echo, missing version 2 returns the bounded composition error, and wrong-subject capability remains 403.

- [ ] **Step 6: Run HTTP RED**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_app.py -q --basetemp .day16-pytest
```

Expected: missing CORS headers and query arguments ignored or rejected by the current endpoints.

- [ ] **Step 7: Add strict CORS parsing and bounded query wiring**

Implement:

```python
DEFAULT_STUDIO_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

def _cors_origins_from_environment() -> tuple[str, ...]:
    configured = os.environ.get("CULTURESHIFT_STUDIO_ORIGINS", "")
    origins = tuple(value.strip() for value in configured.split(",") if value.strip())
    selected = origins or DEFAULT_STUDIO_ORIGINS
    if any(origin == "*" or not origin.startswith(("http://", "https://")) for origin in selected):
        raise RuntimeError("CULTURESHIFT_STUDIO_ORIGINS must contain exact origins")
    return selected
```

Add `CORSMiddleware` with `allow_credentials=False`, exact methods, and exact headers. Type each endpoint query as `Literal[1, 2] = 1`, pass it to the service, and keep current error mapping.

- [ ] **Step 8: Run HTTP GREEN, focused regression, and Ruff**

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_app.py tests/test_composition_export.py -q --basetemp .day16-pytest
python -m ruff check src/cultureshift/app.py src/cultureshift/composition_export.py tests/test_app.py tests/test_composition_export.py
```

- [ ] **Step 9: Commit**

```powershell
git add -- src/cultureshift/app.py src/cultureshift/composition_export.py tests/test_app.py tests/test_composition_export.py
git commit -m "feat: expose versioned Studio exports"
```

---

### Task 2: Build the token-safe typed Studio API client (Person A)

**Files:**

- Create: `apps/web/src/studio/studio-api.ts`
- Create: `apps/web/src/studio/studio-api.test.ts`

**Interfaces:**

- Produces: `StudioApiClient` methods `uploadAsset`, `createRun`, `analyzeRun`, `confirmBrandLock`, `generateDraft`, `generateComposition`, `runCritic`, `submitFeedback`, `retryRevision`, `exportComposition`, and `deleteAsset`.
- Produces: `StudioApiError` with only `status: number` and bounded `code: StudioErrorCode`.
- Produces: `createStudioApiClient(baseUrl?, fetchImpl?) -> StudioApiClient`.
- Consumes: generated contracts from `apps/web/src/generated/contracts.ts` and the versioned endpoints from Task 1.

- [ ] **Step 1: Write failing request-shape and sanitization tests**

Use a recording `fetch` double and assert exact public calls:

```typescript
it("uploads raw bytes with public metadata and never puts capabilities in URLs", async () => {
  const fetchMock = vi.fn().mockResolvedValue(jsonResponse(assetUploaded));
  const api = createStudioApiClient("http://127.0.0.1:8000", fetchMock);
  await api.uploadAsset(file, {
    provenanceRef: "fixture://day16/source",
    rightsRef: "rights://authorized/day16",
  });

  expect(fetchMock).toHaveBeenCalledWith(
    "http://127.0.0.1:8000/api/v1/assets",
    expect.objectContaining({
      method: "POST",
      body: file,
      headers: expect.objectContaining({
        "Content-Type": "image/png",
        "X-Provenance-Ref": "fixture://day16/source",
        "X-Rights-Ref": "rights://authorized/day16",
      }),
    }),
  );
  expect(fetchMock.mock.calls[0][0]).not.toContain("capability");
});

it("sanitizes malformed and private server failures", async () => {
  const api = createStudioApiClient(
    undefined,
    vi.fn().mockResolvedValue(new Response("private traceback", { status: 500 })),
  );
  const error = await api.analyzeRun(runId, "secret-token").catch((value) => value);
  expect(error).toEqual(
    expect.objectContaining({ status: 500, code: "service_unavailable" }),
  );
  expect(String(error)).not.toMatch(/private traceback|secret-token/);
});
```

Add exact tests for Bearer headers, bodyless draft/composition/Critic calls, feedback/retry `Idempotency-Key`, `result_version` query selection, binary media validation, and delete using only the asset token.

- [ ] **Step 2: Run API-client RED**

```powershell
npm.cmd --prefix apps/web test -- src/studio/studio-api.test.ts
```

Expected: module-not-found failure.

- [ ] **Step 3: Implement one JSON/binary request boundary**

Define exact public types and central helpers:

```typescript
export type StudioErrorCode =
  | "asset_empty"
  | "unsupported_asset_type"
  | "asset_type_mismatch"
  | "asset_too_large"
  | "invalid_asset_metadata"
  | "upload_rate_limited"
  | "asset_lifecycle_closed"
  | "invalid_capability"
  | "capability_subject_mismatch"
  | "run_not_found"
  | "invalid_run_state"
  | "brand_lock_immutable"
  | "brand_lock_unconfirmed"
  | "locked_field_changed"
  | "benefit_order_invalid"
  | "localizable_fields_invalid"
  | "invalid_analysis_input"
  | "unsupported_analysis_scope"
  | "provider_failed"
  | "provider_output_invalid"
  | "instruction_like_content"
  | "prohibited_content"
  | "unsafe_hypothesis"
  | "draft_output_invalid"
  | "composition_output_invalid"
  | "critic_failed"
  | "operation_in_progress"
  | "idempotency_conflict"
  | "revision_limit_reached"
  | "invalid_revision_request"
  | "revision_failed"
  | "retry_failed"
  | "composition_unavailable"
  | "composition_artifact_unavailable"
  | "service_unavailable";

export class StudioApiError extends Error {
  constructor(readonly status: number, readonly code: StudioErrorCode) {
    super("Studio request failed");
    this.name = "StudioApiError";
  }
}

export interface StudioApiClient {
  uploadAsset(file: File, metadata: UploadMetadata): Promise<AssetUploaded>;
  createRun(request: RunCreate): Promise<RunCreated>;
  analyzeRun(runId: string, token: string): Promise<AnalysisCompleted>;
  confirmBrandLock(runId: string, token: string, brandLock: BrandLock): Promise<BrandLockConfirmed>;
  generateDraft(runId: string, token: string): Promise<DraftGenerated>;
  generateComposition(runId: string, token: string): Promise<CompositionGenerated>;
  runCritic(runId: string, token: string): Promise<CritiqueCompleted>;
  submitFeedback(runId: string, token: string, request: FeedbackRequest, key: string): Promise<RevisionCompleted>;
  retryRevision(runId: string, token: string, request: RetryRequest, key: string): Promise<RevisionCompleted>;
  exportComposition(runId: string, token: string, version: 1 | 2, format: "png" | "json"): Promise<Blob>;
  deleteAsset(assetId: string, token: string): Promise<void>;
}
```

Decode only `detail.code` from an error JSON object. Treat every other body as `service_unavailable`; never include body text, token, feedback, file name, or request metadata in errors.

- [ ] **Step 4: Run API-client GREEN, typecheck, and lint**

```powershell
npm.cmd --prefix apps/web test -- src/studio/studio-api.test.ts
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
```

- [ ] **Step 5: Commit**

```powershell
git add -- apps/web/src/studio/studio-api.ts apps/web/src/studio/studio-api.test.ts
git commit -m "feat: add token-safe Studio client"
```

---

### Task 3: Model the complete legal Studio flow (Person B)

**Files:**

- Create: `apps/web/src/studio/studio-state.ts`
- Create: `apps/web/src/studio/studio-state.test.ts`
- Reuse: `apps/web/src/revision/revision-flow.ts`

**Interfaces:**

- Produces: `StudioPhase`, `StudioState`, `StudioEvent`, `initialStudioState()`, `studioReducer(state, event)`, and guards `canUpload`, `canConfirmBrandLock`, `canGenerate`, `canSubmitRevision`, `canRetry`, `canExport`, `canDelete`.
- Consumes: public generated response types and bounded `StudioErrorCode` from Task 2.
- Guarantees: `visibleVersions` is exactly `[]`, `[1]`, or `[1, 2]`; capabilities exist only on in-memory state and are removed by `reset`.

- [ ] **Step 1: Write failing bilateral transition tests**

Cover the exact happy path and illegal actions:

```typescript
it.each(["china-to-uk", "uk-to-china"] as const)(
  "reaches ready version one for %s through every required phase",
  (fixtureId) => {
    let state = initialStudioState(fixtureId);
    state = studioReducer(state, { type: "upload_started" });
    state = studioReducer(state, { type: "upload_succeeded", result: uploaded });
    state = studioReducer(state, { type: "run_created", result: runCreated });
    state = studioReducer(state, { type: "analysis_succeeded", result: analysis });
    state = studioReducer(state, { type: "brand_lock_confirmed", result: confirmation });
    state = studioReducer(state, { type: "draft_succeeded", result: draft });
    state = studioReducer(state, { type: "composition_succeeded", result: composition });
    state = studioReducer(state, { type: "critic_succeeded", result: critique });

    expect(state.phase).toBe("ready_v1");
    expect(state.visibleVersions).toEqual([1]);
    expect(canSubmitRevision(state)).toBe(true);
  },
);

it("replay replaces version two and never appends version three", () => {
  const first = studioReducer(submittingRevisionState(), {
    type: "revision_succeeded",
    result: revision,
  });
  const replay = studioReducer(first, { type: "revision_succeeded", result: revision });
  expect(replay.visibleVersions).toEqual([1, 2]);
});
```

Add tests for duplicate-event no-ops, immutable confirmation, the three conflicts, retryable versus final failure, token-expired reset, delete-in-progress, and successful delete/reset.

- [ ] **Step 2: Run state RED**

```powershell
npm.cmd --prefix apps/web test -- src/studio/studio-state.test.ts
```

Expected: module-not-found failure.

- [ ] **Step 3: Implement the minimal discriminated union and guards**

Use the approved phases verbatim and keep session values explicit:

```typescript
export type StudioPhase =
  | "configure" | "uploading" | "analyzing" | "awaiting_brand_lock"
  | "generating_draft" | "composing" | "reviewing" | "ready_v1"
  | "submitting_revision" | "ready_v2" | "retryable_failure"
  | "conflict" | "final_failure" | "deleting";

export interface StudioState {
  phase: StudioPhase;
  fixtureId: FixtureId;
  upload?: AssetUploaded;
  run?: RunCreated;
  analysis?: AnalysisCompleted;
  confirmation?: BrandLockConfirmed;
  draft?: DraftGenerated;
  composition?: CompositionGenerated;
  critique?: CritiqueCompleted;
  revision?: RevisionCompleted;
  visibleVersions: readonly [] | readonly [1] | readonly [1, 2];
  errorCode?: StudioErrorCode;
}
```

`reset` returns `initialStudioState(state.fixtureId)` and therefore removes both capabilities and all public workflow data. Never mirror capabilities into a separate module-level singleton.

- [ ] **Step 4: Run state GREEN, existing revision regression, typecheck, and lint**

```powershell
npm.cmd --prefix apps/web test -- src/studio/studio-state.test.ts src/revision/revision-flow.test.ts
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
```

- [ ] **Step 5: Commit**

```powershell
git add -- apps/web/src/studio/studio-state.ts apps/web/src/studio/studio-state.test.ts
git commit -m "feat: model connected Studio flow"
```

---

### Task 4: Build the connected `/studio` experience (Person B)

**Files:**

- Create: `apps/web/src/app/studio/studio-client.tsx`
- Create: `apps/web/src/app/studio/studio-client.test.tsx`
- Create: `apps/web/src/app/studio/page.tsx`
- Create: `apps/web/src/app/studio/studio.module.css`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/page.test.tsx`
- Reuse: `apps/web/src/components/brand-lock-form.tsx`
- Reuse: `apps/web/src/components/draft-evidence.tsx`
- Reuse: `apps/web/src/components/composition-evidence.tsx`

**Interfaces:**

- Produces: `StudioClient({ api? }: { api?: StudioApiClient })` with dependency injection for tests.
- Produces: `/studio` route and an accessible “Open connected Studio” link from `/`.
- Consumes: Task 2 client, Task 3 reducer/guards, existing bilateral fixtures, generated contracts, and existing evidence components.

- [ ] **Step 1: Write failing route and configuration tests**

Assert both fixture choices, upload prerequisites, authority confirmation, and the home link:

```typescript
it("requires an authorized supported source before upload", () => {
  render(<StudioClient api={fakeApi()} />);
  expect(screen.getByRole("button", { name: "Upload and start" })).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Provenance reference"), {
    target: { value: "fixture://day16/source" },
  });
  fireEvent.change(screen.getByLabelText("Rights reference"), {
    target: { value: "rights://authorized/day16" },
  });
  fireEvent.click(screen.getByRole("checkbox", { name: /authority to process/i }));
  uploadPng(screen.getByLabelText("Source ad"));
  expect(screen.getByRole("button", { name: "Upload and start" })).toBeEnabled();
});

it("links the fixture lab to the connected Studio", () => {
  render(<Home />);
  expect(screen.getByRole("link", { name: "Open connected Studio" })).toHaveAttribute(
    "href",
    "/studio",
  );
});
```

- [ ] **Step 2: Run route RED**

```powershell
npm.cmd --prefix apps/web test -- src/app/studio/studio-client.test.tsx src/app/page.test.tsx
```

Expected: missing Studio module/link failures.

- [ ] **Step 3: Implement configuration, upload, and analysis orchestration**

Create one client component with:

- bilateral fixture radio controls;
- file, provenance, rights, and authority controls;
- 10 MiB and `image/png|image/jpeg|image/webp` client validation;
- raw upload then Run creation using `{ ...fixture.request, source_asset: uploaded.asset }`;
- an analysis action and `role="status"` progress copy;
- sanitized `role="alert"` output mapped only from `StudioApiError.code`.

The selected source preview uses `URL.createObjectURL(file)` and revokes the prior URL whenever the file changes.

- [ ] **Step 4: Add failing Brand Lock and version-1 tests**

Use the fake client to resolve each action and assert:

```typescript
expect(await screen.findByRole("heading", { name: "Confirm Brand Lock" })).toBeVisible();
fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));
expect(await screen.findByText("Brand Lock confirmed and immutable.")).toBeVisible();
fireEvent.click(screen.getByRole("button", { name: "Generate fixture proposal" }));
expect(await screen.findByRole("heading", { name: "Version 1" })).toBeVisible();
expect(screen.getByText("Human review required")).toBeVisible();
expect(screen.getByText("Fixture Demo / 非实时模型")).toBeVisible();
```

Assert both directions call draft, composition, and Critic in order and that a Critic reject never renders a ready result.

- [ ] **Step 5: Implement live Brand Lock, progress, and version-1 result**

Pass the analyzed Brand Lock into the existing `BrandLockForm`; its callback calls `api.confirmBrandLock` and dispatches success only after the response validates. After confirmation, the generation button calls draft, composition, and Critic sequentially, dispatching the corresponding transition after each successful response.

Fetch version-1 PNG only after ready Critic. Render the source/result comparison, draft evidence, composition evidence, Critic findings, rule IDs, evidence references, warnings, disclosure, and pending hypotheses. Do not render raw API JSON or capabilities.

- [ ] **Step 6: Add failing revision, comparison, export, and delete tests**

Cover:

```typescript
fireEvent.click(screen.getByRole("checkbox", { name: "Shorten headline" }));
fireEvent.change(screen.getByLabelText("Feedback context"), {
  target: { value: "Headline is difficult to scan." },
});
fireEvent.click(screen.getByRole("button", { name: "Create version 2" }));
expect(await screen.findByRole("heading", { name: "Compare versions" })).toBeVisible();
expect(screen.getAllByText(/Version [12]/)).toHaveLength(2);
expect(screen.queryByText("Version 3")).not.toBeInTheDocument();

fireEvent.click(screen.getByRole("button", { name: "Export version 2 PNG" }));
expect(api.exportComposition).toHaveBeenCalledWith(runId, runToken, 2, "png");

fireEvent.click(screen.getByRole("button", { name: "Delete uploaded source and reset" }));
expect(api.deleteAsset).toHaveBeenCalledWith(assetId, deleteToken);
expect(await screen.findByRole("button", { name: "Upload and start" })).toBeVisible();
```

Also assert no rendered DOM, link `href`, alert, or mocked thrown error contains either capability token or raw private failure text. Distinguish the three revision conflicts and show retry only for `revision_failed`.

- [ ] **Step 7: Implement one-revision comparison, authorized downloads, and explicit reset**

Use the existing structured revision literals. Treat the feedback textarea as bounded context only. Keep one UUID idempotency key for the submitted logical feedback request and a separate key for an eligible retry.

For export, call `api.exportComposition`, create a temporary object URL from the returned Blob, invoke a download anchor with a fixed safe filename, remove the anchor, and revoke the URL. Never set an authenticated API URL directly on an anchor.

For deletion, require an explicit click, call only `deleteAsset`, revoke source and composition object URLs, dispatch `reset`, and state in the success copy that only the uploaded source asset was deleted.

- [ ] **Step 8: Style only the Studio route and verify accessibility states**

Use one responsive column below 800 px and a two-column comparison above it. Keep high-contrast phase/status labels, visible focus outlines, readable English/Chinese content, and no clipped result images. Do not restyle existing fixture pages.

- [ ] **Step 9: Run component GREEN and Web gates**

```powershell
npm.cmd --prefix apps/web test -- src/app/studio/studio-client.test.tsx src/app/page.test.tsx
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run build -- --webpack
```

- [ ] **Step 10: Commit**

```powershell
git add -- apps/web/src/app/studio apps/web/src/app/page.tsx apps/web/src/app/page.test.tsx
git commit -m "feat: connect the fixture Studio"
```

---

### Task 5: Run bilateral release gates, record Day 16, and publish safely (Person A + Person B)

**Files:**

- Modify only when a failing Day 16 acceptance test proves necessary: files from Tasks 1-4.
- Create outside Git: `../Day16.docx`.
- Do not create committed logs, screenshots, browser downloads, SQLite files, rendered pages, or API-upload staging directories.

**Interfaces:**

- Consumes: all Task 1-4 public interfaces.
- Produces: verified Day 16 tree, visually checked private record, non-force remote `main`, and successful GitHub Actions evidence.

- [ ] **Step 1: Add the focused bilateral connected-client acceptance test**

In `studio-client.test.tsx`, parameterize the two fixture IDs and assert the mocked typed client observes this order with matching Run ID and capability on every Run call:

```text
uploadAsset -> createRun -> analyzeRun -> confirmBrandLock ->
generateDraft -> generateComposition -> runCritic -> exportComposition(version 1)
```

Then cover feedback -> export version 2 -> source deletion in one direction. This is a client-contract acceptance test, not a claim of Day 17 live-browser E2E.

- [ ] **Step 2: Run the complete local release gate**

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='.day16-assets'
python -m pytest -q -p no:cacheprovider --basetemp .day16-pytest
python -m ruff check .
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run build -- --webpack
git diff --check
```

Every command must exit 0. If any test or build fails, invoke `superpowers:systematic-debugging`, establish the root cause, add or retain the reproducing test, and repair only Day 16 scope before rerunning the complete gate.

- [ ] **Step 3: Scan the public boundary and repository hygiene**

```powershell
rg -n -i "localStorage|sessionStorage|indexedDB|document\.cookie|console\.(log|error)|Bearer |capability.*href|feedback.*console|[A-Z]:\\\\" src tests apps/web docs
git status --short
git diff --check
```

Expected: no capability, raw feedback, local absolute path, private body, or exception text in production output or public docs; only intentional tests/configuration names remain. No `.day16-*`, `.cultureshift`, download, render, or SQLite artifact is staged.

- [ ] **Step 4: Create and visually verify `Day16.docx`**

Invoke the `documents:documents` skill. Match the Day 15 section order and typography, and record Issue #15, approved boundary, Person A and Person B outputs, commit SHAs, exact release-gate results, bilateral client-contract evidence, limitations, remote publication evidence, and CI result. Render every page with `render_docx.py`, inspect every page image, and correct clipping, widows, broken tables, or overflow. Keep only the final DOCX in the private parent folder.

- [ ] **Step 5: Commit final repository evidence**

```powershell
git add -- docs/superpowers/specs/2026-08-27-day16-studio-integration-design.md docs/superpowers/plans/2026-08-27-day16-studio-integration.md src tests apps/web
git diff --cached --check
git commit -m "feat: complete Day 16 connected Studio"
```

- [ ] **Step 6: Recheck the partner branch before publication**

Check `github.com:443` and `api.github.com:443`, then read remote `main` commit and tree. The expected Day 15 baseline is commit `6c34d3f84de1a01a9d41b8643a885e2f292f9cce` with tree `34d72510396a2dad540b5e7dc1df105d92dee011`. If remote `main` moved, stop and reconcile without force. Never overwrite a partner commit.

- [ ] **Step 7: Push with the previously verified fallback order**

When Git transport is healthy, use `git push origin HEAD:main`. If it resets or the escalated Windows identity rejects the worktree, immediately use GitHub Git Data API: upload only changed blobs, create a tree on the verified remote base tree, require the new tree SHA to equal local `HEAD^{tree}`, create one commit, and update `refs/heads/main` with `force=false` and the expected-old-SHA guard. Do not repeat browser upload attempts.

- [ ] **Step 8: Verify remote tree and GitHub Actions**

Confirm remote `main` points to the published commit and its tree equals local `HEAD^{tree}`. Wait for the workflow associated with that commit and require every job to succeed. Queued, running, skipped-required, cancelled, or failed is not completion.

- [ ] **Step 9: Remove only named Day 16 temporary artifacts**

Resolve and verify each target before removal. Delete only `.day16-pytest`, `.day16-assets`, `.day16-docx-render`, and `.day16-api-upload` if present inside the repository or private parent folder. Preserve `Day16.docx`, the repository, worktrees, partner files, and every unrelated user file. Finish with `git status -sb` and a parent-folder listing proving no Day 16 temporary directories remain.
