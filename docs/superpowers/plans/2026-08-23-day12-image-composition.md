# Day 12 Fixture Image Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce deterministic 1600 x 900 fixture compositions for both supported directions from trusted Day 11 runs, with constrained background generation, Brand-locked Pillow layers, bilingual evidence, and no live provider calls.

**Architecture:** A fixture-only `ImageProvider` creates validated background PNGs from structured requests that exclude every protected element. A focused composition service resolves only registered fixture assets, delegates fixed-layout rendering to a Pillow compositor, stores the output in TTL-scoped temporary storage, persists immutable bounded metadata, and exposes a bodyless authenticated API. The Web fixture slice displays committed previews and typed layer evidence without making runtime provider calls.

**Tech Stack:** Python 3.13.5, FastAPI, Pydantic 2, Pillow 12.3.0, SQLite, pytest, Next.js, React, TypeScript, Vitest, JSON Schema.

**Spec:** `docs/superpowers/specs/2026-08-23-day12-image-composition-design.md`

## Global Constraints

- Work is tied to GitHub Issue `#11` and remains within Day 12 T08.
- Support only static AI software/app advertisements in China to UK and UK to China directions.
- Use fixture execution only; no live or paid provider, SDK, credential, network runtime call, or automatic fallback.
- Output is exactly 1600 x 900 PNG using one locked layout template.
- Never send Logo, brand name, UI, statistics, product claims, or long rendered text to `ImageProvider`.
- Preserve Logo, product UI, product name, verified facts, benefit order, CTA action meaning, and layout-template identity.
- Cultural hypotheses remain `pending`; never claim automated cultural, legal, brand, or performance validation.
- The composition endpoint has no body and derives all inputs from trusted stored run state.
- The run remains `in_progress`; public PNG/JSON export, critique, revision, and run completion are Day 13+ work.
- Never expose capability tokens, binary input, local paths, prompt transcripts, credentials, stack traces, or provider output in persistence or public errors.
- Use `apply_patch` for text source edits. Binary font and generated PNG files are created only by the exact verified commands/scripts in this plan.
- Every production behavior follows RED -> observed expected failure -> minimal GREEN -> focused verification -> commit.

---

### Task 1: Contracts, verified font, and constrained fixture image provider

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/cultureshift/contracts.py`
- Create: `src/cultureshift/image_provider.py`
- Modify: `tests/test_contracts.py`
- Create: `tests/test_image_provider.py`
- Create: `assets/fonts/README.md`
- Create: `assets/fonts/NotoSansCJKsc-Regular.otf`
- Create: `assets/fonts/OFL-1.1.txt`
- Modify: `THIRD_PARTY_NOTICES.md`
- Modify: `docs/data/source-policy.md`
- Create: `docs/decisions/ADR-0008-image-provider.md`

**Interfaces:**
- Produces: `BackgroundRequest`, `CompositionLayer`, and `CompositionGenerated` public Pydantic contracts.
- Produces: `GeneratedBackground`, `ImageProvider`, `FixtureImageProvider`, `ImageProviderError`, and `ImageProviderErrorCode`.
- `ImageProvider.generate_background(request: BackgroundRequest) -> GeneratedBackground`.
- `FixtureImageProvider` emits a deterministic 1600 x 900 PNG and `execution_mode=fixture` without network access.

- [ ] **Step 1: Write the failing public-contract tests**

Add focused tests that import the missing Day 12 contracts and prove the public boundary:

```python
def test_composition_generated_requires_fixed_fixture_dimensions(day12_layers) -> None:
    with pytest.raises(ValidationError):
        CompositionGenerated(
            run_id=uuid4(),
            status="in_progress",
            execution_mode="fixture",
            width=1599,
            height=900,
            media_type="image/png",
            rendered_sha256="a" * 64,
            artifact_id=uuid4(),
            layers=day12_layers,
            disclosure="Fixture Demo / 非实时模型",
            generated_at=datetime.now(UTC),
        )


def test_composition_generated_rejects_duplicate_layer_kinds(day12_layers) -> None:
    duplicate = (*day12_layers, day12_layers[0])
    with pytest.raises(ValidationError):
        build_composition_generated(layers=duplicate)
```

Also assert that Logo and product-UI layer evidence requires `source_asset_id`, pixel bounds stay inside 1600 x 900, hashes are lowercase SHA-256, and the disclosure is exactly `Fixture Demo / 非实时模型`.

- [ ] **Step 2: Run the contract tests and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_contracts.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-contract-red
```

Expected: collection fails because `CompositionGenerated` and `CompositionLayer` do not exist.

- [ ] **Step 3: Add the minimal public contracts and generated registry entry**

Use literal/frozen fields for:

```python
class CompositionLayer(ContractModel):
    kind: Literal["background", "product_ui", "logo", "headline", "body", "cta", "disclosure"]
    source_asset_id: UUID | None = None
    rgba_sha256: Sha256
    bounds: tuple[int, int, int, int]
    width: int = Field(ge=1, le=1600)
    height: int = Field(ge=1, le=900)


class CompositionGenerated(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.IN_PROGRESS]
    execution_mode: Literal[ExecutionMode.FIXTURE]
    width: Literal[1600]
    height: Literal[900]
    media_type: Literal["image/png"]
    rendered_sha256: Sha256
    artifact_id: UUID
    layers: tuple[CompositionLayer, ...] = Field(min_length=6, max_length=7)
    disclosure: Literal["Fixture Demo / 非实时模型"]
    generated_at: UtcDatetime
```

Add validators for unique ordered layer kinds, protected source IDs, non-empty bounds, and canvas containment. Register `composition_generated` in `ContractRegistry`.

- [ ] **Step 4: Write the failing provider tests**

Add real-code tests for a wished-for protocol:

```python
@pytest.mark.parametrize("protected", [
    "Orbit AI logo", "brand name", "product UI screenshot", "98%", "claim text",
])
def test_background_request_rejects_protected_content(protected) -> None:
    with pytest.raises(ImageProviderError) as caught:
        FixtureImageProvider().generate_background(background_request(protected))
    assert caught.value.code is ImageProviderErrorCode.INVALID_REQUEST


def test_fixture_provider_is_deterministic_and_offline() -> None:
    first = FixtureImageProvider().generate_background(background_request("quiet workspace"))
    second = FixtureImageProvider().generate_background(background_request("quiet workspace"))
    assert first.png_bytes == second.png_bytes
    assert first.width == 1600 and first.height == 900
    assert first.sha256 == sha256(first.png_bytes).hexdigest()
```

Cover both directions, PNG decode, bounded provenance, and no public serialization of `png_bytes`.

- [ ] **Step 5: Run provider tests and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_image_provider.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-provider-red
```

Expected: collection fails because `cultureshift.image_provider` does not exist.

- [ ] **Step 6: Add Pillow and the minimal provider implementation**

Add `Pillow==12.3.0` to runtime dependencies. Implement:

```python
class ImageProvider(Protocol):
    def generate_background(self, request: BackgroundRequest) -> GeneratedBackground: ...


class FixtureImageProvider:
    def generate_background(self, request: BackgroundRequest) -> GeneratedBackground:
        _validate_background_request(request)
        image = _render_direction_background(request.direction)
        png_bytes = _encode_png(image)
        return GeneratedBackground.from_png(request.direction, png_bytes)
```

The renderer uses fixed colours and geometry only. It does not render copy, Logo, UI, or any protected product term. Provider failures expose only `background_request_invalid` or `background_output_invalid`.

Install the exact new runtime dependency into the isolated Day 12 environment before running GREEN:

```powershell
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pip install Pillow==12.3.0
```

- [ ] **Step 7: Download and verify the exact official font and licence**

Download only these pinned raw URLs:

```text
https://raw.githubusercontent.com/notofonts/noto-cjk/f8d157532fbfaeda587e826d4cd5b21a49186f7c/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf
https://raw.githubusercontent.com/notofonts/noto-cjk/f8d157532fbfaeda587e826d4cd5b21a49186f7c/Sans/LICENSE
```

Load the font with `PIL.ImageFont.truetype`, compute SHA-256 with `Get-FileHash`, and record the exact digest consistently in `assets/fonts/README.md`, `THIRD_PARTY_NOTICES.md`, and `docs/data/source-policy.md`. Copy the complete upstream licence to `assets/fonts/OFL-1.1.txt`. Record `fixture-only` and the no-live-provider boundary in `docs/decisions/ADR-0008-image-provider.md`. Stop without committing if the font, licence, pinned source, or font-load check fails.

- [ ] **Step 8: Verify GREEN and commit**

Run:

```powershell
$env:PYTHONPATH='src'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_contracts.py tests/test_image_provider.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-provider-green
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check src/cultureshift/contracts.py src/cultureshift/image_provider.py tests/test_contracts.py tests/test_image_provider.py
```

Expected: all focused tests and Ruff pass. Commit:

```powershell
git add -- pyproject.toml src/cultureshift/contracts.py src/cultureshift/image_provider.py tests/test_contracts.py tests/test_image_provider.py assets/fonts THIRD_PARTY_NOTICES.md docs/data/source-policy.md docs/decisions/ADR-0008-image-provider.md
git commit -m "feat: add constrained Day 12 image provider"
```

---

### Task 2: Deterministic Pillow compositor and authorized fixture rasters

**Files:**
- Create: `src/cultureshift/composition.py`
- Create: `src/cultureshift/fixture_assets.py`
- Create: `tests/test_composition.py`
- Create: `tests/test_fixture_assets.py`
- Create: `scripts/build_day12_fixture_assets.py`
- Create: `apps/web/public/fixtures/orbit-ai/orbit-ai-logo.png`
- Create: `apps/web/public/fixtures/orbit-ai/orbit-ai-product-ui.png`
- Create: `apps/web/public/fixtures/orbit-ai/composed-china-to-uk.png`
- Create: `apps/web/public/fixtures/orbit-ai/composed-uk-to-china.png`
- Modify: `demo/assets/manifest.json`
- Modify: `demo/assets/RIGHTS.md`

**Interfaces:**
- Consumes: `GeneratedBackground`, confirmed `BrandLock`, immutable `AdCopy`, fixed layout-template ID, and verified font path.
- Produces: `FixtureAssetRegistry.resolve(asset_id: UUID) -> RegisteredFixtureAsset`.
- Produces: `PillowCompositor.compose(request: ComposeRequest) -> ComposedAd`.
- Produces: a deterministic output PNG plus ordered `CompositionLayer` evidence.

- [ ] **Step 1: Write failing closed-registry and compositor tests**

Add tests that establish the requested API before implementation:

```python
def test_fixture_registry_rejects_unregistered_asset_id() -> None:
    with pytest.raises(FixtureAssetError):
        fixture_registry().resolve(uuid4())


def test_compositor_preserves_locked_logo_pixels(compositor, compose_request) -> None:
    result = compositor.compose(compose_request)
    actual = decode_rgba(result.logo_layer_png)
    expected = approved_resize(decode_rgba(compose_request.logo.png_bytes), (220, 96))
    assert actual.size == expected.size
    assert alpha_bounds(actual) == alpha_bounds(expected)
    assert sha256(actual.tobytes()).hexdigest() == sha256(expected.tobytes()).hexdigest()
    assert result.layers_by_kind["logo"].source_asset_id == compose_request.brand_lock.logo_asset_id
```

Add the equivalent product-UI assertion; a missing registered UI must raise `locked_asset_missing`, never synthesize a replacement. Assert exact 1600 x 900 output, stable z-order, deterministic bytes, and matching CTA action meaning.

- [ ] **Step 2: Add bilingual glyph and rendered-output RED tests**

For every unique character in both fixture headline/body/CTA/disclosure strings, assert the pinned font returns a non-empty glyph mask. Render both directions and assert non-transparent text-layer bounds without tofu replacement or a system-font fallback.

Run:

```powershell
$env:PYTHONPATH='src'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_fixture_assets.py tests/test_composition.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-compositor-red
```

Expected: collection fails because the registry and compositor modules do not exist.

- [ ] **Step 3: Implement the closed fixture registry and fixed compositor**

Implement focused immutable dataclasses:

```python
@dataclass(frozen=True)
class ComposeRequest:
    run_id: UUID
    background: GeneratedBackground
    brand_lock: BrandLock
    ad_copy: AdCopy
    logo: RegisteredFixtureAsset
    product_ui: RegisteredFixtureAsset
    font_path: Path


class PillowCompositor:
    def compose(self, request: ComposeRequest) -> ComposedAd:
        _validate_locked_inputs(request)
        layers = _render_fixed_layers(request)
        output = _flatten_layers(layers, size=(1600, 900))
        return _build_composed_ad(output, layers)
```

Use `Image.Resampling.LANCZOS`, RGBA layers, fixed semantic rectangles, a single font, bounded font sizes, and deterministic PNG encoding. Do not accept client coordinates or arbitrary paths.

- [ ] **Step 4: Generate authorized PNG derivatives and bilateral previews**

`scripts/build_day12_fixture_assets.py` must create the two locked raster inputs from project-owned fixture geometry, invoke the real provider and compositor for both directions, and refuse overwrite when its computed metadata does not match the fixture definitions. Add each generated PNG to `demo/assets/manifest.json` with exact SHA-256, source SVG provenance where applicable, `rights_status=cleared`, and explicit derivative/public-display permissions. Update `demo/assets/RIGHTS.md` without fabricating external ownership.

- [ ] **Step 5: Verify GREEN, reproducibility, and commit**

Run the asset builder twice and assert unchanged SHA-256 values and a clean second Git diff. Then run:

```powershell
$env:PYTHONPATH='src'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_fixture_assets.py tests/test_composition.py tests/test_validate_demo_manifest.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-compositor-green
..\day8-analysis-foundation\.venv\Scripts\python.exe scripts/validate_demo_manifest.py demo/assets/manifest.json
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check src/cultureshift/composition.py src/cultureshift/fixture_assets.py tests/test_composition.py tests/test_fixture_assets.py scripts/build_day12_fixture_assets.py
```

Expected: all checks pass and the manifest reports `demo asset manifest is valid`. Commit:

```powershell
git add -- src/cultureshift/composition.py src/cultureshift/fixture_assets.py tests/test_composition.py tests/test_fixture_assets.py scripts/build_day12_fixture_assets.py apps/web/public/fixtures/orbit-ai/*.png demo/assets/manifest.json demo/assets/RIGHTS.md
git commit -m "feat: compose deterministic Day 12 fixture ads"
```

---

### Task 3: Immutable composition storage and authenticated API orchestration

**Files:**
- Create: `src/cultureshift/composition_service.py`
- Create: `src/cultureshift/composition_storage.py`
- Modify: `src/cultureshift/repository.py`
- Modify: `src/cultureshift/app.py`
- Create: `tests/test_composition_storage.py`
- Modify: `tests/test_repository.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: trusted stored run/request/analysis/confirmation/draft, fixture provider, fixture registry, and compositor.
- Produces: `CompositionArtifactStore.save(artifact_id: UUID, png_bytes: bytes, expires_at: datetime) -> StoredCompositionArtifact`.
- Produces: `CompositionService.generate(run_id: UUID) -> CompositionGenerated`.
- Produces: bodyless authenticated `POST /api/v1/runs/{run_id}/composition`.

- [ ] **Step 1: Write failing storage and migration tests**

Add a legacy-schema migration test requiring nullable composition metadata columns. Add storage tests for exclusive creation, SHA-256 verification, a 10 MiB ceiling, opaque IDs, 24-hour TTL, expired/missing read refusal, and removal of partial files after failure.

```python
def test_repository_saves_and_replays_one_immutable_composition(repository, ready_run) -> None:
    first = repository.save_composition(ready_run.id, composition_summary())
    replay = repository.save_composition(ready_run.id, composition_summary())
    assert replay == first
    with pytest.raises(CompositionImmutableError):
        repository.save_composition(ready_run.id, changed_composition_summary())
```

- [ ] **Step 2: Run storage tests and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_composition_storage.py tests/test_repository.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-storage-red
```

Expected: collection fails because the store and repository composition methods do not exist.

- [ ] **Step 3: Implement minimal TTL storage and atomic repository metadata**

Write PNG bytes with exclusive `.part` files, `fsync`, SHA-256 verification, atomic replace, bounded metadata, and no public paths. Extend the existing SQLite migration and `BEGIN IMMEDIATE` pattern with canonical `composition_json` storage. Require `in_progress`, confirmed Brand Lock, and stored draft; replay exact metadata; reject drift or partial state.

- [ ] **Step 4: Write the failing service and API tests**

Add API tests proving:

```python
def test_composition_endpoint_is_bodyless_authenticated_and_idempotent(client, ready_run) -> None:
    first = client.post(f"/api/v1/runs/{ready_run.id}/composition", headers=update_auth(ready_run))
    second = client.post(f"/api/v1/runs/{ready_run.id}/composition", headers=update_auth(ready_run))
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["status"] == "in_progress"
    assert first.json()["width"] == 1600
    assert "path" not in json.dumps(first.json()).lower()
```

Cover missing/wrong capability, cross-run subject, absent analysis/confirmation/draft, non-fixture run, invalid state, provider/compositor/storage failure, request-body rejection, and sanitized stable codes.

- [ ] **Step 5: Run API tests and verify RED**

Run:

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='D:\create\Diversity\.day12-api-assets'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_app.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-api-red
```

Expected: route returns 404 or `create_app` rejects the missing Day 12 dependencies.

- [ ] **Step 6: Implement the minimal service and API route**

Add injected provider/registry/compositor/artifact-store dependencies to `create_app`. `CompositionService` must derive direction, Brand Lock, copy, and asset IDs from the repository, validate the output before storage, remove a just-written artifact if metadata persistence fails, and return exact replay metadata. Map internal errors only to the stable codes in the specification.

- [ ] **Step 7: Verify GREEN and commit**

Run:

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='D:\create\Diversity\.day12-api-assets'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest tests/test_composition_storage.py tests/test_repository.py tests/test_app.py -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-api-green
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check src/cultureshift tests/test_composition_storage.py tests/test_repository.py tests/test_app.py
```

Expected: all focused tests and Ruff pass. Commit:

```powershell
git add -- src/cultureshift/composition_service.py src/cultureshift/composition_storage.py src/cultureshift/repository.py src/cultureshift/app.py tests/test_composition_storage.py tests/test_repository.py tests/test_app.py
git commit -m "feat: persist and serve Day 12 compositions"
```

---

### Task 4: Bilateral fixture composition evidence in the Web result pages

**Files:**
- Modify: `apps/web/src/fixtures/types.ts`
- Modify: `apps/web/src/fixtures/fixture-validation.ts`
- Modify: `apps/web/src/fixtures/fixture-loader.test.ts`
- Modify: `apps/web/src/fixtures/data/china-to-uk.json`
- Modify: `apps/web/src/fixtures/data/uk-to-china.json`
- Modify: `apps/web/src/results/compose-fixture-result.ts`
- Modify: `apps/web/src/results/compose-fixture-result.test.ts`
- Create: `apps/web/src/components/composition-evidence.tsx`
- Create: `apps/web/src/components/composition-evidence.module.css`
- Create: `apps/web/src/components/composition-evidence.test.tsx`
- Modify: `apps/web/src/app/results/[fixtureId]/page.tsx`
- Modify: `apps/web/src/app/results/[fixtureId]/page.test.tsx`

**Interfaces:**
- Consumes: generated `CompositionGenerated` TypeScript contract and committed bilateral preview PNGs.
- Produces: typed `FixtureBundle.composition` data and `<CompositionEvidence composition={...} />`.

- [ ] **Step 1: Write failing fixture and component tests**

Require both fixtures to expose exact 1600 x 900 dimensions, fixture mode, preview path, output SHA-256, fixed ordered layers, protected source IDs, pinned font commit, disclosure, and limitation. Add component assertions:

```tsx
expect(screen.getByRole("heading", { name: /Deterministic composition|确定性合成/ })).toBeVisible();
expect(screen.getByRole("img", { name: /1600 x 900 fixture composition/ })).toBeVisible();
expect(screen.getByText("Fixture Demo / 非实时模型")).toBeVisible();
expect(screen.getByText(/NotoSansCJKsc-Regular\.otf/)).toBeVisible();
expect(screen.getByText(/human review|required|人工复核/i)).toBeVisible();
```

Assert the UI does not contain `live model`, `culturally validated`, `approved for production`, a local path, or a capability value.

- [ ] **Step 2: Run Web tests and verify RED**

Run:

```powershell
npm.cmd --prefix apps/web test -- composition-evidence fixture-loader compose-fixture-result page
```

Expected: import or fixture validation fails because `composition` evidence does not exist.

- [ ] **Step 3: Add strict fixture validation and the evidence component**

Extend the typed fixture boundary without duplicating generated public contracts. Validation must require exact direction/locale/Brand Lock asset IDs, recompute the committed preview SHA-256 in the fixture build/test path, require the fixed z-order, and reject extra fields. Render a real `<img>` preview plus compact definition-list evidence for dimensions, output hash, layer sources, font provenance, and fixture limitations.

- [ ] **Step 4: Refresh generated contracts and verify GREEN**

Run:

```powershell
python scripts/export_contracts.py
npm.cmd --prefix apps/web run contracts:generate
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
```

Expected: contract freshness, all Web tests, typecheck, and lint pass.

- [ ] **Step 5: Commit the Web evidence slice**

```powershell
git add -- contracts apps/web/src apps/web/public/fixtures/orbit-ai/*.png
git commit -m "feat: show Day 12 composition evidence"
```

---

### Task 5: Complete verification, Day12.docx, and authorized publication

**Files:**
- Create locally, outside Git: `D:/create/Diversity/Day12.docx`
- Use retained template: `D:/create/Diversity/Day11.docx`
- No repository source changes unless a verification failure receives a focused RED regression first.

**Interfaces:**
- Consumes: the final Day 12 branch tree and all test evidence.
- Produces: a verified local daily record and a non-force fast-forward update of GitHub `main`.

- [ ] **Step 1: Run focused and full Python verification**

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='D:\create\Diversity\.day12-final-assets'
..\day8-analysis-foundation\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp D:\create\Diversity\.day12-final-pytest
..\day8-analysis-foundation\.venv\Scripts\ruff.exe check .
```

Read the full output and require zero failures/errors.

- [ ] **Step 2: Run contract, Web, dependency, manifest, and public-boundary gates**

```powershell
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run build -- --webpack
npm.cmd --prefix apps/web audit --audit-level=high
..\day8-analysis-foundation\.venv\Scripts\python.exe scripts/validate_demo_manifest.py demo/assets/manifest.json
& scripts/verify-public-boundary.ps1
git diff --check origin/main...HEAD
```

Require zero test failures, build exit 0, zero high vulnerabilities, a valid manifest, a clean public-boundary scan, and no whitespace errors.

- [ ] **Step 3: Perform an independent specification and code-quality review**

Re-read Issue #11 and the design acceptance criteria line by line. Inspect `git diff --stat origin/main...HEAD`, every changed public contract, API route, persistence boundary, generated asset hash, fixture disclosure, and error mapping. Add a real failing regression test before any review-driven production fix, then rerun the affected focused suite and the complete gates.

- [ ] **Step 4: Create and visually verify Day12.docx**

Use the Documents skill and the retained `Day11.docx` template. Preserve section geometry, styles, tables, header/footer, bilingual headings, and daily-record structure. Record Person A and Person B requirements, implementation commits, provider/font provenance, TDD RED/GREEN evidence, exact test counts, security/audit results, Issue #11, limitations, final commit/tree, and publication result. Render the latest document with the packaged renderer, inspect every page PNG at 100%, fix visible clipping/overlap/glyph issues, then run structural, style, accessibility, and privacy checks. If LibreOffice is unavailable, document the structural fallback rather than claiming PNG review.

- [ ] **Step 5: Commit final evidence if needed and verify the exact publication tree**

Require `git status --porcelain -uall` to be empty and capture `HEAD` plus `HEAD^{tree}`. Test `github.com` and `api.github.com`, fetch `origin/main`, and compare its commit with the recorded Day 11 baseline `f684fe80b0cf3e5795863a146ef64775fb133812`. If remote moved, inspect and integrate the partner commits without force or overwrite, then rerun verification on the integrated tree.

- [ ] **Step 6: Push by the previously verified route and confirm CI**

Attempt the normal non-force fast-forward push first:

```powershell
git -c safe.directory=D:/create/Diversity/cultureshift/.worktrees/day9-analysis-execution push origin HEAD:main
```

If GitHub network reset occurs, switch immediately to the already verified authenticated GitHub API commit/tree/ref path; do not repeatedly retry browser upload. Never force-update `main`. After publication, read the remote ref/tree and require exact equality with local `HEAD`/tree. Wait for the corresponding GitHub Actions run and require `completed/success` before reporting completion.
