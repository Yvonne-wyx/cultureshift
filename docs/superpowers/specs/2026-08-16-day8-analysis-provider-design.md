# Day 8 Structured Analysis Foundation and Provider Research Design

**Date:** 2026-08-16

**Plan row:** Day 8 / T05 + T12R

**Tracking:** GitHub Issue #7
https://github.com/Yvonne-wyx/cultureshift/issues/7

## Goal

Complete the Day 8 boundary with a deterministic, provider-neutral multimodal
analysis foundation and a dated provider decision record. Preserve the Day 7
privacy and recruitment truthfulness boundaries. Do not start the Day 9
`/analyze` endpoint, repair attempt, or `awaiting_brand_lock` transition.

## Scope and non-goals

Day 8 includes:

- an internal `VisionProvider` protocol;
- a deterministic, offline `FakeProvider`;
- an `AnalysisPipeline` with pre-provider and post-provider `SafetyGate` checks;
- stable, non-sensitive analysis failure codes;
- focused bilateral fixture tests;
- ADR research comparing OpenAI API, Google Vertex AI, and Amazon Bedrock;
- a public-safe human recruitment handoff checklist while recruitment remains
  inactive.

Day 8 excludes:

- live or paid provider calls, credentials, SDKs, procurement, or vendor account
  configuration;
- `/analyze`, job execution, repair/retry behavior, or run-state transitions;
- persistence of image bytes, extracted text, provider payloads, prompts, or raw
  provider errors;
- OCR, cultural validation, generated cultural facts, Brand Lock inference, or
  creative generation;
- reviewer identities, contact details, consent records, outreach evidence,
  responses, or findings.

## Person A design

### Internal request and provider boundary

The internal analysis request carries only the data required by the pipeline:

- private image bytes for the duration of the call;
- the existing `SourceAdAssetRef`;
- localization direction;
- the existing user-supplied `BrandLock`;
- the allowed product category and `static_ad` creative format.

`VisionProvider` is a small synchronous Python `Protocol`. Day 8 deliberately
keeps it independent of a vendor SDK and network lifecycle. A future live
adapter may perform its own asynchronous transport outside this protocol or the
protocol may be revised by a later ADR if async transport becomes a measured
need.

The provider returns a closed, validated internal result containing:

- detected locale;
- zero or more `CulturalHypothesis` candidates;
- non-sensitive warning codes;
- explicit booleans for suspected instruction-like content and prohibited
  content.

The provider cannot return or replace `source_asset` or `BrandLock`. The
pipeline always copies those values from the trusted request when constructing
the public `AdAnalysis` contract.

### FakeProvider

`FakeProvider` is deterministic and offline. It returns configured fixture
results for both supported directions and does not decode, log, retain, hash,
or derive claims from private image bytes. Its output is visibly fixture data,
not evidence of model quality or cultural correctness.

### SafetyGate and data flow

The pipeline performs these steps:

1. Validate the request as PNG or JPEG static-ad input, require an in-scope AI
   software/application category, require one supported direction, and enforce
   public provenance and rights references.
2. Reject missing bytes, media-signature mismatch, unsupported scope, or a
   closed/expired source asset with a stable code before the provider runs.
3. Call the configured provider exactly once.
4. Convert any provider exception into a generic `provider_failed` error without
   exposing exception text or input content.
5. Revalidate the provider result as a closed Pydantic model.
6. Block instruction-like content, prohibited content, wrong target markets,
   non-pending cultural hypotheses, or unapproved evidence references.
7. Construct `AdAnalysis` using the original `source_asset` and `BrandLock`.

No analysis result is persisted in Day 8.

### Failure model

The pipeline raises one typed exception carrying only one of these bounded
codes:

- `invalid_analysis_input`;
- `unsupported_analysis_scope`;
- `asset_lifecycle_closed`;
- `provider_failed`;
- `provider_output_invalid`;
- `instruction_like_content`;
- `prohibited_content`;
- `unsafe_hypothesis`.

The exception string contains only the code. Tests must prove that private
bytes, local paths, provider exception messages, and rejected free text do not
appear in errors or logs.

## Person B design

### Provider research and ADR

Create one dated, machine-readable comparison JSON and one human-readable ADR.
Both use official public sources and record the access date. The comparison
covers:

- training use and default retention behavior;
- zero-retention eligibility and exceptional retention;
- regional storage and processing controls relevant to UK-facing work;
- public pricing unit and the need to refresh prices before procurement;
- multimodal structured-output suitability;
- operational prerequisites and unresolved risks.

Official source set:

- OpenAI data controls:
  https://platform.openai.com/docs/models/default-usage-policies-by-endpoint
- OpenAI API pricing: https://openai.com/api/pricing/
- Google zero data retention:
  https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention
- Google locations:
  https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations
- Google pricing:
  https://cloud.google.com/vertex-ai/generative-ai/pricing
- Amazon Bedrock data protection:
  https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html
- Amazon Bedrock regional compatibility:
  https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html
- Amazon Bedrock pricing: https://aws.amazon.com/bedrock/pricing/

The ADR decision is:

- approve `FakeProvider` for fixture development and CI;
- keep all three live providers as unapproved candidates;
- require a named privacy owner, processing-region requirement, verified
  retention configuration, budget owner, dated price refresh, and separate
  implementation approval before selecting or calling a live provider.

Price figures are research snapshots, never program constants or procurement
promises.

### Recruitment handoff

Recruitment remains `pending_human_activation`, with `opened_at: null` and
`real_reviewers_confirmed: 0`. Add a machine-readable Day 8 handoff record and
extend the public recruitment pack with a matching checklist requiring:

- a named human coordinator;
- an approved private contact route;
- a protected consent vault;
- an approved privacy notice and retention statement;
- a withdrawal/deletion owner;
- a private assignment and response store.

The repository records readiness only. It must not record personal information,
outreach attempts, consent, assignments, responses, or reviewer claims.

## Testing strategy

Test-first development begins with import or behavior failures for the missing
provider/pipeline boundary. Focused tests cover:

- deterministic successful output for both directions;
- exact preservation of request `source_asset` and `BrandLock`;
- provider call count and preflight blocking before provider invocation;
- wrong media signature, unsupported category/format, expired source asset, and
  missing authority;
- malformed provider output and provider exception sanitization;
- instruction-like/prohibited flags and unsafe hypothesis rejection;
- absence of private bytes, local paths, free text, and raw exceptions from
  error surfaces;
- parsed comparison JSON source coverage, required dimensions, and explicit
  no-live-provider decision;
- parsed recruitment status and complete machine-readable human handoff
  requirements.

Tests validate stable behavior and structured evidence, not human prose. Review
the ADR and recruitment-pack wording manually for accuracy and clarity.

After focused GREEN, run one full Python/Ruff/schema/TypeScript/web/typecheck/
lint/build/audit/public-boundary verification. No new runtime dependency is
expected.

## Acceptance criteria

Day 8 is complete when:

1. `VisionProvider`, `FakeProvider`, `AnalysisPipeline`, and `SafetyGate` exist
   as isolated, documented units.
2. The pipeline returns valid `AdAnalysis` for bilateral fixtures while copying
   Brand Lock and source metadata only from the request.
3. All unsafe or malformed paths fail closed with stable non-sensitive codes.
4. No live provider, paid call, credential, provider SDK, or Day 9 endpoint is
   introduced.
5. The dated provider comparison and ADR contain the approved official sources,
   required dimensions, and deferred-live-provider decision.
6. Recruitment remains truthfully inactive and its Day 8 human handoff is
   complete.
7. Focused and full repository gates pass, the worktree is clean, and a verified
   local `Day8.docx` records only observed evidence.

GitHub Issue creation and final `main` publication each require separate user
authorization.
