# Day 11 Brief and Copy Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a fixture-only authenticated T07 slice that produces, validates, persists, and displays bilingual creative briefs and factual ad copy for both supported directions.

**Architecture:** A focused `draft_generation` module owns directional fixture definitions, the copywriter protocol, deterministic fixture output, and fail-closed validation. The existing SQLite repository and FastAPI app add an idempotent bodyless draft endpoint, while the existing typed fixture result pages expose the same Day 11 evidence without pretending to call a live model.

**Tech Stack:** Python 3.11+; FastAPI; Pydantic v2; SQLite; pytest; Next.js 16.3; React 19; TypeScript; Vitest; Testing Library.

**Spec:** `docs/superpowers/specs/2026-08-20-day11-brief-copy-generation-design.md`

## Global Constraints

- Execution remains fixture-only; add no provider SDK, credential, network call, or free-form prompt surface.
- Support only `china_to_uk` and `uk_to_china` static ads for AI software/applications.
- Copy the confirmed Brand Lock from trusted storage; never accept it from the Day 11 request.
- Use exactly `ZEU-S1`,`ZEU-S3` for China to UK and `EZC-S1`,`EZC-S3` for UK to China.
- Keep `ZEU-H1` and `EZC-H1` pending and out of the verified rule list.
- Reject unsupported product facts before persistence and expose only bounded non-sensitive error codes.
- Leave the run status `in_progress`; image generation, critique, revision, export, and completion are out of scope.
- Preserve the visible label `Fixture Demo / 非实时模型` and the human-review limitation.
- Use TDD for every behavior change and commit generated schema/TypeScript output only through generators.

---

### Task 1: Public draft contract and deterministic generation core

**Files:**
- Modify: `src/cultureshift/contracts.py`
- Create: `src/cultureshift/draft_generation.py`
- Modify: `tests/test_contracts.py`
- Create: `tests/test_draft_generation.py`
- Modify: `contracts/json-schema/cultureshift.contracts.schema.json`
- Modify: `apps/web/src/generated/contracts.ts`

**Interfaces:**
- Consumes: existing `AdAnalysis`, `AdCopy`, `BrandLock`, `CreativeBrief`, `LocalizationDirection`, `Locale`, and `RunStatus`.
- Produces: `DraftGenerated`, `DraftGenerationError`, `DraftErrorCode`, `Copywriter`, `CopywriterResult`, `FixtureCopywriter`, `DraftGenerator.generate(analysis, confirmed_brand_lock, *, direction)`.

- [ ] **Step 1: Add failing public-contract tests**

Add tests that construct a valid response and independently mutate brief direction/
locale, copy locale, CTA meaning, and directional rule IDs. Brand Lock equality to
trusted analysis is covered at the generator boundary because the public response
does not duplicate the analysis artifact:

```python
def test_draft_generated_preserves_cross_artifact_constraints(valid_draft_values):
    draft = DraftGenerated.model_validate(valid_draft_values)
    assert draft.status is RunStatus.IN_PROGRESS
    assert draft.rule_ids == ("ZEU-S1", "ZEU-S3")


@pytest.mark.parametrize(
    "mutation",
    ["brief_locale", "copy_locale", "cta", "rule_ids"],
)
def test_draft_generated_rejects_drift(valid_draft_values, mutation):
    mutate_draft(valid_draft_values, mutation)
    with pytest.raises(ValidationError):
        DraftGenerated.model_validate(valid_draft_values)
```

- [ ] **Step 2: Verify the contract tests are RED**

Run: `python -m pytest tests/test_contracts.py -q`

Expected: collection fails because `DraftGenerated` does not exist.

- [ ] **Step 3: Implement and register `DraftGenerated`**

Add the frozen public model and one after-validator:

```python
class DraftGenerated(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.IN_PROGRESS]
    brief: CreativeBrief
    ad_copy: AdCopy = Field(alias="copy")
    rule_ids: tuple[ShortText, ...] = Field(min_length=2, max_length=2)
    generated_at: UtcDatetime

    @model_validator(mode="after")
    def preserve_draft_constraints(self) -> Self:
        expected = {
            LocalizationDirection.CHINA_TO_UK: (Locale.EN_GB, ("ZEU-S1", "ZEU-S3")),
            LocalizationDirection.UK_TO_CHINA: (Locale.ZH_CN, ("EZC-S1", "EZC-S3")),
        }
        locale, rule_ids = expected[self.brief.direction]
        if self.brief.target_locale is not locale or self.ad_copy.locale is not locale:
            raise ValueError("draft locale must match direction")
        if self.ad_copy.cta_action_meaning != self.brief.brand_lock.cta_action_meaning:
            raise ValueError("CTA action meaning must preserve Brand Lock")
        if self.rule_ids != rule_ids:
            raise ValueError("draft rule IDs must match direction")
        return self
```

Register it in `ContractRegistry` so schema generation exposes a named definition.

- [ ] **Step 4: Add failing generation tests for both directions and unsafe output**

Create exact bilateral fixtures from the committed Orbit AI data. Cover deterministic
brief/copy output and the complete fail-closed matrix:

```python
@pytest.mark.parametrize(
    ("direction", "locale", "rules"),
    [
        (LocalizationDirection.CHINA_TO_UK, Locale.EN_GB, ("ZEU-S1", "ZEU-S3")),
        (LocalizationDirection.UK_TO_CHINA, Locale.ZH_CN, ("EZC-S1", "EZC-S3")),
    ],
)
def test_generator_returns_directional_factual_draft(analysis, direction, locale, rules):
    result = DraftGenerator(FixtureCopywriter()).generate(
        analysis, analysis.brand_lock, direction=direction
    )
    assert result.brief.direction is direction
    assert result.ad_copy.locale is locale
    assert result.rule_ids == rules
    assert result.fact_references == analysis.brand_lock.verified_product_facts


@pytest.mark.parametrize(
    "forgery",
    ["unsupported_fact", "wrong_rule", "wrong_locale", "cta_drift", "accepted_hypothesis"],
)
def test_generator_rejects_unsafe_copywriter_output(analysis, forgery):
    with pytest.raises(DraftGenerationError) as caught:
        DraftGenerator(ForgedCopywriter(forgery)).generate(analysis, analysis.brand_lock)
    assert caught.value.code is DraftErrorCode.OUTPUT_INVALID
```

Also test that an analyzed Brand Lock different from the confirmed value fails before
the copywriter is called.

- [ ] **Step 5: Verify generation tests are RED**

Run: `python -m pytest tests/test_draft_generation.py -q`

Expected: collection fails because `cultureshift.draft_generation` does not exist.

- [ ] **Step 6: Implement the minimal generation module**

Create focused immutable types and exact fixture definitions:

```python
class DraftErrorCode(StrEnum):
    BRAND_LOCK_UNCONFIRMED = "brand_lock_unconfirmed"
    OUTPUT_INVALID = "draft_output_invalid"


@dataclass(frozen=True)
class CopywriterResult:
    ad_copy: AdCopy
    fact_references: tuple[str, ...]
    rule_ids: tuple[str, ...]


class Copywriter(Protocol):
    def write(self, brief: CreativeBrief, rule_ids: tuple[str, ...]) -> CopywriterResult: ...
```

Define one immutable fixture per direction with exact locale, rule IDs, narrative,
scenario, trust text, headline, body, and CTA label. `DraftGenerator.generate` must:

1. require `analysis.brand_lock == confirmed_brand_lock`;
2. require every hypothesis to remain `pending`;
3. copy Brand Lock and hypotheses into `CreativeBrief`;
4. call the writer once;
5. require exact locale, CTA meaning, rule IDs, and fact references;
6. return a small internal result containing brief, copy, rule IDs, and fact references.

The caller passes the trusted stored run direction explicitly; the generator rejects
a provider-detected source locale inconsistent with that direction. `FixtureCopywriter`
returns the existing bilingual fixture copy and exactly the
confirmed `verified_product_facts`; it performs no I/O.

- [ ] **Step 7: Verify focused GREEN and regenerate contracts**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_contracts.py tests/test_draft_generation.py -q
python scripts/export_contracts.py
npm.cmd --prefix apps/web run contracts:generate
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
```

Expected: all selected tests pass and both freshness checks report current output.

- [ ] **Step 8: Commit Task 1**

```powershell
git add src/cultureshift/contracts.py src/cultureshift/draft_generation.py tests/test_contracts.py tests/test_draft_generation.py contracts/json-schema/cultureshift.contracts.schema.json apps/web/src/generated/contracts.ts
git commit -m "feat: generate constrained Day 11 drafts"
```

---

### Task 2: Atomic draft persistence and authenticated idempotent API

**Files:**
- Modify: `src/cultureshift/repository.py`
- Modify: `src/cultureshift/app.py`
- Modify: `tests/test_repository.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `DraftGenerator.generate`, `DraftGenerated`, the confirmed Brand Lock record, existing update capability verification, and `ProjectRunStatus.IN_PROGRESS`.
- Produces: `DraftRecord`, `SQLiteProjectRunRepository.get_draft(run_id)`, `SQLiteProjectRunRepository.save_draft(...)`, and `POST /api/v1/runs/{run_id}/draft`.

- [ ] **Step 1: Add failing migration and repository tests**

Test fresh and legacy databases for four nullable columns:

```python
assert {
    "creative_brief_json",
    "ad_copy_json",
    "draft_rule_ids_json",
    "draft_generated_at",
} <= context_columns
```

Add tests that save one valid draft, read back an equal `DraftRecord`, replay the
same call, reject a different second draft, reject missing confirmation, and prove a
transactional failure leaves all four columns null.

- [ ] **Step 2: Verify repository tests are RED**

Run: `python -m pytest tests/test_repository.py -q`

Expected: failures for missing columns and methods.

- [ ] **Step 3: Implement atomic immutable draft storage**

Add:

```python
class DraftImmutableError(ValueError):
    pass


@dataclass(frozen=True)
class DraftRecord:
    brief: CreativeBrief
    ad_copy: AdCopy
    rule_ids: tuple[str, ...]
    generated_at: datetime
```

`initialize` adds each column independently for legacy databases. `get_draft`
requires either all four values or none and validates UTC. `save_draft` runs one
conditional update requiring `status = in_progress`, non-null confirmed Brand Lock,
and all draft columns null. If a draft exists, return it only when all values match;
otherwise raise `DraftImmutableError`. Do not store fact references because they are
validated against the already persisted confirmed lock before the write.

- [ ] **Step 4: Verify repository GREEN**

Run: `python -m pytest tests/test_repository.py -q`

Expected: all repository tests pass.

- [ ] **Step 5: Add failing API tests**

Extend the existing app fixture to inject `DraftGenerator(FixtureCopywriter())`, then
test:

```python
response = client.post(f"/api/v1/runs/{run_id}/draft", headers=update_header)
assert response.status_code == 200
assert response.json()["status"] == "in_progress"
assert response.json()["rule_ids"] == ["ZEU-S1", "ZEU-S3"]
```

Cover missing/invalid token, subject mismatch, missing run, wrong state, unconfirmed
lock, idempotent replay, provider-output failure, and repository failure. Assert the
response never includes a submitted secret, local path, internal exception, or raw
fixture prompt.

- [ ] **Step 6: Verify API tests are RED**

Run: `python -m pytest tests/test_app.py -q`

Expected: `404` for the missing draft route or fixture-construction failure for the
missing dependency.

- [ ] **Step 7: Implement the bodyless endpoint**

Extend `create_app` with optional `draft_generator: DraftGenerator | None = None`,
defaulting to the safe fixture generator. The endpoint must:

1. verify `UPDATE_PROJECT_RUN` and exact subject;
2. return an existing draft first for idempotent replay;
3. require an existing `in_progress` run, analysis, and confirmation;
4. generate once and persist once;
5. map only the approved bounded codes and suppress exception text;
6. return `DraftGenerated` using the stored timestamp.

Map not-found to 404, authentication to 401/403, invalid state or missing confirmation
to 409, invalid generated output to 422, and persistence failure to 500.

- [ ] **Step 8: Verify Task 2 GREEN and commit**

Run:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_repository.py tests/test_app.py -q
python -m ruff check src/cultureshift/repository.py src/cultureshift/app.py tests/test_repository.py tests/test_app.py
```

Expected: all selected tests and Ruff pass.

```powershell
git add src/cultureshift/repository.py src/cultureshift/app.py tests/test_repository.py tests/test_app.py
git commit -m "feat: persist and serve Day 11 drafts"
```

---

### Task 3: Bilingual fixture evidence and Day 11 result UI

**Files:**
- Modify: `apps/web/src/fixtures/types.ts`
- Modify: `apps/web/src/fixtures/fixture-validation.ts`
- Modify: `apps/web/src/fixtures/data/china-to-uk.json`
- Modify: `apps/web/src/fixtures/data/uk-to-china.json`
- Modify: `apps/web/src/fixtures/fixture-loader.test.ts`
- Modify: `apps/web/src/results/compose-fixture-result.ts`
- Modify: `apps/web/src/results/compose-fixture-result.test.ts`
- Create: `apps/web/src/components/draft-evidence.tsx`
- Create: `apps/web/src/components/draft-evidence.test.tsx`
- Create: `apps/web/src/components/draft-evidence.module.css`
- Modify: `apps/web/src/app/results/[fixtureId]/page.tsx`
- Modify: `apps/web/src/app/results/[fixtureId]/page.test.tsx`

**Interfaces:**
- Consumes: generated `CreativeBrief`, `AdCopy`, and the two existing immutable fixture bundles.
- Produces: typed fixture `draft` data, `FixtureResult.draft`, and accessible `DraftEvidence` rendering.

- [ ] **Step 1: Add failing raw-fixture validation tests**

Require each JSON fixture to add:

```ts
draft: {
  brief: CreativeBrief;
  copy: AdCopy;
  rule_ids: string[];
  prompt_summary: string;
}
```

Test exact locale/direction, exact Brand Lock equality, exact bilateral rule IDs,
pending-only hypotheses, copy/brief CTA equality, and the exact disclosure text.
Mutate raw imported JSON rather than already validated loader output.

- [ ] **Step 2: Verify fixture tests are RED**

Run: `npm.cmd --prefix apps/web test -- fixture-loader.test.ts`

Expected: failures because `draft` is missing.

- [ ] **Step 3: Add minimal bilingual fixture draft data and validation**

Reuse the existing localized copy as `draft.copy`. Add brief fields matching the
backend fixture definitions and a short non-sensitive prompt summary:

- en-GB: `Use verified facts and ZEU-S1/ZEU-S3; preserve Brand Lock.`
- zh-CN: `仅使用已验证事实与 EZC-S1/EZC-S3；保持品牌锁定。`

Do not add raw/system prompts. In `fixture-validation.ts`, validate plain objects,
exact immutable lock equality, exact directional mapping, pending hypotheses, and
copy CTA/locale invariants before returning a frozen fixture.

- [ ] **Step 4: Add failing composition and component tests**

Test that composition deep-clones/freezes draft evidence. Test `DraftEvidence` for:

- a level-two `Creative brief / 创意简报` heading;
- narrative and use scenario;
- headline, body, CTA, and locked action meaning;
- exactly two source-backed rule IDs;
- pending hypothesis text and human-review language;
- `Fixture Demo / 非实时模型`;
- no live-model or cultural-validation implication.

- [ ] **Step 5: Verify component tests are RED**

Run:

```powershell
npm.cmd --prefix apps/web test -- compose-fixture-result.test.ts draft-evidence.test.tsx page.test.tsx
```

Expected: import/behavior failures because `FixtureResult.draft` and `DraftEvidence`
do not exist.

- [ ] **Step 6: Implement the compact typed Day 11 section**

Add `draft` to `FixtureResult`, deep-clone it in `composeFixtureResult`, and render a
single `DraftEvidence` component after the Brand Lock form. Use semantic sections,
headings, lists, and definition terms. Keep styling within the new CSS module and do
not duplicate the full result-page layout.

- [ ] **Step 7: Verify Web GREEN and commit**

Run:

```powershell
npm.cmd --prefix apps/web test -- fixture-loader.test.ts compose-fixture-result.test.ts draft-evidence.test.tsx page.test.tsx
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
```

Expected: all selected tests, typecheck, and lint pass.

```powershell
git add apps/web/src/fixtures apps/web/src/results apps/web/src/components/draft-evidence.tsx apps/web/src/components/draft-evidence.test.tsx apps/web/src/components/draft-evidence.module.css apps/web/src/app/results/[fixtureId]/page.tsx apps/web/src/app/results/[fixtureId]/page.test.tsx
git commit -m "feat: show bilingual Day 11 draft evidence"
```

---

### Task 4: Repository-wide verification and delivery record

**Files:**
- Create locally outside Git: `D:/create/Diversity/Day11.docx`
- Modify only if a gate exposes a Day 11 regression: the directly responsible Day 11 file and its regression test.

**Interfaces:**
- Consumes: the three completed Day 11 commits and the established Day 1–10 document format.
- Produces: verified repository state, a rendered/inspected local Day 11 record, and publication-ready branch.

- [ ] **Step 1: Run every repository gate from a clean environment**

```powershell
$env:PYTHONPATH='src'
$env:CULTURESHIFT_CAPABILITY_SECRET='ci-fixture-secret-not-for-production'
$env:CULTURESHIFT_TEMP_ASSET_DIR='.cultureshift/assets'
python -m pytest -q
python -m ruff check .
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
npm.cmd --prefix apps/web test -- --run
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
$env:NEXT_TELEMETRY_DISABLED='1'
npm.cmd --prefix apps/web run build
npm.cmd --prefix apps/web audit --audit-level=high
powershell -File scripts/validate-public-boundary.ps1
git diff --check
git status --short
```

Expected: every command exits zero, generated outputs are current, audit reports no
high-or-worse finding, public-boundary scan passes, and the worktree is clean.

- [ ] **Step 2: Review the complete Day 11 diff against the spec**

Check each acceptance criterion, endpoint/error boundary, migration behavior, exact
rule mapping, both direction fixtures, no secret/path/prompt leakage, and absence of
Day 12 work. Fix only reproducible Day 11 defects with a failing regression first.

- [ ] **Step 3: Generate and visually verify `Day11.docx`**

Use the Documents skill and the established Day 10 document as the formatting
reference. Record Person A and Person B deliverables, issue/commit links, RED/GREEN
evidence, full gates, scope exclusions, and remaining human-review limitations.
Render the DOCX to page images and inspect every page before delivery.

- [ ] **Step 4: Recheck remote main and publish without overwrite**

Test `github.com` and `api.github.com`, fetch/inspect remote `main`, and compare its
commit/tree with the branch base. If unchanged, push the Day 11 branch fast-forward to
`main`. If Git network resets, immediately use the previously validated authenticated
GitHub API commit/tree/ref path. If a partner commit appeared, integrate it without
force-pushing, rerun affected gates, then publish.

- [ ] **Step 5: Verify remote truth**

Confirm GitHub `main` commit and tree match local HEAD, inspect the Day 11 Issue and
Actions run, and report the exact remote commit, Issue URL, CI URL/status, local DOCX
path, test counts, and any non-blocking warnings.
