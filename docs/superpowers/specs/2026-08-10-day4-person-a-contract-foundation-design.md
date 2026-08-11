# Day 4 Person A Contract Foundation Design

**Issue:** [#3](https://github.com/Yvonne-wyx/cultureshift/issues/3)

**Status:** Approved for implementation planning

**Fast-track task:** T03, Day 4, Person A

> **Security supersession (2026-08-11):** The original Next.js 16.2.11 pin is
> superseded by Next.js and eslint-config-next 16.3.0 after npm audit identified
> high-severity transitive PostCSS and Sharp advisories. All other approved pins
> and the Day 4 scope remain unchanged.

## Purpose

Day 4 establishes a contract-first engineering foundation without restructuring the backend completed during Days 1–3. Pydantic models remain the source of truth. Deterministic JSON Schema artifacts and generated TypeScript declarations make the same contracts available to the web application. A minimal API surface, web toolchain, and CI workflow prove that the contracts can be validated and kept fresh.

This work remains inside the MVP boundary: static advertising for AI software/apps in the China-to-UK and UK-to-China directions. It preserves the Brand Lock and represents cultural inference only as reviewable `CulturalHypothesis` records.

## Goals

- Define the Day 4 public contract set as validated Pydantic models.
- Export a deterministic, reviewable JSON Schema bundle.
- Generate TypeScript declarations only from that bundle.
- Add the minimum FastAPI behavior needed to test request validation and OpenAPI exposure.
- Establish a minimal Next.js, TypeScript, and Vitest workspace for later Person B fixture work.
- Add CI jobs that detect backend regressions, stale generated contracts, and web-toolchain failures.
- Preserve all existing Day 1–3 behavior and tests.

## Non-goals

- Moving the backend into a new `services/api` directory.
- Completing authenticated run retrieval, capability-token enforcement, restart recovery, or end-to-end integration; those are Day 5 work.
- Calling live AI, OCR, storage, analytics, or deployment providers.
- Adding Person B fixture assets, fixture composition, result UI, or walkthroughs.
- Expanding supported markets, locales, media formats, or product categories.
- Claiming cultural correctness, automated validation, legal compliance, or performance uplift.

## Architecture

The existing root Python package remains intact. Contract models live in a focused module under `src/cultureshift` and are imported by the FastAPI application, schema exporter, repository-facing run-creation service, and tests. Existing domain and repository behavior is reused rather than copied.

The generation path is one-way:

```text
Pydantic contracts
    -> deterministic JSON Schema bundle
        -> generated TypeScript declarations
            -> Next.js application and fixture work
```

Generated files are committed so reviewers can inspect contract changes. Both generation stages expose check modes that compare expected bytes with committed output and exit non-zero when artifacts are missing or stale. No generated file is edited by hand.

## Components

### Python contract module

`src/cultureshift/contracts.py` will define the public T03 contract surface:

- Enums: `Market`, `Locale`, `ExecutionMode`, `AssetKind`, and `RunStatus`.
- Shared value models: `AssetRef`, `CulturalHypothesis`, and `BrandLock`.
- Pipeline artifacts: `AdAnalysis`, `CreativeBrief`, `AdCopy`, `CritiqueReport`, and `ResultVersion`.
- API models: `RunCreate`, `RunCreated`, `JobAccepted`, `FeedbackRequest`, `RetryRequest`, and `ExportSummary`.
- Aggregate: `ProjectRunContract`, named separately from the existing persistence-oriented `ProjectRun` to avoid silently changing the Day 2 repository schema.
- Registry: `ContractRegistry`, used only to produce one bundled schema with named `$defs` for every public model.

The public values and minimum field sets are fixed for this slice:

- `Market`: `china`, `united_kingdom`; `Locale`: `zh-CN`, `en-GB`; `ExecutionMode`: `fixture`, `live`.
- `AssetKind`: `source_ad`, `logo`, `product_ui`, `layout_template`, `background`, `rendered_ad`.
- `RunStatus`: `pending`, `in_progress`, `blocked`, `completed`, `failed`.
- `AssetRef`: `asset_id`, `kind`, `media_type`, `sha256`, `provenance_ref`, `rights_ref`, and optional `expires_at`.
- `CulturalHypothesis`: `hypothesis_id`, `target_market`, `claim`, `evidence_refs`, `uncertainty`, `rationale`, `validation_requirements`, and `review_status` defaulting to `pending`.
- `BrandLock`: `logo_asset_id`, `product_name`, `verified_product_facts`, `product_ui_asset_ids`, `benefit_order`, `cta_action_meaning`, `layout_template_asset_id`, and `localizable_fields`.
- `AdAnalysis`: `source_asset`, `detected_locale`, `brand_lock`, `hypotheses`, and `warnings`.
- `CreativeBrief`: `direction`, `target_locale`, `brand_lock`, `hypotheses`, `narrative`, `use_scenario`, and `trust_information`.
- `AdCopy`: `locale`, `headline`, `body`, `cta_label`, and the locked `cta_action_meaning`.
- `CritiqueReport`: `warnings`, `brand_lock_preserved`, and `requires_human_review`.
- `ResultVersion`: `version`, `analysis`, `brief`, `copy`, optional `rendered_asset`, `critique`, and `created_at`.
- `RunCreate`: `direction`, `execution_mode`, `source_asset`, `brand_lock`, `product_category`, and `creative_format`.
- `RunCreated`: `run_id`, `status`, `capability_token`, and `created_at`.
- `JobAccepted`: `run_id`, `status`, and `accepted_at`.
- `FeedbackRequest`: `run_id`, `feedback`, `requested_changes`, and `submitted_at`; it does not collect reviewer identity.
- `RetryRequest`: `run_id` and a bounded `reason_category`; it does not repeat raw private input.
- `ExportSummary`: `run_id`, `result_version`, `approval_status`, `warnings`, and `exported_at`.
- `ProjectRunContract`: `run_id`, `request`, `status`, `result_versions`, `warning_codes`, `created_at`, and `updated_at`.

Opaque identifiers use UUIDs. Checksums are lowercase SHA-256 hex strings. Timestamps are timezone-aware UTC values. Non-empty text fields are whitespace-trimmed and length-bounded. `creative_format` permits only `static_ad`; `product_category` permits only `ai_software` or `ai_application`. `localizable_fields` permits only `narrative`, `use_scenario`, `trust_information`, and `language`.

All models are frozen, forbid unknown fields, use explicit constrained fields, and serialize enums by stable string values. `AssetRef` carries opaque identifiers, media type, checksum, provenance/rights references, and optional expiry metadata; it never contains an absolute local path or raw private content. `BrandLock` exposes the immutable categories already frozen by ADR-0002. `CulturalHypothesis` requires target context, evidence references, uncertainty, rationale, validation requirements, and a non-approved default review state.

`RunCreate` accepts only the two supported localization directions and the fixture execution mode on Day 4. The `live` enum value may exist for forward compatibility, but validation rejects it until a later provider decision explicitly enables it. Prohibited categories and unsupported formats fail closed.

### Contract export

`scripts/export_contracts.py` will generate `contracts/json-schema/cultureshift.contracts.schema.json` from `ContractRegistry.model_json_schema()`. It will:

- recursively sort object keys;
- emit UTF-8 JSON with two-space indentation and a final newline;
- avoid timestamps, local paths, machine identifiers, and other nondeterministic values;
- support `--check`, which performs no write and returns a failure when committed output differs;
- report only repository-relative artifact names.

The default command writes the artifact. The check command is suitable for CI and local verification.

### TypeScript generation

The web workspace will use `json-schema-to-typescript` to compile the committed JSON Schema bundle into `apps/web/src/generated/contracts.ts`. `apps/web/scripts/generate-contracts.mjs` will provide write and `--check` modes using the same normalized line endings and final newline rules as the Python exporter.

The generated file begins with a machine-generated warning and contains no manually maintained duplicate interfaces. The web package exposes `contracts:generate` and `contracts:check` scripts.

### API slice

The existing FastAPI application will keep `/health` for compatibility and add `/healthz` as the Day 4 health contract. `POST /api/v1/runs` will accept `RunCreate`, map its supported direction to the existing persistence domain, create a pending run through the SQLite repository, and return `RunCreated` with a newly issued capability token.

Both health endpoints return HTTP 200 with `{"status": "ok"}`. Successful run creation returns HTTP 201. Pydantic request failures return FastAPI's structured HTTP 422 response. Unexpected repository or token-service failures return HTTP 500 with a generic error category and no raw exception or submitted content. OpenAPI must expose `RunCreate` and `RunCreated` by those stable component names.

Day 4 proves creation and validation only. It does not add an unauthenticated run-read endpoint. Authenticated retrieval, token edge cases, restart recovery, and wider integration remain Day 5 scope.

FastAPI dependency injection will provide the repository and capability-token service so tests use isolated temporary SQLite databases and deterministic service setup. Responses and error bodies must not include submitted asset content, raw evidence, tokens other than the one-time creation response, or local filesystem paths.

### Web toolchain

`apps/web` will be a minimal Next.js App Router workspace using TypeScript. It contains only a small foundation page and a Vitest smoke test; fixture UI is intentionally deferred to Person B.

The toolchain will use Node.js 24.18.0, Next.js 16.2.11, Vitest 4.1.10, Testing Library React 16.3.2, Testing Library DOM 10.4.1, jest-dom 7.0.0, jsdom 30.0.1, Playwright 1.61.1, and json-schema-to-typescript 15.0.4. React and React DOM versions will be the exact compatible versions selected by `create-next-app@16.2.11` and recorded in the committed npm lockfile. Package scripts will include `test`, `test:e2e`, `typecheck`, `build`, `contracts:generate`, and `contracts:check`.

No browser test will make a network request to a third-party service. Playwright installation is prepared by the toolchain, but Day 4 CI does not require a browser walkthrough.

### CI skeleton

`.github/workflows/ci.yml` will run on pushes and pull requests. It will contain reviewable jobs for:

1. Python setup, editable development install, Ruff, and Pytest.
2. JSON Schema freshness, npm clean install, TypeScript contract freshness, Vitest, TypeScript checking, and the Next.js build.
3. The existing public-boundary verification script.

The workflow uses only repository contents and standard GitHub-hosted runners. It does not add secrets, provider credentials, paid services, deployments, or mutable external state.

## Data flow

1. A developer changes a Pydantic contract and first updates or adds its failing test.
2. The developer runs the Python exporter, producing the deterministic JSON Schema bundle.
3. The web generator compiles that committed bundle into TypeScript declarations.
4. FastAPI references the same Pydantic request and response models, so OpenAPI describes the public contract without a second source of truth.
5. Python and web tests consume the generated artifacts.
6. CI reruns both check modes; a contract change cannot merge with stale generated files.
7. Person B fixture artifacts can later validate against the committed bundle and import the generated declarations.

## Validation and failure behavior

- Unknown JSON fields, unsupported directions, unsupported formats, prohibited categories, missing rights references, and incomplete Brand Lock data receive structured validation failures.
- Contract generation fails when serialization is nondeterministic or committed artifacts are stale.
- TypeScript generation fails when the schema cannot be compiled or the checked declaration differs.
- Repository or run-creation failures return a non-sensitive server error and do not echo raw input.
- Token issuance happens only after a run is created. The raw token is returned once and is not logged or persisted.
- CI fails independently by job so backend, contract, web, and public-boundary failures remain distinguishable.

## Testing strategy

Implementation follows test-first development:

- Contract unit tests cover valid serialization, unknown-field rejection, Brand Lock requirements, hypothesis review defaults, fixture-only execution, and prohibited/unsupported inputs.
- Exporter tests prove byte-for-byte determinism and verify that `--check` detects stale output.
- API tests cover `/healthz`, preservation of `/health`, OpenAPI exposure of named contracts, successful run creation, and HTTP 422 for invalid input.
- Run-creation tests use a temporary SQLite repository and confirm no capability token is persisted.
- Web tests confirm the foundation page renders and generated contracts compile under TypeScript.
- Script-level checks cover JSON Schema and TypeScript freshness.
- The full existing Python test suite and public-boundary verifier must remain green.

## Acceptance mapping

| Issue #3 criterion | Design evidence |
| --- | --- |
| Explicit, validated Pydantic contracts | Python contract module and unit tests |
| Deterministic JSON Schema with `--check` | Contract export component |
| Generated TypeScript with freshness check | TypeScript generation component |
| Working minimal web toolchain | Next.js/Vitest workspace and smoke test |
| Health, OpenAPI, and invalid-input API tests | API slice and API testing strategy |
| Backend, contract, and frontend CI | CI skeleton |
| Existing tests remain green | Full-suite verification gate |
| Day 5 work excluded | Non-goals and API boundary |

## Completion boundary

Person A Day 4 is complete when all issue acceptance criteria pass locally, generated artifacts are current, the CI workflow is syntactically valid, the existing public-boundary check passes, and the implementation is committed against Issue #3. Person B begins only after this foundation is verified.
