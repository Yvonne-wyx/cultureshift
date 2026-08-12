# Day 5 Fixture Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add capability-protected run recovery and a deterministic, watermarked bilateral fixture result walkthrough without entering Day 6+ scope.

**Architecture:** FastAPI reads a stable capability secret at application construction, exposes one authenticated run-read endpoint, and reuses the existing SQLite repository for restart recovery. The web application composes validated Day 4 fixtures through a pure TypeScript function into static result routes with an always-visible three-step walkthrough. Python and web lanes are developed with focused tests, then converge in the existing CI and one final verification pass.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLite, pytest, Ruff, Next.js 16.3.0, React 19.2.4, TypeScript, Vitest, Testing Library, GitHub Actions.

## Global Constraints

- Track all work against GitHub Issue #4 and the approved Day 5 design.
- Support only `china-to-uk` and `uk-to-china` fixture directions.
- The environment variable is exactly `CULTURESHIFT_CAPABILITY_SECRET` and must encode to at least 32 UTF-8 bytes.
- The exact result watermark is `Fixture Demo / 非实时模型`.
- Preserve the approved Orbit AI Brand Lock and keep every cultural hypothesis pending human review.
- Do not add upload, storage lifecycle, provider, analysis, Brand Lock confirmation, export, feedback, revision, telemetry, deployment, external assets, or new dependencies.
- Do not log, persist, or echo capability tokens, secrets, private content, local paths, or internal exception details.
- Use focused RED-to-GREEN tests during implementation, one final full verification, and at most one consolidated repair pass.

---

### Task 1: Capability-protected run retrieval and restart recovery

**Files:**
- Modify: `src/cultureshift/app.py`
- Modify: `src/cultureshift/contracts.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_contracts.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `CapabilityTokenService.verify(token, required=Capability.READ_PROJECT_RUN)`, `SQLiteProjectRunRepository.get(run_id)`, and the existing `ProjectRun` persistence model.
- Produces: `RunSnapshot` and `GET /api/v1/runs/{run_id}` with stable safe error codes.

- [ ] **Step 1: Add contract and endpoint RED tests**

Add a `RunSnapshot` contract test that validates this exact public shape and rejects unknown fields:

```python
snapshot = RunSnapshot(
    run_id=run.id,
    direction=run.direction,
    status=run.status,
    warning_codes=run.warning_codes,
    created_at=run.created_at,
    updated_at=run.updated_at,
)
assert snapshot.model_dump(mode="json")["direction"] == "china_to_uk"
```

Add API tests that create a run, then retrieve it with `Authorization: Bearer <capability_token>`. Assert the response contains exactly the public snapshot fields and no token. Add parameterized failures for missing header, non-Bearer header, malformed token, expired token, wrong audience, and update-only scope; assert `401` and `{"detail": {"code": "invalid_capability"}}` without the submitted authorization value.

Add subject isolation and missing-run cases:

```python
assert subject_mismatch.status_code == 403
assert subject_mismatch.json() == {"detail": {"code": "capability_subject_mismatch"}}
assert absent.status_code == 404
assert absent.json() == {"detail": {"code": "run_not_found"}}
```

- [ ] **Step 2: Verify the endpoint tests fail for the missing behavior**

Run:

```powershell
python -m pytest tests/test_contracts.py tests/test_app.py -q
```

Expected: RED because `RunSnapshot` and the GET endpoint do not exist.

- [ ] **Step 3: Implement the public snapshot and authenticated GET endpoint**

Add a frozen, extra-forbid `RunSnapshot` contract using existing public enums and UTC validation. In `app.py`, parse the header without retaining it in errors, verify `READ_PROJECT_RUN`, compare `claims.subject` to `str(run_id)`, then call the repository. Map failures only to the three approved response codes. Return `RunSnapshot.model_validate(...)` from non-sensitive repository state.

- [ ] **Step 4: Add environment and restart RED tests**

Add tests that construct the default app with a missing or short environment variable and expect a configuration-only `RuntimeError` without the value. Add a restart test using two app instances, one SQLite path, and two independently constructed token services with the same 32-byte secret. The first creates a run; the second retrieves it with the original token. A third app using a different secret must return `401`. Confirm SQLite has no token or secret column.

- [ ] **Step 5: Implement the stable default secret boundary**

Create a small private helper in `app.py`:

```python
def _capability_service_from_environment() -> CapabilityTokenService:
    value = os.environ.get("CULTURESHIFT_CAPABILITY_SECRET")
    if value is None or len(value.encode("utf-8")) < 32:
        raise RuntimeError("CULTURESHIFT_CAPABILITY_SECRET must contain at least 32 UTF-8 bytes")
    return CapabilityTokenService(secret=value.encode("utf-8"), audience="cultureshift-api")
```

Keep explicit dependency injection unchanged for tests. Configure the backend CI job with a fixed non-production test string of at least 32 bytes.

- [ ] **Step 6: Verify Person A GREEN and commit**

Run:

```powershell
python -m pytest tests/test_contracts.py tests/test_app.py tests/test_repository.py tests/test_capability_tokens.py -q
python -m ruff check src/cultureshift/app.py src/cultureshift/contracts.py tests/test_app.py tests/test_contracts.py
```

Expected: all selected tests pass and Ruff reports no findings.

Commit:

```powershell
git add src/cultureshift/app.py src/cultureshift/contracts.py tests/test_app.py tests/test_contracts.py .github/workflows/ci.yml
git commit -m "feat: recover capability-protected runs"
```

---

### Task 2: Deterministic fixture results and three-step walkthrough

**Files:**
- Create: `apps/web/src/results/types.ts`
- Create: `apps/web/src/results/compose-fixture-result.ts`
- Create: `apps/web/src/results/compose-fixture-result.test.ts`
- Create: `apps/web/src/components/fixture-result.tsx`
- Create: `apps/web/src/components/fixture-result.module.css`
- Create: `apps/web/src/components/fixture-result.test.tsx`
- Create: `apps/web/src/app/results/[fixtureId]/page.tsx`
- Create: `apps/web/src/app/results/[fixtureId]/page.test.tsx`
- Modify: `apps/web/src/components/fixture-preview.tsx`
- Modify: `apps/web/src/components/fixture-preview.test.tsx`
- Modify: `apps/web/src/app/page.test.tsx`

**Interfaces:**
- Consumes: `FixtureBundle`, `FixtureId`, `loadFixture(id)`, `listFixtureIds()`, and only the existing project-owned public asset paths.
- Produces: `FixtureResult`, `composeFixtureResult(fixture)`, `FixtureResultView`, and two static `/results/[fixtureId]` routes.

- [ ] **Step 1: Add pure composer RED tests**

Define the wished-for interface in tests:

```typescript
const first = composeFixtureResult(loadFixture("china-to-uk"));
const second = composeFixtureResult(loadFixture("china-to-uk"));

expect(first).toEqual(second);
expect(JSON.stringify(first)).toBe(JSON.stringify(second));
expect(first.watermark).toBe("Fixture Demo / 非实时模型");
expect(first.walkthrough.map((step) => step.id)).toEqual([
  "verify-source",
  "inspect-composition",
  "review-evidence",
]);
```

Test both fixture IDs. Assert the result preserves exact Brand Lock values, localized copy, rule IDs, hypotheses, warnings, limitation, and public asset references; is deeply frozen; and does not mutate the source fixture.

- [ ] **Step 2: Verify composer RED**

Run:

```powershell
npm.cmd --prefix apps/web test -- src/results/compose-fixture-result.test.ts
```

Expected: RED because the result module does not exist.

- [ ] **Step 3: Implement the minimal pure result composer**

Define `FixtureResult` with explicit readonly fields and exactly three readonly walkthrough steps. Implement `composeFixtureResult` as a synchronous mapping from validated fixture fields, then recursively freeze the new object. Do not use `Date`, randomness, fetch, DOM APIs, filesystem APIs, environment variables, or providers.

- [ ] **Step 4: Add result component and route RED tests**

For `FixtureResultView`, render a real composed result and assert:

- one visible and semantic `Fixture Demo / 非实时模型` watermark;
- the human-readable direction, source creative, result composition, localized copy, and CTA meaning;
- every Brand Lock field and value;
- every rule, pending hypothesis, evidence reference, warning, and limitation;
- an ordered three-item walkthrough with the approved step headings;
- no generation, retry, edit, export, download, approval, or live-model controls.

For the route, call `generateStaticParams()` and expect exactly the two fixture IDs. Render each route and assert a link back to `/`, the direction heading, watermark, and walkthrough. Assert an unknown ID invokes the not-found boundary.

- [ ] **Step 5: Verify UI RED**

Run:

```powershell
npm.cmd --prefix apps/web test -- src/components/fixture-result.test.tsx "src/app/results/[fixtureId]/page.test.tsx"
```

Expected: RED because the result component and route do not exist.

- [ ] **Step 6: Implement the static result view and route**

Build a server-compatible `FixtureResultView` with semantic sections and an `<ol>` walkthrough. Use CSS pseudo-element or a normal repeated text layer for the composition watermark, plus visible text associated with a `data-watermark` marker; do not alter the hashed fixture SVG files. The route validates the runtime segment against `listFixtureIds()`, calls `notFound()` otherwise, composes the validated fixture, and renders the result.

- [ ] **Step 7: Link the bilateral entry page and verify Person B GREEN**

Add one descriptive result link per `FixturePreview`, such as `/results/china-to-uk`. Preserve the existing read-only preview content and tests.

Run:

```powershell
npm.cmd --prefix apps/web test -- src/results src/components src/app
npm.cmd --prefix apps/web run typecheck
```

Expected: all selected web tests pass and TypeScript reports no errors.

Commit:

```powershell
git add apps/web/src/results apps/web/src/components apps/web/src/app
git commit -m "feat: present deterministic fixture results"
```

---

### Task 3: CI convergence, final verification, publication, and evidence

**Files:**
- Modify if required: `.github/workflows/ci.yml`
- Create: `Day5.docx` outside the repository at `D:\create\Diversity\Day5.docx`

**Interfaces:**
- Consumes: all Task 1 and Task 2 deliverables, the existing manifest/schema/contract/public-boundary scripts, and the Day 4 document template.
- Produces: a verified Day 5 repository tree on GitHub `main` and a local Day 5 completion record.

- [ ] **Step 1: Run the single consolidated repository verification**

Run once after both focused lanes are green:

```powershell
python -m pytest -q
python -m ruff check .
python scripts/validate_demo_manifest.py
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
$env:NEXT_TELEMETRY_DISABLED='1'; npm.cmd --prefix apps/web run build
npm.cmd --prefix apps/web audit --audit-level=high
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify-public-boundary.ps1
git diff --check
git status --short
```

Expected: every command passes; only already-recorded non-blocking deprecation or cache warnings may remain; the worktree contains no uncommitted implementation changes.

- [ ] **Step 2: Apply at most one consolidated repair pass if a final gate fails**

For each genuine failure, first add or narrow a regression test that reproduces the behavior, run it RED, apply the smallest correction, and rerun only the affected focused gate. After the repair pass, rerun the complete Step 1 command set once. Do not add enhancements during repair.

- [ ] **Step 3: Commit any CI-only convergence change**

If `.github/workflows/ci.yml` required a post-task adjustment, stage only that file and its focused test, then commit:

```powershell
git commit -m "ci: verify Day 5 vertical slice"
```

- [ ] **Step 4: Publish the exact verified tree**

Attempt normal `git push origin main` first. If Git smart-HTTP is reset, use the already proven GitHub Git Database API fallback with the current remote main SHA as a fail-closed parent and verify that the created remote tree equals local `HEAD^{tree}`. Do not force-update and do not overwrite a changed remote baseline.

- [ ] **Step 5: Generate and structurally verify the Day 5 record**

Use `D:\create\Diversity\Day4.docx` as the retained format template. Record the actual Issue #4 URL, Person A and Person B deliverables, RED-to-GREEN evidence, test counts, local and remote commits, compressed-publication disclosure when applicable, residual warnings, and Day 6 exclusions. Preserve Letter geometry, styles, two-column evidence tables, footer PAGE field, and real list styles. Structurally audit headings, tables, footer, placeholders, mojibake, and package integrity; render visually if LibreOffice is available, otherwise disclose the renderer limitation.

- [ ] **Step 6: Final handoff**

Report the GitHub commit URL, actual verification counts, and the local `Day5.docx`. Do not claim Issue closure or modify its state unless separately authorized.
