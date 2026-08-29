# Day 17 Browser E2E and Reviewer Readiness Design

**Date:** 2026-08-29
**Plan item:** Day 17 / T11
**Issue:** [#16](https://github.com/Yvonne-wyx/cultureshift/issues/16)
**Baseline:** verified remote `main` `9f5d971cac68a87f0890952d792f4934c64695a1`

## Outcome and boundary

Day 17 adds a small, deterministic Playwright layer over the connected Day 16
Studio and freezes a public-safe reviewer-study package for a later, separately
authorized study. It does not add product behavior, a live provider, real
reviewers, response collection, analytics, cultural approval, or production
approval.

At the end of Day 17 recruitment remains closed: real reviewers confirmed `0`,
responses collected `0`, findings produced `0`, cultural approval not granted,
and production/campaign approval not granted.

## Person A: isolated browser E2E

### Process topology

`npm run test:e2e` invokes one Node orchestration script. It creates a private
temporary root, assigns a temporary SQLite database and asset directory, starts
FastAPI on `127.0.0.1:8000` with an explicit non-production secret, starts
Next.js on `127.0.0.1:3000` with telemetry disabled and the exact API origin,
waits for both health surfaces, runs Playwright Chromium, then terminates both
process groups and removes the temporary root even after a test failure.

The runner rejects production-like configuration and uses only repository
fixtures. It does not load `.env`, external credentials, paid services, live
providers, or network resources. Playwright uses one Chromium project, one
worker, no retries, no trace, no video, and screenshots only in memory when a
test explicitly inspects the page. Downloads live under Playwright's temporary
context and are deleted with it.

### Browser journeys

Two happy-path tests use the visible controls to complete upload, Run creation,
analysis, Brand Lock confirmation, draft, composition, Critic, Version 1 PNG and
JSON export, exact source deletion, and clean reset for `china_to_uk` and
`uk_to_china`.

One of those directions continues through the single structured
`shorten_headline` revision. It proves immutable Version 1 and Version 2 are
shown side by side, exports both versions independently, attempts no internal
shortcut, and verifies that a second revision control and visible Version 3 do
not exist. Public JSON evidence and visible fields are compared to prove Brand
Lock, verified facts, CTA meaning, protected Logo/UI sources, layout, and
cultural-hypothesis status remain preserved.

Focused browser tests cover only high-value UI boundaries. Real backend calls
cover upload validation, missing authority, expired/mismatched capabilities,
Brand Lock conflict, revision limit, invalid/unavailable export, and exact
deletion/reset where the public API can deterministically reach them. Bounded
Playwright response routing is permitted only for otherwise unreachable Day 15
operation-state branches (`revision_failed` retryable and final failure); the
browser still exercises the real Studio UI and its public HTTP error contract.
These cases are UI contract tests, not claims that the fixture backend naturally
failed.

### Security and exports

Tests observe requests and bounded browser state using sentinel predicates.
They never print or snapshot capability values. Assertions cover URL/query,
rendered text, localStorage, sessionStorage, cookies, suggested download names,
and public errors. Test output must not include tokens, absolute private paths,
source bytes, prompts, feedback, idempotency keys, or internal exceptions.

Every PNG/JSON download verifies the clicked version, safe filename, media type,
non-zero bounded size, and absence of capability sentinels. JSON is parsed and
allowlisted as public evidence. PNG IHDR bytes prove `1600 x 900`; backend
artifact identity and integrity checks remain authoritative.

### CI

Add a separate `browser-e2e` job with `contents: read`, Python and Node setup,
editable fixture backend install, `npm ci`, and
`npx playwright install --with-deps chromium`. The job sets an explicit test
secret, uses the runner's temporary storage, uploads no artifacts, and does not
change existing backend or web jobs.

## Person B: reviewer readiness

Create a dated, versioned study package plus a machine-readable status record
and activation checklist. The package covers purpose, inclusion/exclusion,
participant information, consent, withdrawal, privacy/minimisation, screening,
bilateral tasks, blinded counterbalanced A/B presentation, rubric, qualitative
follow-up, discomfort handling, escalation, stopping rules, decision rule,
limitations, and unapproved placeholders for recruitment channel,
compensation, and retention.

The rubric explicitly distinguishes clarity/readability, factual accuracy,
Brand Lock preservation, perceived cultural appropriateness, possible
stereotyping, trust/credibility, CTA comprehension, overall preference, and
reason for preference. All cultural judgments are reviewer observations.

No preview route is added. A read-only route would duplicate versioned study
material without advancing browser confidence and would expand the UI/public
surface. Validated documentation and structural tests are the lighter,
truth-preserving Day 17 deliverable.

Recruitment cannot open until a research owner, target profile, sample-size
rationale, channel, compensation, consent, privacy/retention, contact and
withdrawal route, data access, adverse-event escalation, cultural-expert role,
final materials, and explicit user authorization are all approved outside Git
where private data belongs.

## Test-first evidence plan

Each slice begins with a missing-artifact or focused behavioral failure, records
the observed RED result in the implementation plan and Day 17 record, adds the
minimum implementation, then runs focused GREEN and relevant regression tests.
No working behavior is intentionally broken to manufacture RED evidence.

## Acceptance boundary

Day 17 is ready only when both real-browser Version 1 journeys, one exact
Version 2 journey, versioned export verification, deletion/reset, high-value
failure/security coverage, temporary teardown, reviewer-package structural
tests, all repository gates, `Day17.docx` visual verification, authorized
publication, GitHub Actions, and remote-tree equality are directly verified.
All participant activation and all cultural/production approval remain not
ready.
