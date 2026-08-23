# Day 13 T08 Export and Composition Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Export immutable fixture compositions as verified PNG and canonical JSON artifacts while adding deterministic bilingual wrapping, protected-layer golden verification, and a bilateral public workflow test.

**Architecture:** Keep the Day 12 fixture-only provider and immutable composition summary unchanged. Add pure wrapping helpers to the Pillow compositor and a small read-only export service that cross-checks repository metadata with TTL-scoped artifact bytes before the FastAPI routes return attachments. Exercise the full public fixture workflow for both directions and record the provider/export boundary in ADR-0008.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, Pillow 12.3.0, SQLite, pytest, Ruff, Next.js 16, React 19, TypeScript 5, Vitest

**Spec:** `docs/superpowers/specs/2026-08-23-day13-t08-export-polish-design.md`

## Global Constraints

- Work is tied to GitHub Issue `#12` and remains within Day 13 T08.
- Runtime execution remains fixture-only, deterministic, offline, and `in_progress`.
- Export requires `project_run:read` with an exact `run_id` subject.
- Export never regenerates an artifact, extends TTL, mutates a run, or accepts a caller path or filename.
- Only `image/png` and canonical bounded `application/json` attachments are added.
- English wraps at whitespace; Simplified Chinese may wrap between characters; approved copy is never rewritten, hyphenated, truncated, or ellipsized.
- Logo and product UI remain separate protected layers sourced only from the confirmed Brand Lock and registered fixture registry.
- No live provider, SDK, credential, ZIP, cloud storage, signed URL, critique, revision, approval, or production-validation claim is introduced.
- Preserve `Fixture Demo / 非实时模型` and the human-review limitation.
- Use observable RED then GREEN, minimal implementation, and focused commits.

---

### Task 1: Deterministic bilingual wrapping and protected-layer golden verification

**Files:**
- Modify: `src/cultureshift/composition.py`
- Modify: `tests/test_composition.py`
- Modify if output hashes change: `scripts/build_day12_fixture_assets.py`
- Modify if output hashes change: `apps/web/public/fixtures/orbit-ai/composed-china-to-uk.png`
- Modify if output hashes change: `apps/web/public/fixtures/orbit-ai/composed-uk-to-china.png`
- Modify if output hashes change: `apps/web/src/fixtures/data/china-to-uk.json`
- Modify if output hashes change: `apps/web/src/fixtures/data/uk-to-china.json`
- Modify if output hashes change: `demo/assets/manifest.json`

**Interfaces:**
- Consumes: pinned `NotoSansCJKsc-Regular.otf`, `ComposeRequest`, registered Logo/UI rasters, and fixed semantic layer boxes.
- Produces: `_wrap_text(font, text, maximum_width, maximum_lines) -> tuple[str, ...]`, deterministic multi-line `_text_layer(...)`, and unchanged `PillowCompositor.compose(...) -> ComposedAd`.

- [ ] **Step 1: Add failing wrapping and overflow tests**

Add focused tests that import `_wrap_text` and prove word-aware English, character-aware CJK,
mixed-token preservation, stable whitespace normalization, exact-fit behavior, and failure when a
minimum-size text box cannot contain the input:

```python
def test_wrap_text_is_deterministic_for_english_cjk_and_mixed_copy(font_path) -> None:
    font = ImageFont.truetype(str(font_path), 34)
    assert _wrap_text(font, "Trusted AI workflows for teams", 250, 3) == (
        "Trusted AI",
        "workflows for",
        "teams",
    )
    assert _wrap_text(font, "可信赖的人工智能工作流", 180, 3) == (
        "可信赖的",
        "人工智能",
        "工作流",
    )
    first = _wrap_text(font, "团队使用 Orbit 360 平台", 260, 3)
    assert first == _wrap_text(font, "  团队使用  Orbit 360  平台  ", 260, 3)
    assert "Orbit 360" in " ".join(first)


def test_text_layer_fails_closed_instead_of_truncating(font_path) -> None:
    with pytest.raises(CompositionError) as caught:
        _text_layer(
            font_path,
            "one two three four five six seven eight nine ten",
            (90, 40),
            start_font=18,
            minimum_font=18,
            maximum_lines=1,
            colour="#000000",
        )
    assert caught.value.code is CompositionErrorCode.INVALID_OUTPUT
```

- [ ] **Step 2: Run the wrapping tests and confirm RED**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_composition.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-wrap-red
```

Expected: collection or assertions fail because `_wrap_text` and `maximum_lines` do not exist.

- [ ] **Step 3: Implement the minimal deterministic wrapping algorithm**

In `composition.py`, add a tokenizer that groups contiguous Latin letters/numbers, treats
normalized spaces as break opportunities, and permits breaks between CJK characters. Measure
candidate lines using `font.getlength`, greedily take the longest fitting prefix, and raise
`CompositionError(INVALID_OUTPUT)` when one token or the line count cannot fit.

Change `_fit_font` to return `(font, lines)` only when both width and height fit. Render each line
with a fixed line gap and vertically center the complete line block. Add explicit limits:

```python
headline: maximum_lines=2
body: maximum_lines=3
cta: maximum_lines=2
disclosure: maximum_lines=1
```

Do not change fixed box bounds, colors, font provenance, z-order, copy, or protected assets.

- [ ] **Step 4: Add independent golden protected-layer tests**

For both fixture directions, decode the registered source raster, independently apply
`thumbnail((650, 520), Image.Resampling.LANCZOS)` or `thumbnail((220, 96), ...)`, and compare the
expected RGBA bytes with `composed.layer_png("product_ui")` and `composed.layer_png("logo")`:

```python
@pytest.mark.parametrize("direction", [Direction.CHINA_TO_UK, Direction.UK_TO_CHINA])
def test_locked_layers_preserve_registered_pixels_and_geometry(direction, compose_request) -> None:
    request = compose_request(direction)
    composed = PillowCompositor().compose(request)
    for kind, registered, maximum in (
        ("logo", request.logo, (220, 96)),
        ("product_ui", request.product_ui, (650, 520)),
    ):
        expected = Image.open(BytesIO(registered.png_bytes)).convert("RGBA")
        expected.thumbnail(maximum, Image.Resampling.LANCZOS)
        actual = Image.open(BytesIO(composed.layer_png(kind))).convert("RGBA")
        assert actual.size == expected.size
        assert actual.tobytes() == expected.tobytes()
        evidence = composed.layer(kind)
        assert evidence.source_asset_id == registered.asset_id
        assert evidence.rgba_sha256 == hashlib.sha256(expected.tobytes()).hexdigest()
        assert actual.getbbox() == expected.getbbox()
```

Keep the existing negative tests for missing/wrong Brand Lock assets and CTA meaning drift.

- [ ] **Step 5: Run focused GREEN checks and regenerate only when required**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_composition.py tests/test_fixture_assets.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-wrap-green
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check src/cultureshift/composition.py tests/test_composition.py
```

If the existing bilateral preview hashes fail because wrapping legitimately changed rendered
pixels, run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe scripts/build_day12_fixture_assets.py
..\day8-analysis-foundation\.venv\Scripts\python.exe scripts/validate_demo_manifest.py
npm.cmd --prefix apps/web test -- fixture-loader composition-evidence page
```

Inspect the diff to confirm only deterministic previews and their recorded hashes changed.

- [ ] **Step 6: Commit the compositor slice**

```powershell
git add -- src/cultureshift/composition.py tests/test_composition.py scripts/build_day12_fixture_assets.py apps/web/public/fixtures/orbit-ai apps/web/src/fixtures/data demo/assets/manifest.json
git commit -m "feat: harden Day 13 bilingual composition"
```

---

### Task 2: Integrity-checked PNG and canonical JSON export

**Files:**
- Create: `src/cultureshift/composition_export.py`
- Create: `tests/test_composition_export.py`
- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `SQLiteProjectRunRepository.get_composition(run_id)`, `CompositionArtifactStore.load(artifact_id)`, `CompositionGenerated`, and `Capability.READ_PROJECT_RUN`.
- Produces: `CompositionExportService.export_png(run_id) -> ExportedComposition`, `CompositionExportService.export_json(run_id) -> bytes`, and two authenticated GET routes.

- [ ] **Step 1: Add failing export-service tests**

Create `tests/test_composition_export.py` with fixtures that persist a real summary and artifact.
Test exact bytes, canonical JSON, metadata cross-checks, and bounded failures:

```python
def test_export_service_returns_verified_png_and_canonical_json(export_service, summary, png_bytes) -> None:
    exported = export_service.export_png(summary.run_id)
    assert exported.png_bytes == png_bytes
    assert exported.sha256 == summary.rendered_sha256
    encoded = export_service.export_json(summary.run_id)
    assert encoded.endswith(b"\n")
    assert json.loads(encoded) == summary.model_dump(mode="json")
    assert encoded == json.dumps(
        summary.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8") + b"\n"


@pytest.mark.parametrize("mutation", ["missing", "expired", "hash", "dimensions"])
def test_export_service_fails_closed_for_unavailable_or_inconsistent_artifact(
    export_service_factory, mutation
) -> None:
    service = export_service_factory(mutation)
    with pytest.raises(CompositionExportError) as caught:
        service.export_png(RUN_ID)
    assert caught.value.code is CompositionExportErrorCode.ARTIFACT_UNAVAILABLE
```

- [ ] **Step 2: Run export-service tests and confirm RED**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_composition_export.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-export-red
```

Expected: collection fails because `cultureshift.composition_export` does not exist.

- [ ] **Step 3: Implement the read-only export service**

Create frozen `ExportedComposition(png_bytes: bytes, sha256: str, size_bytes: int)` and stable
codes `RUN_NOT_FOUND`, `COMPOSITION_UNAVAILABLE`, and `ARTIFACT_UNAVAILABLE`. `export_png` must:

```python
summary = repository.get_composition(run_id)
if summary is None:
    raise CompositionExportError(COMPOSITION_UNAVAILABLE)
loaded = artifact_store.load(summary.artifact_id)
if loaded.record.artifact_id != summary.artifact_id:
    raise CompositionExportError(ARTIFACT_UNAVAILABLE)
if loaded.record.sha256 != summary.rendered_sha256:
    raise CompositionExportError(ARTIFACT_UNAVAILABLE)
with Image.open(BytesIO(loaded.png_bytes)) as image:
    if image.format != "PNG" or image.size != (summary.width, summary.height):
        raise CompositionExportError(ARTIFACT_UNAVAILABLE)
return ExportedComposition(loaded.png_bytes, loaded.record.sha256, loaded.record.size_bytes)
```

Translate repository/store/Pillow exceptions without including source exception text.
`export_json` loads only the summary and emits sorted compact UTF-8 JSON plus one newline.

- [ ] **Step 4: Add failing authenticated route tests**

In `tests/test_app.py`, extend the app factory to inject the export service and test:

```python
png = client.get(
    f"/api/v1/runs/{run_id}/composition.png",
    headers={"Authorization": f"Bearer {token}"},
)
metadata = client.get(
    f"/api/v1/runs/{run_id}/composition.json",
    headers={"Authorization": f"Bearer {token}"},
)
assert png.status_code == metadata.status_code == 200
assert png.headers["content-type"] == "image/png"
assert png.headers["content-disposition"] == (
    f'attachment; filename="cultureshift-{run_id}.png"'
)
assert png.headers["x-content-type-options"] == "nosniff"
assert hashlib.sha256(png.content).hexdigest() == metadata.json()["rendered_sha256"]
assert "path" not in metadata.text.casefold()
```

Also issue a token containing only `UPDATE_PROJECT_RUN` and assert both GETs return 401; use a
read token for another run and assert 403; assert missing composition is 409 and missing/corrupt
artifact is 410 with stable bounded JSON errors.

- [ ] **Step 5: Run route tests and confirm RED**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_app.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-routes-red
```

Expected: the new GET routes return 404 or app construction rejects the missing export service.

- [ ] **Step 6: Wire the two FastAPI routes**

Construct `CompositionExportService` from the same repository and `CompositionArtifactStore`
instances used by composition generation. Add a local authentication helper that verifies
`Capability.READ_PROJECT_RUN` and exact subject equality without echoing authorization input.

Return `Response` objects with fixed attachment filenames derived from parsed UUID `run_id`:

```python
return Response(
    content=exported.png_bytes,
    media_type="image/png",
    headers={
        "Content-Disposition": f'attachment; filename="cultureshift-{run_id}.png"',
        "X-Content-Type-Options": "nosniff",
    },
)
```

Use the same header pattern for JSON. Map run-not-found to 404, missing composition to 409, and
expired/missing/corrupt artifact to 410. Responses expose only stable codes.

- [ ] **Step 7: Run focused GREEN and static checks**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_composition_export.py tests/test_app.py tests/test_capability_tokens.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-export-green
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check src/cultureshift/composition_export.py src/cultureshift/app.py tests/test_composition_export.py tests/test_app.py
```

Expected: all focused tests and Ruff pass.

- [ ] **Step 8: Commit the export slice**

```powershell
git add -- src/cultureshift/composition_export.py src/cultureshift/app.py tests/test_composition_export.py tests/test_app.py
git commit -m "feat: export verified Day 13 compositions"
```

---

### Task 3: Bilateral public-flow proof and provider ADR

**Files:**
- Create: `tests/test_day13_integration.py`
- Modify: `docs/decisions/ADR-0008-image-provider.md`
- Modify: `docs/evidence/index.md`

**Interfaces:**
- Consumes: all public Day 6–13 HTTP routes, fixture upload bytes, run capability token, immutable composition summary, and the two export routes.
- Produces: one parametrized bilateral integration test and an accurate fixture-only provider/export decision record.

- [ ] **Step 1: Add the failing bilateral public workflow test**

Create a parametrized test for `china_to_uk` and `uk_to_china`. Use the real `TestClient` and
fixture provider, upload authorized fixture PNGs with provenance/rights headers, create the run,
analyze, confirm Brand Lock, generate draft, generate composition, and export twice:

```python
@pytest.mark.parametrize("direction", ["china_to_uk", "uk_to_china"])
def test_day13_bilateral_upload_to_export_is_repeatable(tmp_path, direction, valid_run_payload):
    client, _ = make_day13_client(tmp_path)
    with client:
        assets = upload_registered_fixture_assets(client)
        run_id, token = create_fixture_run(client, valid_run_payload, direction, assets)
        assert client.post(f"/api/v1/runs/{run_id}/analyze", headers=auth(token)).status_code == 200
        assert confirm_exact_brand_lock(client, run_id, token, assets).status_code == 200
        assert client.post(f"/api/v1/runs/{run_id}/draft", headers=auth(token)).status_code == 200
        generated = client.post(f"/api/v1/runs/{run_id}/composition", headers=auth(token))
        first_png = client.get(f"/api/v1/runs/{run_id}/composition.png", headers=auth(token))
        second_png = client.get(f"/api/v1/runs/{run_id}/composition.png", headers=auth(token))
        exported_json = client.get(f"/api/v1/runs/{run_id}/composition.json", headers=auth(token))
    assert first_png.content == second_png.content
    assert hashlib.sha256(first_png.content).hexdigest() == generated.json()["rendered_sha256"]
    assert exported_json.json() == generated.json()
    assert exported_json.json()["disclosure"] == "Fixture Demo / 非实时模型"
```

The helpers must call public routes rather than repository shortcuts for workflow actions.

- [ ] **Step 2: Run the integration test and confirm RED**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_day13_integration.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-flow-red
```

Expected: fail until the fixture uploads and export behavior satisfy the complete route sequence.

- [ ] **Step 3: Apply only integration defects proven by the test**

Fix public-flow mismatches with the smallest change and a failing regression in the owning test
file first. Do not add workflow completion, live-provider behavior, revision state, or new UI.

- [ ] **Step 4: Update ADR-0008 and evidence index**

Add a “Day 13 export boundary” section stating:

- exports serve only a previously persisted fixture composition;
- the server checks TTL, artifact ID, hash, PNG decoding, and fixed dimensions before delivery;
- canonical JSON contains only public `CompositionGenerated` evidence;
- export support neither selects nor approves a live image provider;
- protected pixel checks and deterministic bilingual wrapping are technical evidence, not human
  cultural, legal, brand, or performance approval.

Add Issue #12, the design, plan, focused tests, and local `Day13.docx` record to the evidence
index using its existing table format.

- [ ] **Step 5: Run bilateral GREEN checks**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_day13_integration.py tests/test_composition.py tests/test_composition_export.py tests/test_app.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-flow-green
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check src/cultureshift tests/test_day13_integration.py
```

Expected: all focused tests and Ruff pass for both directions.

- [ ] **Step 6: Commit the integration and decision record**

```powershell
git add -- tests/test_day13_integration.py docs/decisions/ADR-0008-image-provider.md docs/evidence/index.md
git commit -m "test: prove Day 13 bilateral export flow"
```

---

### Task 4: Generated artifacts, full verification, daily record, and safe publication

**Files:**
- Modify if generated output changes: `contracts/json-schema/cultureshift.contracts.schema.json`
- Modify if generated output changes: `apps/web/src/generated/contracts.ts`
- Create outside repository: `D:\create\Diversity\Day13.docx`

**Interfaces:**
- Consumes: final Day 13 branch tree, Issue #12, all test output, and the established Day 12 daily-record format.
- Produces: reproducible generated contracts, passing repository gates, visually verified Day13.docx, and a non-force update of GitHub `main`.

- [ ] **Step 1: Refresh and verify generated contracts**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe scripts/export_contracts.py
npm.cmd --prefix apps/web run contracts:generate
git diff -- contracts/json-schema/cultureshift.contracts.schema.json apps/web/src/generated/contracts.ts
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_contracts.py tests/test_schema_export.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-contracts
npm.cmd --prefix apps/web run contracts:check
```

Expected: generators are deterministic and freshness checks pass. Commit only real generated
changes:

```powershell
git add -- contracts/json-schema/cultureshift.contracts.schema.json apps/web/src/generated/contracts.ts
git diff --cached --quiet || git commit -m "chore: refresh Day 13 contracts"
```

- [ ] **Step 2: Run the complete repository verification matrix**

Run:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp D:\create\Diversity\.day13-full
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check .
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run build
npm.cmd --prefix apps/web audit --audit-level=high
..\day8-analysis-foundation\.venv\Scripts\python.exe scripts/validate_demo_manifest.py
pwsh -File scripts/verify-public-boundary.ps1
git diff --check
git status -sb
```

Expected: every command exits zero and the worktree contains no uncommitted implementation
changes.

- [ ] **Step 3: Create and visually verify the local daily record**

Use the documents skill and the established `Day12.docx` structure. Record:

- plan-row requirements for Person A and Person B;
- Issue #12, design/plan files, commits, exact changed files, and implementation boundaries;
- focused and full verification commands with observed pass counts;
- privacy, fixture-only, Brand Lock, human-review, and no-live-provider limitations;
- remote preflight, publication result, remote commit/tree, and GitHub Actions result.

Save to `D:\create\Diversity\Day13.docx`, render every page with `render_docx.py`, inspect all
page PNGs, run structural/accessibility checks, and revise until there is no clipping, overlap,
or malformed table content.

- [ ] **Step 4: Re-check remote `main` and publish without force**

Test `github.com` and `api.github.com`, then read remote `main`. If it still equals the recorded
Day 12 base, try one normal `git push`. If the connection resets, immediately use the previously
validated GitHub Git Data API route: create blobs/tree/commit with the current remote commit as
parent and update `refs/heads/main` with `force=false`. If remote moved, stop and reconcile the
partner commit before publication.

- [ ] **Step 5: Verify remote identity and CI**

Confirm remote `main` has the exact local tree, verify the remote commit message and parent, and
wait for the associated GitHub Actions run to complete successfully. Update `Day13.docx` with the
final remote commit, tree, and CI run, then rerender and recheck the document.

---

## Self-review

- Spec coverage: Tasks 1–4 cover export security, canonical JSON, bilingual wrapping, protected
  pixels, bilateral workflow, ADR evidence, generated artifacts, local record, safe push, and CI.
- Scope: no Day 14 workflow state, critique, revision, live provider, or expanded export product
  appears in any task.
- Type consistency: `CompositionExportService`, `ExportedComposition`, error codes, route paths,
  capability scope, and fixed filenames are identical wherever referenced.
- Placeholder scan: all implementation actions identify exact behavior, files, commands, and
  expected RED/GREEN evidence.
