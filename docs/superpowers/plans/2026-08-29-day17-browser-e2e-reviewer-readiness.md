# Day 17 Browser E2E and Reviewer Readiness Implementation Plan

**Goal:** Prove the Day 16 bilateral Studio through Chromium and freeze a
truthful, activation-gated reviewer-study package without recruiting anyone.

**Spec:** `docs/superpowers/specs/2026-08-29-day17-browser-e2e-reviewer-readiness-design.md`

## Constraints

- Work from verified remote `main` `9f5d971cac68a87f0890952d792f4934c64695a1` on `day17-browser-e2e-reviewer-readiness`.
- Create and read the Day 17 Issue before production implementation.
- Use only deterministic bilateral fixtures and a non-production secret.
- Preserve capability, Brand Lock, revision, retry, export, deletion, and artifact-integrity boundaries.
- No live provider, recruitment, responses, telemetry, persistent browser session, Version 3, or approval claim.
- Do not commit test downloads, traces, screenshots, videos, databases, or uploaded assets.

## Task 1: Freeze issue/spec/plan gates

- [x] Verify clean local and remote Day 16 baseline.
- [x] Inspect Git history, open Issues, Day 6-8 and Day 14-16 materials, test layout, and CI.
- [x] Record missing-artifact RED for the Day 17 design, plan, reviewer package, and Playwright config.
- [x] Create Day 17 Issue [#16](https://github.com/Yvonne-wyx/cultureshift/issues/16) from the internally consistent scope below.
- [x] Replace the pending Issue reference in the design and reread the Issue.

## Task 2: Reviewer-readiness package (Person B)

- [ ] RED: add structural tests for the missing dated status, package, and activation checklist.
- [ ] Add `docs/evaluation/day17-reviewer-readiness-status-v1.0.json` with all zero/not-granted fields.
- [ ] Add `docs/evaluation/day17-reviewer-study-package-v1.0.md` with bilateral blinded/counterbalanced protocol, consent, withdrawal, privacy, rubric, follow-ups, escalation, stopping and decision rules, limitations, and explicitly unapproved placeholders.
- [ ] Add `docs/evaluation/day17-reviewer-activation-checklist-v1.0.md`; keep every gate closed.
- [ ] GREEN: run the focused structural test and existing evaluation tests.

## Task 3: E2E foundation (Person A)

- [ ] RED: run the absent Playwright config/spec command and record failure.
- [ ] Add `playwright.config.ts`, a teardown-safe isolated server runner, and the minimum npm scripts.
- [ ] Add ignore rules for Playwright output and temporary data.
- [ ] GREEN: prove server startup, one smoke navigation, teardown, and temp-root removal.

## Task 4: Bilateral Version 1 and export journeys

- [ ] RED: add the first visible bilateral flow test and observe the missing helper/behavior.
- [ ] Add a small page-object helper that only drives visible controls.
- [ ] Complete both fixture directions through Critic-ready Version 1.
- [ ] Verify PNG/JSON version selection, safe names, types, sizes, allowlisted JSON, and 1600 x 900 PNG.
- [ ] Explicitly delete the exact source and verify reset for both directions.
- [ ] GREEN: run the focused bilateral project.

## Task 5: One revision and security assertions

- [ ] RED: add Version 2 and capability-sentinel assertions.
- [ ] Drive `shorten_headline`, compare Version 1/2, export both, and prove no second revision or Version 3.
- [ ] Compare public evidence for Brand Lock, facts, CTA meaning, protected layers, layout, and pending hypotheses.
- [ ] Assert no capability sentinel in URL, rendered text, local/session storage, cookies, filenames, or public errors.
- [ ] GREEN: run the focused revision/security tests.

## Task 6: Failure and recovery boundaries

- [ ] RED: add focused user-visible failure cases.
- [ ] Cover invalid upload, missing authority, capability expiry/mismatch, Brand Lock conflict, revision limit, server-authorized retryable failure, final failure, unavailable/integrity-invalid export, and deletion/reset.
- [ ] Assert retry appears only for the bounded retryable revision response; safety, cultural-review, and final branches do not retry.
- [ ] GREEN: run the focused failure project and relevant Vitest/Python regression tests.

## Task 7: CI and complete verification

- [ ] RED: extend the CI workflow structural test before adding the job.
- [ ] Add an isolated least-privilege `browser-e2e` job installing Chromium only and uploading no artifacts.
- [ ] GREEN: run CI structure tests.
- [ ] Run full pytest and record count; Ruff check/format; schema and generated contracts; Vitest and count; Playwright and count; typecheck; ESLint; webpack build; npm audit; manifest/public-boundary; `git diff --check`.

## Task 8: Day 17 record and publication

- [ ] Build `Day17.docx` outside Git using the established daily-record content structure and a consistent professional record style.
- [ ] Render every page to PNG, inspect at 100%, fix and rerender until clean.
- [ ] Commit the intended tree, re-fetch remote `main`, and safely reconcile any movement.
- [ ] Push the branch without force, fast-forward `main` only if the verified publication path remains safe, and push `main` without force.
- [ ] Verify GitHub Actions URL/conclusion and exact remote `main` tree equality.
- [ ] Keep recruitment closed and report every remaining not-ready boundary.

## Issue acceptance criteria

- Both directions complete the visible connected Version 1 Studio journey in Chromium.
- One direction creates exactly one Version 2; Version 1 is immutable and no Version 3 is visible.
- PNG/JSON exports are version-specific, safe, bounded, integrity-checked, and PNGs are 1600 x 900.
- Exact source deletion returns the page to a clean reset state.
- Important validation, capability, conflict, retryable, final, and artifact failures remain distinguishable.
- Tokens are absent from URL, UI, storage, cookies, filenames, and public errors.
- E2E storage and downloads are temporary and removed; no trace/video/screenshot artifacts are committed or uploaded.
- Reviewer package and activation checklist cover both directions while reviewers/responses/findings remain zero and approvals remain not granted.
- All local repository gates, DOCX visual QA, authorized publication, GitHub Actions, and remote-tree equality pass.
