# Day 7 Lightweight Implementation Plan

## Task 1 — Person A lifecycle tests and implementation

1. Add failing tests for persisted expiry metadata, idempotent deletion,
   tombstoned late writes, fixed-window rate limiting, startup purge, delete
   capability authorization, and safe 429 responses.
2. Implement the smallest storage, limiter, contract, and API changes.
3. Regenerate JSON Schema and TypeScript contracts.
4. Run focused Python tests and Ruff.

## Task 2 — Person B frozen evaluation package

1. Update structural tests first for protocol v0.2, sampling, severe-risk flags,
   public recruitment materials, and truthful activation status.
2. Update the rubric/protocol and add the public-safe recruitment pack/status.
3. Run focused evaluation tests and Ruff.

## Task 3 — convergence

Run one full Python/web/schema/lint/build/audit/public-boundary verification,
create one focused local commit, then generate and verify Day7.docx. Do not push
without separate authorization.
