# Day 5 Capability Recovery and Fixture Vertical Slice Design

**Date:** 2026-08-12

**Owners:** Person A (Engineering / AI / Backend) and Person B (Product / Frontend / Research)

**Tracking:** GitHub Issue #4

## Goal

Deliver the fast-track Day 5 checkpoint as a three-minute, fixture-only vertical slice. A caller can create a persisted run, retrieve it with a least-privilege capability after an application restart, and inspect deterministic bilateral result pages that are visibly marked as non-live fixture demonstrations.

## Scope and constraints

- Support only the existing China-to-UK and UK-to-China static AI-software fixtures.
- Preserve the approved Orbit AI Brand Lock exactly.
- Treat every cultural inference as a pending `CulturalHypothesis` requiring human review.
- Use only project-owned assets already recorded in the demo rights manifest.
- Make no provider, network, paid API, telemetry, or live-model call.
- Do not add upload, temporary storage, deletion, TTL purge, rate limiting, analysis, Brand Lock confirmation, export, feedback, or revision behavior.
- Use one main implementation agent, focused RED-to-GREEN tests, one final full verification, and at most one consolidated repair pass.

## Person A: capability security and restart recovery

### Stable secret boundary

The default FastAPI application reads `CULTURESHIFT_CAPABILITY_SECRET` from the environment. The UTF-8 value must contain at least 32 bytes. Missing or short configuration fails during application construction with a configuration-only error that contains no secret value.

Tests continue to inject a deterministic `CapabilityTokenService`; repository tests use temporary SQLite files. CI supplies a non-production test secret through the workflow environment. No secret, token, or secret-derived value is written to Git, SQLite, logs, errors, or response bodies other than the one-time token returned by run creation.

### Authenticated retrieval

Add `GET /api/v1/runs/{run_id}`. It accepts `Authorization: Bearer <token>` and requires `project_run:read`.

The endpoint verifies the token before reading the repository, then requires the token subject to equal the requested run UUID. A valid request returns a public run snapshot containing:

- `run_id`
- `direction`
- `status`
- `warning_codes`
- `created_at`
- `updated_at`

It never returns or persists the capability token.

Authentication failures are deliberately non-specific:

- missing or malformed Bearer authorization: `401`, code `invalid_capability`
- invalid, expired, wrong-audience, or insufficient-scope token: `401`, code `invalid_capability`
- valid token whose subject does not match the requested run: `403`, code `capability_subject_mismatch`
- valid matching token for a missing run: `404`, code `run_not_found`

Responses must not echo authorization content, local paths, submitted fixture data, database details, or internal exceptions.

### Restart recovery

Restart recovery is proven with two independently constructed FastAPI applications that reuse the same SQLite path and the same injected stable capability secret:

1. the first application creates a run and returns its one-time token;
2. the first application closes;
3. the second application initializes the existing database;
4. the original token retrieves the original run through the new GET endpoint.

Reusing a database with a different secret must fail authentication. The database schema remains token-free.

## Person B: deterministic result slice

### Pure composition model

Add a pure TypeScript composer that accepts a validated, deeply frozen `FixtureBundle` and returns a deeply frozen `FixtureResult`. The result is derived only from existing fixture fields and contains:

- stable fixture and direction identifiers;
- source and result asset references;
- localized copy;
- the exact Brand Lock;
- rule identifiers and pending hypotheses;
- warnings and limitation text;
- an ordered three-step walkthrough;
- the exact watermark `Fixture Demo / 非实时模型`.

The composer performs no random, time-based, filesystem, fetch, provider, or browser operation. Repeated composition of the same fixture must be structurally equal and JSON-byte deterministic. It must not mutate or weaken the source bundle.

### Result page

Add static routes for `/results/china-to-uk` and `/results/uk-to-china` using the existing fixture loader and static parameter generation. Unknown fixture IDs resolve through the framework's not-found boundary.

Each page presents:

- a visible human-readable direction and source-to-result context;
- the project-owned source creative and deterministic result composition;
- the exact fixture watermark in visible text and an accessible semantic marker;
- localized headline, body, CTA label, and CTA action meaning;
- a complete Brand Lock checklist;
- rule IDs, pending hypotheses, evidence references, warnings, and limitations;
- a link back to the bilateral fixture lab.

The page must not call the backend or imply that the result was generated live.

### Three-minute walkthrough

The walkthrough is an ordered, always-visible list rather than a stateful wizard:

1. verify the source creative and direction;
2. inspect locked brand truth and the deterministic localized composition;
3. review evidence, pending hypotheses, warnings, and limitations.

This keeps the walkthrough keyboard accessible, server rendered, printable, and free of client-state or E2E complexity. It contains no claim of cultural correctness, legal compliance, automated validation, or performance uplift.

### Bilateral entry page

Keep the existing read-only fixture previews and add one clear result link per fixture. Do not add generation buttons, progress indicators, editing controls, retry controls, or download/export behavior.

## Data flow

```text
POST /api/v1/runs
  -> SQLite non-sensitive run state
  -> one-time read capability
  -> application restart with same database + secret
  -> authenticated GET /api/v1/runs/{run_id}

validated FixtureBundle
  -> pure deterministic composeFixtureResult()
  -> static /results/[fixtureId] page
  -> visible watermark + Brand Lock + evidence + walkthrough
```

The backend recovery proof and frontend result demonstration share the Day 4 contracts and fixture vocabulary but do not introduce a browser-to-backend session integration. That integration remains scheduled for Day 16.

## Testing strategy

Development uses two focused TDD lanes:

1. Python tests cover environment configuration, safe Bearer parsing, token failure modes, subject isolation, missing runs, token-free storage, and two-application restart recovery.
2. Web tests cover deterministic composition, deep immutability, exact watermarking, both static result routes, Brand Lock completeness, pending-hypothesis disclosure, walkthrough order, accessible navigation, and absence of live-model claims.

After focused tests are green, run one consolidated verification:

- full Python tests and Ruff;
- manifest validation;
- JSON Schema and TypeScript contract freshness;
- full web tests, typecheck, lint, telemetry-disabled build, and npm audit;
- public-boundary scan;
- Git whitespace and clean-status checks.

No new dependency is expected.

## Exit criteria

Day 5 is complete when both directions can be demonstrated from the bilateral entry page to a deterministic result page in under three minutes, every result is explicitly watermarked as a non-live fixture, capability-protected run retrieval survives a controlled restart, all final gates pass, GitHub `main` contains the exact verified tree, and the local Day 5 record reflects the actual evidence.
