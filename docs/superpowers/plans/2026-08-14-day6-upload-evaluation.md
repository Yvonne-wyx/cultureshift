# Day 6 Secure Upload and Evaluation Protocol Plan

**Issue:** #5  
**Execution:** main agent only; two focused TDD lanes; one final full verification; at most one consolidated repair pass.

## Task 1 — Person A secure upload

- Add failing unit tests for MIME detection, mismatch, empty/oversize bodies, public-safe metadata, atomic filenames, and 24-hour expiry.
- Implement a dependency-free `TemporaryAssetStore` and upload result contract.
- Add failing API tests for success and stable non-echoing failures.
- Implement `POST /api/v1/assets` with injected storage and environment-backed default configuration.
- Run focused Python tests and Ruff.

## Task 2 — Person B evaluation protocol

- Add failing structural tests for rubric version, six criteria, five-point scale, both directions, randomized blinded A/B presentation, consent/withdrawal/privacy, inactive recruitment, and prohibited claims.
- Add `docs/evaluation/rubric-v0.1.json` and `docs/evaluation/protocol-v0.1.md`.
- Run focused protocol tests and Ruff.

## Task 3 — Convergence and evidence

- Regenerate JSON Schema and TypeScript declarations if the public contract changes.
- Run one complete Python/web/contracts/build/audit/public-boundary verification.
- Commit and fast-forward local main.
- Generate `D:\create\Diversity\Day6.docx` from the Day 5 format and structurally audit it; render if LibreOffice is available.
- Request explicit authorization before publishing GitHub main; publish fail-closed against the known remote SHA and verify exact tree equality.
