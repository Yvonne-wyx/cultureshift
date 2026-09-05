# Day 18 Accessible Demo Hardening and Guided Studio UX Design

**Date:** 2026-08-29  
**Baseline:** verified `origin/main` `b9b7d25c536f5915524a3174331136edf2b9c550`  
**Issue:** [#17](https://github.com/Yvonne-wyx/cultureshift/issues/17)

## Outcome and boundaries

Day 18 makes the deterministic `/studio` workflow understandable and operable for a first-time keyboard user in a three-minute fixture demonstration. It adds no live provider, deployment, account, analytics, response collection, reviewer recruitment, Version 3, unrestricted feedback, or approval claim. The Day 17 reviewer gate remains closed with zero reviewers, responses and findings.

## Local demo lifecycle

Add one development-only Node launcher invoked by `npm --prefix apps/web run demo`. It validates a non-production secret, accepts configurable loopback ports and a caller-selected or owned temporary root, performs explicit port probes, builds and starts FastAPI before Next.js, waits on bounded public-safe readiness, and reports only loopback URLs and state. It owns and terminates only children it created. Signal/error teardown removes its temporary database, assets and PID-free working root. A `--check` mode tests configuration and port availability without starting services.

The existing OpenAPI/Studio reachability checks are sufficient public readiness surfaces: no new endpoint is justified because backend dependencies are local and initialized during app construction. The launcher distinguishes configuration, port availability, backend readiness and frontend reachability in its own bounded console messages.

## Accessible guided Studio

The page begins with concise fixture/demo, bilateral, Brand Lock, hypothesis and one-revision disclosures. An ordered progress list derives from legal reducer state; it communicates current/completed/needs-attention/unavailable states but contains no navigation.

Async operations use a named polite live region, busy states and duplicate-submit prevention. Validation uses an error summary linked to fields. Major successful transitions focus the next section heading only when it materially advances the workflow; errors focus the summary. Brand Lock adds an explicit immutable-state acknowledgement. Deletion becomes a two-step inline confirmation with confirm/cancel, bounded scope copy and focus return.

Comparison includes source, versions, requested structured change, protected invariants, Critic/human-review distinction, rule/evidence references and secondary hashes. Version 2 remains distinct from technical retry. The demo guide is versioned documentation rather than automation.

## Test evidence

Focused Vitest covers disclosures, progress semantics, validation summary, Brand Lock acknowledgement, loading/duplicate prevention and deletion confirm/cancel. Playwright adds `@axe-core/playwright` scans with serious/critical blockers at initial, Brand Lock, Version 1, comparison, validation and reset states. Browser tests also cover keyboard activation/focus, desktop/narrow/enlarged/reduced-motion layouts and absence of page-level horizontal overflow. Existing six bilateral, revision, export, failure, deletion and token-boundary tests remain authoritative regression evidence. No traces, videos, screenshots or accessibility reports are persisted or uploaded.

## Readiness boundary

Day 18 is ready only after launcher checks, unit/browser/accessibility/responsive gates, full repository verification, normal publication, successful GitHub Actions, remote-tree equality and rendered `Day18.docx` QA. Cultural, production and recruitment readiness remain explicitly not granted.
