# Day 8 Analysis Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic provider-neutral multimodal analysis foundation,
record a dated live-provider deferral decision, and complete the public-safe
reviewer-recruitment handoff.

**Architecture:** Keep the vendor boundary in `analysis_provider.py` and the
orchestration/safety boundary in `analysis_pipeline.py`. The provider may return
only candidate analysis fields; the pipeline copies the trusted source asset and
Brand Lock into the existing public `AdAnalysis`. Provider research remains
documentation-only and real recruitment remains inactive.

**Tech Stack:** Python 3.11+; Pydantic 2; stdlib `Protocol` and dataclasses;
pytest; Ruff; existing JSON Schema/TypeScript generators; Markdown and JSON.

## Global Constraints

- GitHub Issue #7 contains the accepted specification and acceptance criteria:
  https://github.com/Yvonne-wyx/cultureshift/issues/7
- Do not add a runtime dependency, provider SDK, credential, network call, paid
  API call, or provider account configuration.
- Do not add `/analyze`, repair/retry behavior, job execution, persistence, or a
  run-state transition; those belong to Day 9.
- Never log or persist private image bytes, extracted text, prompts, provider
  payloads, local paths, capability tokens, personal data, or raw exceptions.
- Preserve Brand Lock and `source_asset` by copying them only from the trusted
  request, never from provider output.
- Keep every `CulturalHypothesis` pending, traceable, direction-correct, and
  explicitly hypothetical.
- Keep recruitment at `pending_human_activation`, `opened_at: null`, and
  `real_reviewers_confirmed: 0`.
- Limit implementation to static ads for AI software/applications in
  China-to-UK and UK-to-China directions.

---

## File map

- Create `src/cultureshift/analysis_provider.py`: internal provider request,
  closed provider result, `VisionProvider`, and deterministic `FakeProvider`.
- Create `src/cultureshift/analysis_pipeline.py`: stable error codes,
  `SafetyGate`, and `AnalysisPipeline` orchestration.
- Modify `src/cultureshift/asset_storage.py`: expose the existing signature
  detector as `detect_media_type` so upload and analysis share one rule.
- Create `tests/test_analysis_provider.py`: provider protocol and deterministic
  fixture behavior.
- Create `tests/test_analysis_pipeline.py`: preflight, postflight, privacy, and
  Brand Lock invariants.
- Create `docs/research/vision-provider-comparison-2026-08-16.json`: dated,
  machine-readable official-source comparison.
- Create `docs/decisions/ADR-0007-vision-provider-selection.md`: approve only the
  fake provider and defer live selection.
- Modify `docs/evaluation/recruitment-pack-v0.1.md`: Day 8 human handoff.
- Create `docs/evaluation/recruitment-handoff-v0.1.json`: machine-readable Day 8
  activation boundary.
- Create `tests/test_provider_research.py`: parsed comparison structure and
  source coverage.
- Modify `tests/test_evaluation_protocol.py`: recruitment status and handoff
  truthfulness.

### Task 1: Provider contract and deterministic fake

**Files:**

- Create: `src/cultureshift/analysis_provider.py`
- Create: `tests/test_analysis_provider.py`

**Interfaces:**

- Consumes: `SourceAdAssetRef`, `BrandLock`, `CulturalHypothesis`, `Locale`,
  `WarningCode`, and `LocalizationDirection`.
- Produces:
  `VisionAnalysisRequest`, `VisionProviderResult`, `VisionProvider`, and
  `FakeProvider.analyze(request) -> VisionProviderResult | Mapping[str, object]`.

- [ ] **Step 0: Prepare the isolated Python environment**

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Expected: the worktree has its own ignored `.venv`, imports resolve from the
current Day 8 `src`, and no project dependency file changes.

- [ ] **Step 1: Write failing provider tests**

Create `tests/test_analysis_provider.py` with a reusable trusted request and
these explicit checks:

```python
def test_fake_provider_is_deterministic_and_does_not_derive_from_private_bytes(
    analysis_request,
) -> None:
    result = VisionProviderResult(
        detected_locale=Locale.ZH_CN,
        hypotheses=(),
        warnings=("fixture_provider",),
    )
    provider = FakeProvider(result)

    first = provider.analyze(analysis_request)
    second = provider.analyze(
        replace(analysis_request, content=b"\x89PNG\r\n\x1a\nanother-fixture")
    )

    assert first == second == result
    assert provider.call_count == 2
```

Also assert that `VisionProviderResult` rejects extra fields and that a class
implementing `analyze` satisfies `VisionProvider` under `@runtime_checkable`.

- [ ] **Step 2: Run RED**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_analysis_provider.py -q
```

Expected: collection fails with `ModuleNotFoundError` for
`cultureshift.analysis_provider`.

- [ ] **Step 3: Implement the minimal provider boundary**

Create `src/cultureshift/analysis_provider.py` with these exact shapes:

```python
@dataclass(frozen=True, slots=True)
class VisionAnalysisRequest:
    content: bytes
    source_asset: SourceAdAssetRef
    direction: LocalizationDirection
    brand_lock: BrandLock
    product_category: Literal["ai_software", "ai_application"]
    creative_format: Literal["static_ad"] = "static_ad"


class VisionProviderResult(ContractModel):
    detected_locale: Locale
    hypotheses: tuple[CulturalHypothesis, ...] = Field(default=(), max_length=32)
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    instruction_like_content_detected: bool = False
    prohibited_content_detected: bool = False


@runtime_checkable
class VisionProvider(Protocol):
    def analyze(
        self, request: VisionAnalysisRequest
    ) -> VisionProviderResult | Mapping[str, object]: ...
```

`FakeProvider` stores one already validated `VisionProviderResult`, increments a
read-only `call_count`, ignores `request.content`, and returns the configured
result. It performs no I/O and contains no vendor name.

- [ ] **Step 4: Run GREEN and Ruff**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_analysis_provider.py -q
.venv\Scripts\python.exe -m ruff check src/cultureshift/analysis_provider.py tests/test_analysis_provider.py
```

Expected: all focused tests pass and Ruff reports `All checks passed!`.

- [ ] **Step 5: Commit Task 1**

```powershell
git add src/cultureshift/analysis_provider.py tests/test_analysis_provider.py
git commit -m "feat: define deterministic vision provider boundary"
```

### Task 2: Safety gate and analysis pipeline

**Files:**

- Modify: `src/cultureshift/asset_storage.py`
- Create: `src/cultureshift/analysis_pipeline.py`
- Create: `tests/test_analysis_pipeline.py`
- Modify: `tests/test_asset_storage.py`

**Interfaces:**

- Consumes: every Task 1 interface plus existing `AdAnalysis` and `Market`.
- Produces:
  `detect_media_type(data: bytes) -> str | None`,
  `AnalysisPipelineError.code: AnalysisErrorCode`,
  `SafetyGate.validate_request(request, now)`,
  `SafetyGate.validate_result(request, result)`, and
  `AnalysisPipeline.analyze(request) -> AdAnalysis`.

- [ ] **Step 1: Write failing pipeline and shared-signature tests**

Create table-driven tests for these exact error codes:

```python
@pytest.mark.parametrize(
    ("request_change", "expected_code"),
    [
        ({"content": b""}, "invalid_analysis_input"),
        ({"content": b"not-a-png"}, "invalid_analysis_input"),
        ({"product_category": "medical"}, "unsupported_analysis_scope"),
        ({"creative_format": "video"}, "unsupported_analysis_scope"),
    ],
)
def test_preflight_blocks_before_provider(request_change, expected_code, valid_request):
    provider = RecordingProvider(_safe_result())
    with pytest.raises(AnalysisPipelineError) as caught:
        AnalysisPipeline(provider).analyze(replace(valid_request, **request_change))
    assert caught.value.code == expected_code
    assert provider.call_count == 0
```

Add separate tests for expired assets, provider exceptions, malformed mappings,
instruction-like content, prohibited content, wrong target market, non-pending
hypotheses, and safe bilateral success. On success assert:

```python
assert analysis.source_asset is request.source_asset
assert analysis.brand_lock is request.brand_lock
assert analysis.hypotheses == provider_result.hypotheses
```

Add one regression proving errors contain none of the private byte marker,
`C:\private\source.png`, rejected claim text, or provider exception text. Add a
small asset-storage regression proving upload validation and analysis both use
`detect_media_type` for PNG and JPEG.

- [ ] **Step 2: Run RED**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_analysis_pipeline.py tests/test_asset_storage.py -q
```

Expected: import fails because `analysis_pipeline` and public
`detect_media_type` do not exist.

- [ ] **Step 3: Expose the existing media detector**

Rename `_detected_media_type` to `detect_media_type` in
`asset_storage.py` and update the existing `TemporaryAssetStore.store` call.
Do not change accepted signatures or file lifecycle behavior.

- [ ] **Step 4: Implement stable errors and SafetyGate**

Use an enum and code-only exception:

```python
class AnalysisErrorCode(StrEnum):
    INVALID_INPUT = "invalid_analysis_input"
    UNSUPPORTED_SCOPE = "unsupported_analysis_scope"
    ASSET_CLOSED = "asset_lifecycle_closed"
    PROVIDER_FAILED = "provider_failed"
    PROVIDER_OUTPUT_INVALID = "provider_output_invalid"
    INSTRUCTION_LIKE_CONTENT = "instruction_like_content"
    PROHIBITED_CONTENT = "prohibited_content"
    UNSAFE_HYPOTHESIS = "unsafe_hypothesis"


class AnalysisPipelineError(RuntimeError):
    def __init__(self, code: AnalysisErrorCode) -> None:
        self.code = code
        super().__init__(code.value)
```

`SafetyGate.validate_request` must compare `detect_media_type(content)` with
`source_asset.media_type`, enforce PNG/JPEG, require non-expired assets, and
accept only the two product categories plus `static_ad`.

`SafetyGate.validate_result` must reject either safety boolean, require every
hypothesis to be `pending`, and map target market exactly:

```python
expected_market = {
    LocalizationDirection.CHINA_TO_UK: Market.UNITED_KINGDOM,
    LocalizationDirection.UK_TO_CHINA: Market.CHINA,
}[request.direction]
```

- [ ] **Step 5: Implement AnalysisPipeline without leaking provider errors**

```python
def analyze(self, request: VisionAnalysisRequest) -> AdAnalysis:
    self._gate.validate_request(request, now=self._now())
    try:
        raw_result = self._provider.analyze(request)
    except Exception:
        raise AnalysisPipelineError(AnalysisErrorCode.PROVIDER_FAILED) from None
    try:
        result = VisionProviderResult.model_validate(raw_result)
    except ValidationError:
        raise AnalysisPipelineError(
            AnalysisErrorCode.PROVIDER_OUTPUT_INVALID
        ) from None
    self._gate.validate_result(request, result)
    return AdAnalysis(
        source_asset=request.source_asset,
        detected_locale=result.detected_locale,
        brand_lock=request.brand_lock,
        hypotheses=result.hypotheses,
        warnings=result.warnings,
    )
```

Do not add logging, persistence, FastAPI routes, retries, or fallback providers.

- [ ] **Step 6: Run focused GREEN and Ruff**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_analysis_provider.py tests/test_analysis_pipeline.py tests/test_asset_storage.py -q
.venv\Scripts\python.exe -m ruff check src/cultureshift/analysis_provider.py src/cultureshift/analysis_pipeline.py src/cultureshift/asset_storage.py tests/test_analysis_provider.py tests/test_analysis_pipeline.py tests/test_asset_storage.py
```

Expected: all focused tests pass and Ruff is clean.

- [ ] **Step 7: Commit Task 2**

```powershell
git add src/cultureshift/analysis_pipeline.py src/cultureshift/asset_storage.py tests/test_analysis_pipeline.py tests/test_asset_storage.py
git commit -m "feat: add safe fixture analysis pipeline"
```

### Task 3: Provider ADR and truthful recruitment handoff

**Files:**

- Create: `docs/research/vision-provider-comparison-2026-08-16.json`
- Create: `docs/decisions/ADR-0007-vision-provider-selection.md`
- Modify: `docs/evaluation/recruitment-pack-v0.1.md`
- Create: `docs/evaluation/recruitment-handoff-v0.1.json`
- Create: `tests/test_provider_research.py`
- Modify: `tests/test_evaluation_protocol.py`

**Interfaces:**

- Consumes: the accepted design's eight official URLs and the existing
  `recruitment-status.json` exact object.
- Produces: a dated machine-readable comparison, an accepted ADR that approves
  only `FakeProvider`, and a six-item machine-readable human activation handoff.

- [ ] **Step 1: Write failing documentation-structure tests**

Create `tests/test_provider_research.py` to parse the comparison JSON and
require:

```python
def test_provider_comparison_uses_official_sources_and_required_dimensions():
    comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
    assert comparison["accessed_at"] == "2026-08-16"
    assert comparison["decision"] == "no_live_provider_approved"
    assert {item["provider"] for item in comparison["providers"]} == {
        "OpenAI API",
        "Google Vertex AI",
        "Amazon Bedrock",
    }
    assert all(
        set(item["dimensions"]) == REQUIRED_DIMENSIONS
        for item in comparison["providers"]
    )
    assert all(
        source.startswith("https://")
        for item in comparison["providers"]
        for source in item["sources"]
    )
```

Require all eight approved official URLs through parsed `sources` arrays. Extend
the evaluation test to parse `recruitment-handoff-v0.1.json`, require the exact
inactive status values and six stable requirement identifiers, and keep the
existing `recruitment-status.json` exact object unchanged. Do not test ADR or
recruitment-pack prose by matching human sentences.

- [ ] **Step 2: Run RED**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_provider_research.py tests/test_evaluation_protocol.py -q
```

Expected: `FileNotFoundError` for the comparison or handoff JSON.

- [ ] **Step 3: Write the dated comparison**

Use a compact JSON document. Every provider has the same six dimension keys;
each dimension separates `verified` official statements from project
`inference`. Include `accessed_at: 2026-08-16` and direct official source URLs.
Record pricing as a dated unit/model description plus the rule “refresh before
procurement”; do not promise a future price or rank vendors by an unmeasured
score.

- [ ] **Step 4: Write ADR-0007**

Use sections `Status`, `Context`, `Decision`, `Approval gates`, and
`Consequences`. Decision text must approve only `FakeProvider` for fixture
development/CI and state that OpenAI API, Google Vertex AI, and Amazon Bedrock
remain unapproved candidates. Approval gates are:

1. named privacy owner;
2. explicit processing-region requirement;
3. verified retention/zero-retention configuration;
4. budget owner;
5. dated price refresh;
6. separate implementation approval.

- [ ] **Step 5: Extend recruitment handoff without changing status**

Create `recruitment-handoff-v0.1.json` with the exact inactive status values and
stable identifiers for named human coordinator, approved private contact route,
protected consent vault, approved privacy/retention notice,
withdrawal/deletion owner, and private assignment/response store. Add a matching
`## Day 8 human activation handoff` checklist to the recruitment pack and state
that no outreach starts and no personal data is committed until all requirements
are satisfied. Manually review the prose; tests validate the JSON behavior.

- [ ] **Step 6: Run GREEN and Ruff**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_provider_research.py tests/test_evaluation_protocol.py -q
.venv\Scripts\python.exe -m ruff check tests/test_provider_research.py tests/test_evaluation_protocol.py
```

Expected: focused tests pass; recruitment status remains exactly unchanged.

- [ ] **Step 7: Commit Task 3**

```powershell
git add docs/research/vision-provider-comparison-2026-08-16.json docs/decisions/ADR-0007-vision-provider-selection.md docs/evaluation/recruitment-pack-v0.1.md docs/evaluation/recruitment-handoff-v0.1.json tests/test_provider_research.py tests/test_evaluation_protocol.py
git commit -m "docs: record Day 8 provider and recruitment decision"
```

### Task 4: Convergence and local Day 8 record

**Files:**

- Verify only: repository tracked files
- Create outside repository after all gates: workspace-parent `Day8.docx`

**Interfaces:**

- Consumes: all Task 1-3 outputs and existing repository verification commands.
- Produces: one clean Day 8 branch, verified evidence, and a local record that
  follows the Day 7 DOCX template.

- [ ] **Step 0: Reuse the verified web dependency tree without reinstalling**

Verify that the sibling Day 7 worktree's `apps/web/node_modules` exists. If
`apps/web/node_modules` is absent, create a Windows junction to that verified
target. Confirm `git status --short` does not list the junction because
`node_modules` is ignored. Do not run `npm install` or change the lockfile.

- [ ] **Step 1: Run the complete Python and contract gates once**

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
```

Expected: all Python tests pass, Ruff is clean, and generated contracts are
current. Day 8 should not change public schema output.

- [ ] **Step 2: Run web/build/security gates once**

```powershell
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run build -- --webpack
npm.cmd --prefix apps/web audit --audit-level=high
```

Expected: Vitest, typecheck, lint, webpack production build, and audit pass. Use
the webpack path because the local worktree reuses `node_modules` through a
junction; CI still exercises a normal checkout.

- [ ] **Step 3: Run repository and public-boundary gates**

```powershell
.venv\Scripts\python.exe scripts/validate_demo_manifest.py demo/assets/manifest.json
powershell -ExecutionPolicy Bypass -File scripts/check_public_boundary.ps1
git diff --check main...HEAD
git status --short
```

Expected: manifest valid, public-boundary scan passes, no whitespace errors, and
no uncommitted repository changes.

- [ ] **Step 4: Generate and structurally verify Day8.docx**

Use the workspace-parent `Day7.docx` as the retained template. Record the Issue,
local commits, RED/GREEN evidence, exact final gate counts, the no-live-provider
decision, and unchanged recruitment status. Run the canonical document render;
if LibreOffice is unavailable, record that exception and run section, style,
OOXML preserve-only, placeholder, and accessibility audits instead.

- [ ] **Step 5: Finish without unauthorized remote writes**

Confirm the branch is clean and report the local commit(s). Do not push, merge,
create a PR, close the Issue, or mutate GitHub until the user gives a separate
explicit authorization for that action.
