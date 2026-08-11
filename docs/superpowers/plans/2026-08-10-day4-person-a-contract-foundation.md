# Day 4 Person A Contract Foundation Implementation Plan

> **Security erratum (2026-08-11):** Wherever this historical plan pins Next.js
> or eslint-config-next 16.2.11, use 16.3.0 instead. This narrowly supersedes the
> affected pins after high-severity transitive PostCSS and Sharp advisories; all
> other versions and steps remain unchanged.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Day 4 Person A contract foundation from Issue #3: validated Pydantic contracts, deterministic JSON Schema, generated TypeScript declarations, a minimal run-creation API, a Next.js test toolchain, and CI freshness checks.

**Architecture:** Preserve the existing root Python package and SQLite repository. Add one focused public-contract module, generate a committed JSON Schema bundle from a registry model, compile that bundle into committed TypeScript, and make FastAPI, tests, and the web workspace consume those contracts. Keep capability enforcement, restart recovery, full integration, and Person B fixture rendering outside this plan.

**Tech Stack:** Python 3.13.5 in CI, FastAPI, Pydantic 2, SQLite, Pytest, Ruff, Node.js 24.18.0, Next.js 16.2.11, TypeScript, Vitest 4.1.10, Testing Library React 16.3.2, Testing Library DOM 10.4.1, jest-dom 7.0.0, jsdom 30.0.1, Playwright 1.61.1, json-schema-to-typescript 15.0.4, GitHub Actions.

## Global Constraints

- Work against GitHub Issue [#3](https://github.com/Yvonne-wyx/cultureshift/issues/3) and preserve all unrelated changes.
- Keep the backend under `src/cultureshift`; do not create a `services/api` migration.
- Support only static advertising for AI software/apps in `china_to_uk` and `uk_to_china` directions.
- Permit only `static_ad`, `ai_software`, and `ai_application` request values.
- Treat Pydantic models as the only hand-maintained contract source; JSON Schema and TypeScript are generated artifacts.
- Preserve Brand Lock: logo, product name, verified facts, real UI, benefit order, CTA action meaning, and layout template.
- Permit localization only for narrative, use scenario, trust information, and language.
- Represent cultural inference only as `CulturalHypothesis`; never claim automated cultural validation.
- Reject unknown fields, unsupported scope, missing rights/provenance references, and live execution on Day 4.
- Never log or commit secrets, capability tokens, private content, local absolute paths, PII, or unauthorized assets.
- Use Node.js 24.18.0 and the exact JavaScript tool versions listed in the Tech Stack; record all resolved versions in `apps/web/package-lock.json`.
- Day 5 capability enforcement, authenticated retrieval, restart recovery, and full integration are explicitly excluded.

---

## File map

- Create `src/cultureshift/contracts.py`: public enums, value models, artifact models, API models, and `ContractRegistry`.
- Create `tests/conftest.py`: one authorized synthetic request payload shared by contract and API tests.
- Create `tests/test_contracts.py`: Pydantic validation and serialization tests.
- Create `src/cultureshift/schema_export.py`: deterministic rendering, writing, and freshness checking.
- Create `scripts/export_contracts.py`: CLI for write and `--check` modes.
- Create `tests/test_schema_export.py`: deterministic and stale-artifact tests.
- Create `contracts/json-schema/cultureshift.contracts.schema.json`: generated contract bundle.
- Modify `src/cultureshift/app.py`: healthz and injected run-creation API.
- Modify `tests/test_app.py`: API, OpenAPI, 422, generic 500, and non-persistence tests.
- Create `apps/web/*`: minimal Next.js App Router workspace and npm lockfile.
- Create `apps/web/src/app/page.test.tsx`: web smoke test.
- Create `apps/web/vitest.config.ts` and `apps/web/src/test/setup.ts`: deterministic DOM test setup.
- Create `apps/web/scripts/generate-contracts.mjs`: TypeScript generation and freshness check.
- Create `apps/web/scripts/generate-contracts.test.mjs`: stale TypeScript detection test.
- Create `apps/web/src/generated/contracts.ts`: generated declarations.
- Create `apps/web/src/generated/contracts.test.ts`: generated-type compilation smoke test.
- Create `.github/workflows/ci.yml`: backend, contracts/web, and public-boundary jobs.
- Create `tests/test_ci_workflow.py`: executable assertion that required CI gates remain present.

---

### Task 1: Public contract vocabulary and safe shared models

**Files:**
- Create: `src/cultureshift/contracts.py`
- Create: `tests/conftest.py`
- Create: `tests/test_contracts.py`

**Interfaces:**
- Consumes: `cultureshift.domain.LocalizationDirection` and the approved Brand Lock/CulturalHypothesis boundaries.
- Produces: `Market`, `Locale`, `ExecutionMode`, `AssetKind`, `RunStatus`, `AssetRef`, `CulturalHypothesis`, `BrandLock`, `ContractModel`, and shared constrained-string aliases.

- [ ] **Step 1: Reconfirm the issue, repository rules, and clean baseline**

Run:

```powershell
git status --short --branch
python -m pytest -q
python -m ruff check .
```

Expected: branch is `main`, only the approved design/plan commits are ahead of `origin/main`, the existing suite passes, and Ruff reports no violations.

- [ ] **Step 2: Add the synthetic request fixture and failing shared-model tests**

Create `tests/conftest.py`:

```python
from typing import Any

import pytest


@pytest.fixture
def valid_run_payload() -> dict[str, Any]:
    return {
        "direction": "china_to_uk",
        "execution_mode": "fixture",
        "product_category": "ai_application",
        "creative_format": "static_ad",
        "source_asset": {
            "asset_id": "11111111-1111-4111-8111-111111111111",
            "kind": "source_ad",
            "media_type": "image/png",
            "sha256": "a" * 64,
            "provenance_ref": "fixture:ai-app/source-ad",
            "rights_ref": "rights:fixture-synthetic-v1",
        },
        "brand_lock": {
            "logo_asset_id": "22222222-2222-4222-8222-222222222222",
            "product_name": "Orbit AI",
            "verified_product_facts": ["Turns approved notes into task summaries"],
            "product_ui_asset_ids": ["33333333-3333-4333-8333-333333333333"],
            "benefit_order": ["Summarize", "Organize"],
            "cta_action_meaning": "Start a fixture demo",
            "layout_template_asset_id": "44444444-4444-4444-8444-444444444444",
            "localizable_fields": [
                "narrative",
                "use_scenario",
                "trust_information",
                "language",
            ],
        },
    }
```

Create the first part of `tests/test_contracts.py`:

```python
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cultureshift.contracts import (
    AssetKind,
    AssetRef,
    BrandLock,
    CulturalHypothesis,
    ExecutionMode,
    Locale,
    Market,
    RunStatus,
)


def test_contract_enums_have_stable_public_values() -> None:
    assert [item.value for item in Market] == ["china", "united_kingdom"]
    assert [item.value for item in Locale] == ["zh-CN", "en-GB"]
    assert [item.value for item in ExecutionMode] == ["fixture", "live"]
    assert AssetKind.RENDERED_AD.value == "rendered_ad"
    assert RunStatus.PENDING.value == "pending"


def test_asset_ref_is_serializable_and_rejects_local_paths() -> None:
    asset = AssetRef(
        asset_id="11111111-1111-4111-8111-111111111111",
        kind="source_ad",
        media_type="image/png",
        sha256="a" * 64,
        provenance_ref="fixture:ai-app/source-ad",
        rights_ref="rights:fixture-synthetic-v1",
        expires_at=datetime(2026, 8, 11, tzinfo=UTC),
    )
    assert AssetRef.model_validate_json(asset.model_dump_json()) == asset

    with pytest.raises(ValidationError, match="local path"):
        AssetRef(
            asset_id="11111111-1111-4111-8111-111111111111",
            kind="source_ad",
            media_type="image/png",
            sha256="a" * 64,
            provenance_ref=r"C:\\private\\source.png",
            rights_ref="rights:fixture-synthetic-v1",
        )


def test_cultural_hypothesis_defaults_to_pending_review() -> None:
    hypothesis = CulturalHypothesis(
        hypothesis_id="55555555-5555-4555-8555-555555555555",
        target_market="united_kingdom",
        claim="A concise proof point may reduce interpretation effort.",
        evidence_refs=("evidence:public-study-1",),
        uncertainty="high",
        rationale="This is a testable localization hypothesis, not a fact.",
        validation_requirements=("Qualified UK reviewer",),
    )
    assert hypothesis.review_status == "pending"


def test_brand_lock_forbids_unknown_and_unapproved_localizable_fields(
    valid_run_payload: dict[str, object],
) -> None:
    brand_lock = valid_run_payload["brand_lock"]
    assert isinstance(brand_lock, dict)
    BrandLock.model_validate(brand_lock)

    with pytest.raises(ValidationError):
        BrandLock.model_validate({**brand_lock, "logo_can_change": True})

    with pytest.raises(ValidationError):
        BrandLock.model_validate({**brand_lock, "localizable_fields": ["product_name"]})
```

- [ ] **Step 3: Run the focused tests and verify the expected failure**

Run:

```powershell
python -m pytest tests/test_contracts.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'cultureshift.contracts'`.

- [ ] **Step 4: Implement the public vocabulary and shared models**

Create `src/cultureshift/contracts.py` with these foundations:

```python
from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
Reference = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
MediaType = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$"),
]
LocalizableField = Literal["narrative", "use_scenario", "trust_information", "language"]


class ContractModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class Market(StrEnum):
    CHINA = "china"
    UNITED_KINGDOM = "united_kingdom"


class Locale(StrEnum):
    ZH_CN = "zh-CN"
    EN_GB = "en-GB"


class ExecutionMode(StrEnum):
    FIXTURE = "fixture"
    LIVE = "live"


class AssetKind(StrEnum):
    SOURCE_AD = "source_ad"
    LOGO = "logo"
    PRODUCT_UI = "product_ui"
    LAYOUT_TEMPLATE = "layout_template"
    BACKGROUND = "background"
    RENDERED_AD = "rendered_ad"


class RunStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


def _is_local_path(value: str) -> bool:
    return re.match(r"^(?:[A-Za-z]:[\\/]|/|\\\\)", value) is not None


class AssetRef(ContractModel):
    asset_id: UUID
    kind: AssetKind
    media_type: MediaType
    sha256: Sha256
    provenance_ref: Reference
    rights_ref: Reference
    expires_at: AwareDatetime | None = None

    @field_validator("provenance_ref", "rights_ref")
    @classmethod
    def reject_local_paths(cls, value: str) -> str:
        if _is_local_path(value):
            raise ValueError("public references must not contain a local path")
        return value


class CulturalHypothesis(ContractModel):
    hypothesis_id: UUID
    target_market: Market
    claim: LongText
    evidence_refs: tuple[Reference, ...] = Field(min_length=1, max_length=32)
    uncertainty: Literal["low", "medium", "high"]
    rationale: LongText
    validation_requirements: tuple[ShortText, ...] = Field(min_length=1, max_length=16)
    review_status: Literal["pending", "accepted", "rejected"] = "pending"


class BrandLock(ContractModel):
    logo_asset_id: UUID
    product_name: ShortText
    verified_product_facts: tuple[ShortText, ...] = Field(min_length=1, max_length=32)
    product_ui_asset_ids: tuple[UUID, ...] = Field(min_length=1, max_length=16)
    benefit_order: tuple[ShortText, ...] = Field(min_length=1, max_length=16)
    cta_action_meaning: ShortText
    layout_template_asset_id: UUID
    localizable_fields: tuple[LocalizableField, ...] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def require_unique_sequences(self) -> Self:
        for values in (
            self.verified_product_facts,
            self.product_ui_asset_ids,
            self.benefit_order,
            self.localizable_fields,
        ):
            if len(values) != len(set(values)):
                raise ValueError("Brand Lock sequences must contain unique values")
        return self
```

- [ ] **Step 5: Run focused and existing domain tests**

Run:

```powershell
python -m pytest tests/test_contracts.py tests/test_domain.py -v
python -m ruff check src/cultureshift/contracts.py tests/conftest.py tests/test_contracts.py
```

Expected: all selected tests pass and Ruff reports no violations.

- [ ] **Step 6: Commit the shared contracts**

```powershell
git add src/cultureshift/contracts.py tests/conftest.py tests/test_contracts.py
git commit -m "feat: add safe public contract vocabulary"
```

---

### Task 2: Pipeline, API, and registry contracts

**Files:**
- Modify: `src/cultureshift/contracts.py`
- Modify: `tests/test_contracts.py`

**Interfaces:**
- Consumes: Task 1 shared models plus `LocalizationDirection`.
- Produces: `AdAnalysis`, `CreativeBrief`, `AdCopy`, `CritiqueReport`, `ResultVersion`, `RunCreate`, `RunCreated`, `JobAccepted`, `FeedbackRequest`, `RetryRequest`, `ExportSummary`, `ProjectRunContract`, and `ContractRegistry`.

- [ ] **Step 1: Add failing validation and registry tests**

Append to `tests/test_contracts.py`:

```python
from cultureshift.contracts import ContractRegistry, ResultVersion, RunCreate


def test_run_create_accepts_only_fixture_mvp_payload(valid_run_payload: dict[str, object]) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    assert request.execution_mode is ExecutionMode.FIXTURE

    with pytest.raises(ValidationError, match="live execution"):
        RunCreate.model_validate({**valid_run_payload, "execution_mode": "live"})

    with pytest.raises(ValidationError):
        RunCreate.model_validate({**valid_run_payload, "creative_format": "video"})

    with pytest.raises(ValidationError):
        RunCreate.model_validate({**valid_run_payload, "product_category": "medical"})


def test_result_version_fails_when_cta_meaning_changes(
    valid_run_payload: dict[str, object],
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    values = {
        "version": 1,
        "analysis": {
            "source_asset": request.source_asset,
            "detected_locale": "zh-CN",
            "brand_lock": request.brand_lock,
            "hypotheses": [],
            "warnings": ["human_review_required"],
        },
        "brief": {
            "direction": request.direction,
            "target_locale": "en-GB",
            "brand_lock": request.brand_lock,
            "hypotheses": [],
            "narrative": "A reviewable fixture narrative.",
            "use_scenario": "An authorized fictional workflow.",
            "trust_information": "Fixture demo; not a live model.",
        },
        "copy": {
            "locale": "en-GB",
            "headline": "Organize approved notes",
            "body": "Fixture copy for review.",
            "cta_label": "Try fixture",
            "cta_action_meaning": "A different action",
        },
        "critique": {
            "warnings": ["human_review_required"],
            "brand_lock_preserved": True,
            "requires_human_review": True,
        },
        "created_at": datetime(2026, 8, 10, tzinfo=UTC),
    }
    with pytest.raises(ValidationError, match="CTA action meaning"):
        ResultVersion.model_validate(values)


def test_registry_schema_contains_every_public_contract() -> None:
    definitions = ContractRegistry.model_json_schema(by_alias=True)["$defs"]
    for name in (
        "AssetRef",
        "BrandLock",
        "CulturalHypothesis",
        "AdAnalysis",
        "CreativeBrief",
        "AdCopy",
        "CritiqueReport",
        "ResultVersion",
        "RunCreate",
        "RunCreated",
        "JobAccepted",
        "FeedbackRequest",
        "RetryRequest",
        "ExportSummary",
        "ProjectRunContract",
    ):
        assert name in definitions
    assert "copy" in definitions["ResultVersion"]["properties"]
    assert "ad_copy" not in definitions["ResultVersion"]["properties"]
```

- [ ] **Step 2: Verify the tests fail for missing contracts**

Run:

```powershell
python -m pytest tests/test_contracts.py -v
```

Expected: collection fails because `ContractRegistry`, `ResultVersion`, and `RunCreate` do not exist.

- [ ] **Step 3: Implement the pipeline and API models**

Append these definitions to `src/cultureshift/contracts.py`, adding `AwareDatetime`, `Field`, `Literal`, `Self`, and `LocalizationDirection` imports if not already present:

```python
from cultureshift.domain import LocalizationDirection


WarningCode = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class AdAnalysis(ContractModel):
    source_asset: AssetRef
    detected_locale: Locale
    brand_lock: BrandLock
    hypotheses: tuple[CulturalHypothesis, ...] = Field(default=(), max_length=32)
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)


class CreativeBrief(ContractModel):
    direction: LocalizationDirection
    target_locale: Locale
    brand_lock: BrandLock
    hypotheses: tuple[CulturalHypothesis, ...] = Field(default=(), max_length=32)
    narrative: LongText
    use_scenario: LongText
    trust_information: LongText


class AdCopy(ContractModel):
    locale: Locale
    headline: ShortText
    body: LongText
    cta_label: ShortText
    cta_action_meaning: ShortText


class CritiqueReport(ContractModel):
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    brand_lock_preserved: bool
    requires_human_review: bool = True

    @model_validator(mode="after")
    def fail_closed_on_lock_change(self) -> Self:
        if not self.brand_lock_preserved and not self.requires_human_review:
            raise ValueError("Brand Lock changes require human review")
        return self


class ResultVersion(ContractModel):
    version: int = Field(ge=1)
    analysis: AdAnalysis
    brief: CreativeBrief
    ad_copy: AdCopy = Field(alias="copy")
    rendered_asset: AssetRef | None = None
    critique: CritiqueReport
    created_at: AwareDatetime

    @model_validator(mode="after")
    def preserve_cross_artifact_brand_lock(self) -> Self:
        if self.ad_copy.cta_action_meaning != self.brief.brand_lock.cta_action_meaning:
            raise ValueError("CTA action meaning must preserve Brand Lock")
        if self.rendered_asset is not None and self.rendered_asset.kind is not AssetKind.RENDERED_AD:
            raise ValueError("rendered_asset must use the rendered_ad asset kind")
        return self


class RunCreate(ContractModel):
    direction: LocalizationDirection
    execution_mode: ExecutionMode
    source_asset: AssetRef
    brand_lock: BrandLock
    product_category: Literal["ai_software", "ai_application"]
    creative_format: Literal["static_ad"]

    @model_validator(mode="after")
    def fixture_only_on_day_four(self) -> Self:
        if self.execution_mode is not ExecutionMode.FIXTURE:
            raise ValueError("live execution is not enabled in the Day 4 MVP")
        return self


class RunCreated(ContractModel):
    run_id: UUID
    status: RunStatus
    capability_token: Annotated[str, StringConstraints(min_length=16, max_length=4096)]
    created_at: AwareDatetime


class JobAccepted(ContractModel):
    run_id: UUID
    status: RunStatus
    accepted_at: AwareDatetime


class FeedbackRequest(ContractModel):
    run_id: UUID
    feedback: LongText
    requested_changes: tuple[ShortText, ...] = Field(min_length=1, max_length=16)
    submitted_at: AwareDatetime


class RetryRequest(ContractModel):
    run_id: UUID
    reason_category: Literal["validation", "generation", "review"]


class ExportSummary(ContractModel):
    run_id: UUID
    result_version: int = Field(ge=1)
    approval_status: Literal["pending", "approved", "rejected"]
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    exported_at: AwareDatetime


class ProjectRunContract(ContractModel):
    run_id: UUID
    request: RunCreate
    status: RunStatus
    result_versions: tuple[ResultVersion, ...] = Field(default=(), max_length=64)
    warning_codes: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ContractRegistry(ContractModel):
    asset_ref: AssetRef
    cultural_hypothesis: CulturalHypothesis
    brand_lock: BrandLock
    ad_analysis: AdAnalysis
    creative_brief: CreativeBrief
    ad_copy: AdCopy
    critique_report: CritiqueReport
    result_version: ResultVersion
    run_create: RunCreate
    run_created: RunCreated
    job_accepted: JobAccepted
    feedback_request: FeedbackRequest
    retry_request: RetryRequest
    export_summary: ExportSummary
    project_run: ProjectRunContract
```

- [ ] **Step 4: Run tests and resolve only contract-local failures**

Run:

```powershell
python -m pytest tests/test_contracts.py -v
python -m ruff check src/cultureshift/contracts.py tests/test_contracts.py
```

Expected: all contract tests pass. The Python attribute is `ad_copy`, while its validation/schema alias remains the approved public JSON field `copy`.

- [ ] **Step 5: Commit the complete contract surface**

```powershell
git add src/cultureshift/contracts.py tests/test_contracts.py
git commit -m "feat: define Day 4 pipeline contracts"
```

---

### Task 3: Deterministic JSON Schema export

**Files:**
- Create: `src/cultureshift/schema_export.py`
- Create: `scripts/export_contracts.py`
- Create: `tests/test_schema_export.py`
- Create: `contracts/json-schema/cultureshift.contracts.schema.json`

**Interfaces:**
- Consumes: `ContractRegistry.model_json_schema()`.
- Produces: `render_contract_schema() -> str`, `write_contract_schema(repo_root: Path) -> Path`, `check_contract_schema(repo_root: Path) -> bool`, and CLI `python scripts/export_contracts.py [--check]`.

- [ ] **Step 1: Add failing deterministic-render and stale-check tests**

Create `tests/test_schema_export.py`:

```python
import json

from cultureshift.schema_export import (
    SCHEMA_RELATIVE_PATH,
    check_contract_schema,
    render_contract_schema,
    write_contract_schema,
)


def test_contract_schema_is_deterministic_and_contains_public_definitions() -> None:
    first = render_contract_schema()
    second = render_contract_schema()
    assert first == second
    assert first.endswith("\n")
    schema = json.loads(first)
    assert schema["title"] == "ContractRegistry"
    assert "RunCreate" in schema["$defs"]


def test_write_and_check_detect_stale_contract_schema(tmp_path) -> None:
    path = write_contract_schema(tmp_path)
    assert path == tmp_path / SCHEMA_RELATIVE_PATH
    assert check_contract_schema(tmp_path)

    path.write_text("{}\n", encoding="utf-8", newline="\n")
    assert not check_contract_schema(tmp_path)
```

- [ ] **Step 2: Verify the schema-export test fails**

Run:

```powershell
python -m pytest tests/test_schema_export.py -v
```

Expected: collection fails because `cultureshift.schema_export` does not exist.

- [ ] **Step 3: Implement deterministic rendering and check mode**

Create `src/cultureshift/schema_export.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from cultureshift.contracts import ContractRegistry


SCHEMA_RELATIVE_PATH = Path("contracts/json-schema/cultureshift.contracts.schema.json")


def render_contract_schema() -> str:
    schema = ContractRegistry.model_json_schema(by_alias=True)
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_contract_schema(repo_root: Path) -> Path:
    path = repo_root / SCHEMA_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render_contract_schema().encode("utf-8"))
    return path


def check_contract_schema(repo_root: Path) -> bool:
    path = repo_root / SCHEMA_RELATIVE_PATH
    return path.is_file() and path.read_bytes() == render_contract_schema().encode("utf-8")
```

Create `scripts/export_contracts.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from cultureshift.schema_export import (
    SCHEMA_RELATIVE_PATH,
    check_contract_schema,
    write_contract_schema,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CultureShift public contracts")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    relative = SCHEMA_RELATIVE_PATH.as_posix()
    if args.check:
        if check_contract_schema(REPO_ROOT):
            print(f"current: {relative}")
            return 0
        print(f"stale: {relative}")
        return 1
    write_contract_schema(REPO_ROOT)
    print(f"wrote: {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, generate the committed schema, and check freshness**

Run:

```powershell
python -m pytest tests/test_schema_export.py -v
python scripts/export_contracts.py
python scripts/export_contracts.py --check
python -m ruff check src/cultureshift/schema_export.py scripts/export_contracts.py tests/test_schema_export.py
```

Expected: tests pass, the exporter reports only `contracts/json-schema/cultureshift.contracts.schema.json`, check mode exits 0, and Ruff passes.

- [ ] **Step 5: Commit exporter and generated schema together**

```powershell
git add src/cultureshift/schema_export.py scripts/export_contracts.py tests/test_schema_export.py contracts/json-schema/cultureshift.contracts.schema.json
git commit -m "feat: export deterministic JSON contracts"
```

---

### Task 4: FastAPI healthz and run-creation slice

**Files:**
- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `RunCreate`, `RunCreated`, `RunStatus`, `ProjectRun`, `SQLiteProjectRunRepository`, and `CapabilityTokenService.issue()`.
- Produces: `create_app(*, repository=None, token_service=None)`, `GET /healthz`, and `POST /api/v1/runs` returning HTTP 201.

- [ ] **Step 1: Replace the small app test with failing API-contract tests**

Expand `tests/test_app.py` to include injected dependencies and these assertions:

```python
import sqlite3

from fastapi.testclient import TestClient

from cultureshift.app import create_app
from cultureshift.capability_tokens import CapabilityTokenService
from cultureshift.repository import SQLiteProjectRunRepository


def make_client(tmp_path) -> tuple[TestClient, SQLiteProjectRunRepository]:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    return TestClient(create_app(repository=repository, token_service=tokens)), repository


def test_health_contracts_and_openapi(tmp_path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/healthz").json() == {"status": "ok"}
        openapi = client.get("/openapi.json").json()
    assert "RunCreate" in openapi["components"]["schemas"]
    assert "RunCreated" in openapi["components"]["schemas"]


def test_create_run_returns_one_time_token_without_persisting_it(
    tmp_path, valid_run_payload
) -> None:
    client, repository = make_client(tmp_path)
    with client:
        response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert len(body["capability_token"]) >= 16
    assert repository.get(body["run_id"]).direction.value == "china_to_uk"

    with sqlite3.connect(tmp_path / "runs.sqlite3") as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(project_runs)")}
    assert "capability_token" not in columns


def test_create_run_rejects_live_and_unknown_input(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    invalid = {**valid_run_payload, "execution_mode": "live", "private_note": "do not echo"}
    with client:
        response = client.post("/api/v1/runs", json=invalid)
    assert response.status_code == 422
    assert "do not echo" not in response.text


def test_create_run_returns_generic_error_without_exception_text(
    tmp_path, valid_run_payload
) -> None:
    class FailingRepository(SQLiteProjectRunRepository):
        def create(self, run):
            raise RuntimeError("private repository detail")

    repository = FailingRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with TestClient(create_app(repository=repository, token_service=tokens)) as client:
        response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "run_creation_failed"}}
    assert "private repository detail" not in response.text
```

- [ ] **Step 2: Run the API tests and verify missing-route/signature failures**

Run:

```powershell
python -m pytest tests/test_app.py -v
```

Expected: failures show `/healthz` and `/api/v1/runs` are absent and `create_app` does not yet accept injected dependencies.

- [ ] **Step 3: Implement lifespan initialization and run creation**

Replace `src/cultureshift/app.py` with an application factory following this exact structure:

```python
from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cultureshift.capability_tokens import Capability, CapabilityTokenService
from cultureshift.contracts import RunCreate, RunCreated, RunStatus
from cultureshift.domain import ProjectRun
from cultureshift.repository import SQLiteProjectRunRepository


def create_app(
    *,
    repository: SQLiteProjectRunRepository | None = None,
    token_service: CapabilityTokenService | None = None,
) -> FastAPI:
    runs = repository or SQLiteProjectRunRepository(Path(".cultureshift/runs.sqlite3"))
    tokens = token_service or CapabilityTokenService(
        secret=secrets.token_bytes(32),
        audience="cultureshift-api",
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        runs.initialize()
        yield

    application = FastAPI(title="CultureShift API", version="0.1.0", lifespan=lifespan)

    @application.exception_handler(RequestValidationError)
    async def safe_validation_error(
        _: Request, error: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"type": item["type"], "loc": item["loc"], "msg": item["msg"]}
            for item in error.errors()
        ]
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": details})

    @application.get("/health", tags=["operations"])
    @application.get("/healthz", tags=["operations"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post(
        "/api/v1/runs",
        response_model=RunCreated,
        status_code=status.HTTP_201_CREATED,
        tags=["runs"],
    )
    def create_run(request: RunCreate) -> RunCreated:
        try:
            run = runs.create(ProjectRun(direction=request.direction))
            token = tokens.issue(
                subject=str(run.id),
                capabilities={Capability.READ_PROJECT_RUN},
                ttl=timedelta(minutes=15),
            )
            return RunCreated(
                run_id=run.id,
                status=RunStatus(run.status.value),
                capability_token=token,
                created_at=run.created_at,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "run_creation_failed"},
            ) from None

    return application


app = create_app()
```

The broad catch is restricted to the side-effecting repository/token block so Pydantic validation remains FastAPI's HTTP 422 behavior.

- [ ] **Step 4: Run API and backend regression tests**

Run:

```powershell
python -m pytest tests/test_app.py tests/test_repository.py tests/test_capability_tokens.py -v
python -m ruff check src/cultureshift/app.py tests/test_app.py
```

Expected: all selected tests pass, raw fixture text and fake exception messages are absent from error responses, and Ruff passes.

- [ ] **Step 5: Commit the API slice**

```powershell
git add src/cultureshift/app.py tests/test_app.py
git commit -m "feat: add contract-backed run creation API"
```

---

### Task 5: Minimal Next.js and Vitest toolchain

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/package-lock.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/eslint.config.mjs`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/page.test.tsx`
- Create: `apps/web/src/app/globals.css`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/test/setup.ts`

**Interfaces:**
- Consumes: Node.js 24.18.0 and npm.
- Produces: npm scripts `test`, `test:e2e`, `typecheck`, `build`, `contracts:generate`, and `contracts:check`, plus a renderable foundation page.

- [ ] **Step 1: Scaffold the minimal App Router workspace with pinned create-next-app**

Run from the repository root:

```powershell
npx create-next-app@16.2.11 apps/web --ts --eslint --app --src-dir --use-npm --no-tailwind --import-alias "@/*" --yes
npm --prefix apps/web install --save-exact next@16.2.11
npm --prefix apps/web install --save-dev --save-exact vitest@4.1.10 @testing-library/react@16.3.2 @testing-library/dom@10.4.1 @testing-library/jest-dom@7.0.0 jsdom@30.0.1 @playwright/test@1.61.1 json-schema-to-typescript@15.0.4
```

Expected: `apps/web/package-lock.json` records exact resolved versions and no package is installed at the repository root.

- [ ] **Step 2: Write the failing foundation-page test**

Create `apps/web/src/app/page.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("CultureShift foundation page", () => {
  it("labels the contract-first Day 4 foundation", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: "CultureShift contract foundation" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Fixture Demo / 非实时模型")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Verify the test command is not configured yet**

Run:

```powershell
npm --prefix apps/web test
```

Expected: npm fails because the scaffold has no `test` script.

- [ ] **Step 4: Configure Vitest and the exact package scripts**

Create `apps/web/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

Create `apps/web/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

Set scripts without deleting the scaffold's existing scripts:

```powershell
npm --prefix apps/web pkg set scripts.test="vitest run"
npm --prefix apps/web pkg set scripts.test:e2e="playwright test"
npm --prefix apps/web pkg set scripts.typecheck="tsc --noEmit"
npm --prefix apps/web pkg set scripts.contracts:generate="node scripts/generate-contracts.mjs"
npm --prefix apps/web pkg set scripts.contracts:check="node scripts/generate-contracts.mjs --check"
```

Replace `apps/web/src/app/page.tsx` with:

```tsx
export default function Home() {
  return (
    <main>
      <h1>CultureShift contract foundation</h1>
      <p>Fixture Demo / 非实时模型</p>
      <p>Static AI software advertising localization for accountable human review.</p>
    </main>
  );
}
```

- [ ] **Step 5: Run web tests, type checking, and build**

Run:

```powershell
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
```

Expected: the smoke test passes, TypeScript passes, and Next.js builds without third-party network calls.

- [ ] **Step 6: Commit the web foundation**

```powershell
git add apps/web
git commit -m "feat: establish Day 4 web toolchain"
```

---

### Task 6: Generated TypeScript contracts and freshness check

**Files:**
- Create: `apps/web/scripts/generate-contracts.mjs`
- Create: `apps/web/scripts/generate-contracts.test.mjs`
- Create: `apps/web/src/generated/contracts.ts`
- Create: `apps/web/src/generated/contracts.test.ts`
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`

**Interfaces:**
- Consumes: `contracts/json-schema/cultureshift.contracts.schema.json` and `json-schema-to-typescript.compile()`.
- Produces: `renderContracts()`, `syncGeneratedFile(content, outputPath, check)`, CLI write/`--check`, and exported TypeScript types such as `RunCreate` and `RunStatus`.

- [ ] **Step 1: Write the failing stale-file helper test**

Create `apps/web/scripts/generate-contracts.test.mjs`:

```js
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { syncGeneratedFile } from "./generate-contracts.mjs";

describe("generated contract freshness", () => {
  it("fails closed when committed output is stale", () => {
    const directory = mkdtempSync(join(tmpdir(), "cultureshift-contracts-"));
    const output = join(directory, "contracts.ts");
    writeFileSync(output, "stale\n", "utf8");
    expect(() => syncGeneratedFile("fresh\n", output, true)).toThrow("stale");
  });
});
```

- [ ] **Step 2: Verify the generator test fails to import the missing module**

Run:

```powershell
npm --prefix apps/web test -- scripts/generate-contracts.test.mjs
```

Expected: Vitest fails because `generate-contracts.mjs` does not exist.

- [ ] **Step 3: Implement deterministic TypeScript rendering and check mode**

Create `apps/web/scripts/generate-contracts.mjs`:

```js
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { compile } from "json-schema-to-typescript";

const WEB_ROOT = resolve(import.meta.dirname, "..");
const REPO_ROOT = resolve(WEB_ROOT, "../..");
const SCHEMA_PATH = resolve(
  REPO_ROOT,
  "contracts/json-schema/cultureshift.contracts.schema.json",
);
const OUTPUT_PATH = resolve(WEB_ROOT, "src/generated/contracts.ts");

function normalize(text) {
  return `${text.replace(/\r\n/g, "\n").trimEnd()}\n`;
}

export function syncGeneratedFile(content, outputPath, check) {
  if (check) {
    if (!existsSync(outputPath) || readFileSync(outputPath, "utf8") !== content) {
      throw new Error("stale: src/generated/contracts.ts");
    }
    return;
  }
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, content, "utf8");
}

export async function renderContracts(schemaPath = SCHEMA_PATH) {
  const schema = JSON.parse(readFileSync(schemaPath, "utf8"));
  return normalize(
    await compile(schema, "ContractRegistry", {
      bannerComment: "/* AUTO-GENERATED FROM PYDANTIC JSON SCHEMA. DO NOT EDIT. */",
      unreachableDefinitions: true,
    }),
  );
}

export async function run({ check = false, outputPath = OUTPUT_PATH } = {}) {
  syncGeneratedFile(await renderContracts(), outputPath, check);
  console.log(`${check ? "current" : "wrote"}: src/generated/contracts.ts`);
}

const invokedDirectly =
  process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
if (invokedDirectly) {
  run({ check: process.argv.includes("--check") }).catch((error) => {
    const message =
      error instanceof Error && error.message.startsWith("stale:")
        ? error.message
        : "contract generation failed";
    console.error(message);
    process.exitCode = 1;
  });
}
```

- [ ] **Step 4: Generate declarations and add a type-compilation smoke test**

Run:

```powershell
npm --prefix apps/web run contracts:generate
npm --prefix apps/web run contracts:check
```

Create `apps/web/src/generated/contracts.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import type { RunStatus } from "./contracts";

describe("generated contracts", () => {
  it("exposes the public run status contract", () => {
    const status: RunStatus = "pending";
    expect(status).toBe("pending");
  });
});
```

- [ ] **Step 5: Run generator, web tests, and type checking**

Run:

```powershell
npm --prefix apps/web test
npm --prefix apps/web run contracts:check
npm --prefix apps/web run typecheck
```

Expected: stale-file test passes, generated type smoke test passes, freshness exits 0, and TypeScript reports no errors.

- [ ] **Step 6: Commit generator and generated output together**

```powershell
git add apps/web/scripts apps/web/src/generated apps/web/package.json apps/web/package-lock.json
git commit -m "feat: generate TypeScript contracts from JSON Schema"
```

---

### Task 7: GitHub Actions CI skeleton

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `tests/test_ci_workflow.py`

**Interfaces:**
- Consumes: Python, schema, npm, web, and public-boundary commands produced by Tasks 1–6.
- Produces: independent `backend`, `contracts-web`, and `public-boundary` GitHub Actions jobs.

- [ ] **Step 1: Write the failing CI contract test**

Create `tests/test_ci_workflow.py`:

```python
from pathlib import Path


WORKFLOW = Path(".github/workflows/ci.yml")


def test_ci_runs_required_day_four_gates() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for required in (
        "python -m ruff check .",
        "python -m pytest",
        "python scripts/export_contracts.py --check",
        "npm --prefix apps/web run contracts:check",
        "npm --prefix apps/web test",
        "npm --prefix apps/web run typecheck",
        "npm --prefix apps/web run build",
        "./scripts/verify-public-boundary.ps1",
    ):
        assert required in text
```

- [ ] **Step 2: Verify the test fails because the workflow is absent**

Run:

```powershell
python -m pytest tests/test_ci_workflow.py -v
```

Expected: `FileNotFoundError` for `.github/workflows/ci.yml`.

- [ ] **Step 3: Add the least-privilege CI workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13.5"
          cache: pip
      - run: python -m pip install -e ".[dev]"
      - run: python -m ruff check .
      - run: python -m pytest

  contracts-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13.5"
          cache: pip
      - uses: actions/setup-node@v4
        with:
          node-version: "24.18.0"
          cache: npm
          cache-dependency-path: apps/web/package-lock.json
      - run: python -m pip install -e .
      - run: npm --prefix apps/web ci
      - run: python scripts/export_contracts.py --check
      - run: npm --prefix apps/web run contracts:check
      - run: npm --prefix apps/web test
      - run: npm --prefix apps/web run typecheck
      - run: npm --prefix apps/web run build

  public-boundary:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - shell: pwsh
        run: ./scripts/verify-public-boundary.ps1
```

- [ ] **Step 4: Run the CI contract test and all fast local checks**

Run:

```powershell
python -m pytest tests/test_ci_workflow.py -v
python scripts/export_contracts.py --check
npm --prefix apps/web run contracts:check
python -m ruff check .
```

Expected: all commands pass and workflow text contains every required gate.

- [ ] **Step 5: Commit the CI skeleton**

```powershell
git add .github/workflows/ci.yml tests/test_ci_workflow.py
git commit -m "ci: add Day 4 contract foundation checks"
```

---

## Final verification gate

Run every command from the repository root after Task 7:

```powershell
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q
python scripts/export_contracts.py --check
npm --prefix apps/web ci
npm --prefix apps/web run contracts:check
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
pwsh -File scripts/verify-public-boundary.ps1
git diff --check
git status --short --branch
```

Expected:

- Python tests and Ruff pass.
- JSON Schema and TypeScript declarations are current.
- Vitest, TypeScript, and Next.js build pass.
- Public-boundary verification passes without reporting secrets, private content, or local paths.
- `git diff --check` is silent.
- The branch is ahead of `origin/main` only by the reviewed Issue #3 commits and the worktree is clean.

Do not close Issue #3 or push `main` at this point. Person B Day 4 work and `Day4.docx` still need their own approved design/plan/implementation cycle; the final Day 4 push happens only after both people’s work and the document are verified.
