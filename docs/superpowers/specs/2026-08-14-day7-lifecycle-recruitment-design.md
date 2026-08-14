# Day 7 Asset Lifecycle and Recruitment Readiness Design

**Date:** 2026-08-14
**Tracking:** GitHub Issue #6

## Goal

Complete the Day 7 boundary with a restart-safe temporary-asset lifecycle and a
truthful, frozen evaluation package that is ready for a human coordinator to
activate. Keep the change dependency-free and do not start Day 8 provider work.

## Person A: bounded asset lifecycle

- Keep the Day 6 raw PNG/JPEG upload interface.
- Persist only public-safe lifecycle metadata beside each private asset.
- Return a one-time delete capability token; never persist that token.
- Add idempotent `DELETE /api/v1/assets/{asset_id}` authorization.
- Purge assets whose recorded 24-hour expiry has passed, at application startup
  and through a small operator script.
- Add an in-memory fixed-window upload limiter keyed by the direct client address.
- Create a seven-day tombstone containing only a hash of the asset identifier,
  deletion time, reason, and result. A tombstoned identifier cannot be committed
  by a late write.

The lifecycle remains single-instance and local-filesystem based. Distributed
rate limiting and scheduled deployment jobs belong to the release phase.

## Person B: frozen protocol and recruitment readiness

- Promote the bilateral A/B protocol to frozen v0.2.
- Freeze 12 planned cases, six per direction, with at least three independent
  relevant ratings per case and a planned pool of 6-8 adult reviewers.
- Define the language-only control, six scored criteria, five severe-risk flags,
  eligibility, exclusions, consent scopes, withdrawal, assignment, privacy,
  retention, and reporting limits.
- Add a public-safe recruitment pack and machine-readable status.
- Record `pending_human_activation` until a real human coordinator provides an
  approved private contact route and performs outreach.

No identity, contact detail, consent record, assignment key, raw response, or
claim of active recruitment is committed.

## Exit criteria

Focused RED-to-GREEN tests cover purge, deletion, rate limiting, late writes,
safe API errors, and evaluation structure. Full repository gates pass, and the
local Day 7 record contains only verified evidence.
