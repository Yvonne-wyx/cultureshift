# CultureShift

**A cross-cultural creative reasoning studio for adapting static AI-product advertising between China and the UK while preserving verified brand truth.**

CultureShift turns localization into a traceable, reviewable workflow. It separates facts that must remain unchanged from creative choices that may be explored, represents cultural reasoning as hypotheses rather than truth, and keeps a human accountable for approval.

> **Current evidence boundary:** the repository contains a deterministic fixture demonstration, not a production deployment or a live AI integration. The reviewer gate is closed: **0 reviewers, 0 responses, and 0 findings**. CultureShift does not claim cultural validation, campaign uplift, legal approval, or production readiness.

## Why CultureShift

Cross-market adaptation is not simply translation. A creative team must preserve brand identity, substantiated product claims, real product UI, and the intent of the call to action while reconsidering language, context, and trust cues for another market.

That work creates three recurring risks:

- **Brand drift:** localization silently changes a fact, feature, promise, or interaction.
- **Cultural overclaiming:** an intuition is presented as a validated insight without appropriate evidence or local review.
- **Lost accountability:** source provenance, uncertainty, decisions, and approval state disappear between handoffs.

CultureShift is designed around those risks. It provides structure for creative exploration without pretending to replace target-context research, qualified reviewers, legal advice, or accountable human judgment.

## MVP Scope

The MVP is deliberately narrow:

| Dimension | Included |
| --- | --- |
| Creative format | Static advertisements |
| Product category | AI software and AI applications |
| Localization directions | China → UK and UK → China |
| Output | A reviewable static proposal, evidence trail, hypotheses, warnings, and approval state |

Dynamic, video, audio, interactive, and personalized advertising are outside scope. Politics, medical, financial, gambling, tobacco, and child-targeted advertising are excluded.

## Core Product Mechanisms

### Brand Lock

Brand Lock is a fail-closed contract between verified brand truth and localizable creative choices.

**Locked:** logo, product name, verified product facts, real product UI, benefit order, CTA action meaning, and layout template.

**Localizable:** narrative, use scenario, verified trust information, and language.

If a requested transformation would alter a locked element, weaken its meaning, or detach it from provenance, the workflow preserves the original and surfaces the conflict instead of silently proceeding.

### `CulturalHypothesis`

Every cultural inference is represented as a `CulturalHypothesis`: a traceable proposal with rationale, uncertainty, evidence references, validation requirements, and pending review state. A hypothesis is never promoted to a cultural fact merely because the system generated it.

### Human-in-the-Loop

The system can organize evidence, propose a transformation, run structured checks, and expose warnings. A human reviewer remains responsible for verifying brand truth, evaluating cultural hypotheses, resolving conflicts, confirming rights and privacy authority, and approving any use or public display. There is no implicit or automated approval.

## End-to-End Workflow

1. **Ingest** an authorized static creative with provenance, purpose, privacy, and rights metadata.
2. **Extract and analyze** candidate content as untrusted input, retaining source references and uncertainty.
3. **Build the Brand Lock** and stop on missing, conflicted, or unverified immutable values.
4. **Confirm the lock** through an explicit human acknowledgement.
5. **Generate a draft** using only permitted localizable fields and evidence-linked hypotheses.
6. **Compose the creative** while preserving locked assets and carrying forward provenance and warnings.
7. **Run the Critic** to identify contract conflicts and review requirements; this is a structured check, not cultural validation.
8. **Review and export Version 1**, or submit one bounded revision to create immutable Version 2.
9. **Delete the uploaded source** through an exact-scope action when the session is complete.

## System Architecture

```text
Next.js / React / TypeScript Studio
              │
      generated API contracts
              │
       FastAPI application layer
              │
  workflow and domain service layer
  ├─ ingestion and temporary assets
  ├─ analysis and Brand Lock confirmation
  ├─ draft generation and composition
  ├─ Critic, revision, and export
  └─ capability-scoped access control
              │
 contracts · persistence · security boundaries
```

- **Frontend:** Next.js, React, and TypeScript provide the guided Studio, evidence views, Brand Lock confirmation, results comparison, revision controls, and accessible interaction states.
- **Backend:** FastAPI and Python expose the workflow through typed endpoints and domain-specific services rather than embedding product rules in route handlers.
- **Domain services:** analysis, Brand Lock confirmation, draft generation, composition, Critic evaluation, revision, export, temporary asset storage, and lifecycle cleanup are independently testable boundaries.
- **Contracts:** Pydantic is the hand-maintained public contract source. Deterministic JSON Schema and generated TypeScript declarations keep backend and frontend aligned.
- **Persistence and security:** repository abstractions preserve workflow state; capability tokens scope access; temporary assets have bounded retention; input, logging, provenance, rights, and public-boundary rules fail closed.

The provider interfaces are intentionally replaceable. The included demonstration uses deterministic fixtures and does not select or call a live vision, language, or image-generation provider.

## Key Features

- Guided bilateral Studio for China → UK and UK → China fixture flows
- Provenance, processing-authority, privacy, and rights capture
- Explicit Brand Lock review and confirmation gate
- Evidence-linked analysis and visible uncertainty
- Contract-constrained draft and image composition
- Structured Critic output with human-review requirements
- Immutable Version 1 and one bounded Version 2 revision
- Capability-scoped reads, updates, downloads, and deletion
- PNG and JSON exports with fixture and approval disclosures
- Exact-source deletion with clear scope and session reset
- Responsive, keyboard-operable, accessibility-checked UI

## Testing & Reliability

The repository treats product boundaries as executable checks:

- **Backend:** Pytest covers contracts, domain rules, API behavior, repositories, workflow transitions, providers, storage, capabilities, rate limits, generation, composition, Critic behavior, revision, export, and evaluation readiness.
- **Contract checks:** deterministic Pydantic → JSON Schema → TypeScript generation is checked for stale artifacts and cross-stack compatibility.
- **Frontend:** Vitest and Testing Library exercise components, Studio state, API integration, fixture validation, result composition, and revision behavior.
- **Browser E2E:** Playwright runs the complete fixture workflow in Chromium, including accessibility assertions powered by axe-core.
- **Security and release hygiene:** CI runs Ruff, type checking, production builds, `npm audit` at high severity, demo launcher checks, and public-boundary verification.
- **CI:** GitHub Actions separates backend, contracts/web, browser E2E, and public-boundary jobs on pushes and pull requests.

These checks establish software behavior within the repository. They do not establish cultural correctness, real-world effectiveness, or production operational readiness.

## Demo

The bundled demo is a deterministic, development-only walkthrough using the fictional Orbit AI fixture. **It connects to no live AI provider** and must not be used with production data or configuration.

Prerequisites: Python 3.11+, Node.js, npm, and the ability to run the local FastAPI and Next.js processes.

```bash
python -m pip install -e ".[dev]"
npm --prefix apps/web ci
npm --prefix apps/web run demo -- --check
npm --prefix apps/web run demo
```

Open the local Studio URL printed by the launcher and follow the [three-minute fixture walkthrough](docs/demo/day18-three-minute-walkthrough-v1.0.md). Optional `--backend-port`, `--frontend-port`, and `--root` arguments support caller-managed local settings.

### What Is Real vs. Fixture Demo

| Implemented in the repository | Simulated or not yet evidenced |
| --- | --- |
| FastAPI workflow and domain services | Live AI model/provider calls |
| Next.js Studio and bilateral flows | Real customer or production data |
| Brand Lock enforcement and confirmation | Cultural validation or cultural approval |
| Typed contracts and generated client types | Reviewer participation: **0 reviewers** |
| Critic, revision, composition, and exports | Study data: **0 responses, 0 findings** |
| Automated backend, frontend, E2E, accessibility, security, and boundary checks | Campaign performance, uplift, or business impact |
| Deterministic synthetic assets with recorded rights boundaries | Production hosting, scaling, monitoring, or deployment |

## Limitations and Non-goals

- CultureShift does not certify cultural correctness, legal compliance, accessibility compliance, brand approval, or campaign performance.
- The included Critic checks structured constraints; it is not a substitute for qualified target-context review.
- No reviewer study has been activated, and no human research evidence has been collected.
- The system does not autonomously publish advertisements or approve outputs.
- The MVP does not support other markets, product categories, or creative formats.
- Production authentication, external provider governance, operational monitoring, and deployment infrastructure are not included.
- Provider retention, logging, training, deletion, privacy, cost, and reliability would require separate evaluation before any live integration.

## AI-Assisted Development

This project was developed with AI assistance across planning, implementation, test design, and documentation. AI assistance does not replace human accountability: architecture and product boundaries are recorded in specifications and decision records, generated changes are exercised by automated checks, and claims are limited to evidence committed in this repository. The project does not treat AI-generated output as independent cultural research or validation.

## Getting Started

### Run the backend

```bash
python -m pip install -e ".[dev]"
export CULTURESHIFT_CAPABILITY_SECRET="local-development-secret"
python -m uvicorn cultureshift.app:app --host 127.0.0.1 --port 8000
```

The readiness endpoint is `GET /health`. Use a local-only secret and never commit populated environment files.

### Run the web app

```bash
npm --prefix apps/web ci
npm --prefix apps/web run dev
```

For the connected end-to-end experience, prefer the fixture demo launcher described above; it starts and checks both local processes with bounded cleanup.

### Run the checks

```bash
python -m ruff check .
python -m pytest
python scripts/export_contracts.py --check
npm --prefix apps/web run contracts:check
npm --prefix apps/web test
npm --prefix apps/web run demo:test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
npm --prefix apps/web run test:e2e
```

On Windows, run the public-boundary verification without changing the machine execution policy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify-public-boundary.ps1
```

## License Boundary

The MIT License applies only to original source code in this repository. Unless a file explicitly states otherwise, documentation, brand materials, and project-created non-code assets are **All Rights Reserved**. Third-party materials retain their own terms. See [LICENSE_SCOPE.md](LICENSE_SCOPE.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), and [demo/assets/RIGHTS.md](demo/assets/RIGHTS.md).

---

CultureShift is a portfolio-stage demonstration of how an AI product can be designed around explicit truth boundaries, uncertainty, and accountable review—not a claim that those hard problems have already been automated.
