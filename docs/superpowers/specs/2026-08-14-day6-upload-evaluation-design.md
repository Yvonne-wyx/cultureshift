# Day 6 Secure Upload and Evaluation Protocol Design

**Date:** 2026-08-14  
**Owners:** Person A (Engineering / AI / Backend) and Person B (Product / Frontend / Research)  
**Tracking:** GitHub Issue #5

## Goal

Deliver the Day 6 boundary as a secure, private temporary upload path plus a frozen evaluation-protocol draft. The implementation remains deliberately smaller than the full T04/T12 lifecycle: Day 7 owns purge, deletion, rate limiting, late-response protection, and actual recruitment.

## Person A: bounded temporary asset upload

### API

`POST /api/v1/assets` accepts the request body as raw bytes. Required headers are:

- `Content-Type`: exactly `image/png` or `image/jpeg`;
- `X-Provenance-Ref`: a public-safe provenance reference;
- `X-Rights-Ref`: a public-safe rights reference.

The endpoint does not accept or use a client filename. It streams at most 10 MiB, rejects empty content, validates PNG/JPEG magic bytes, and requires the detected type to match the declared type. Stable errors are `unsupported_asset_type`, `asset_type_mismatch`, `asset_empty`, `asset_too_large`, `invalid_asset_metadata`, and `asset_storage_failed`. Errors never echo content, headers, local paths, or exceptions.

### Storage

`TemporaryAssetStore` receives an explicit private root. The default app reads `CULTURESHIFT_TEMP_ASSET_DIR`; missing or blank configuration fails closed. Tests inject a temporary root.

Storage assigns a UUID, writes `<uuid>.part` with exclusive creation, then atomically replaces it with `<uuid>.<png|jpg>`. It returns metadata only after the final file exists. The public response contains a `source_ad` `AssetRef`, byte size, UTC creation time, and `expires_at = created_at + 24 hours`. The endpoint never serves bytes back and does not persist raw content or client metadata in SQLite.

## Person B: frozen evaluation protocol v0.1

Create a public-safe protocol package under `docs/evaluation/`:

- a machine-readable rubric containing six criteria on a five-point scale;
- a human-readable blinded A/B protocol for both supported directions;
- consent, withdrawal, privacy-minimization, reviewer-screening, and recruitment-readiness sections;
- a clear statement that recruitment is not active and no personal data is collected in Day 6.

Criteria cover Brand Lock preservation, language naturalness, task clarity, traceability, safety/misleadingness, and overall preference. Cultural responses are reviewer observations used to assess pending hypotheses, not cultural facts or automated validation. The protocol defines randomized A/B labels, balanced order, separate directional analysis, a Brand Lock fail-closed rule, and no performance-uplift inference.

## Testing and limits

Use focused RED→GREEN tests for byte detection, size enforcement, metadata validation, atomic storage, safe API errors, and protocol structure. Then run one complete repository verification. Add no runtime dependency, UI, provider, network call, recruitment action, deletion, purge, rate limit, or Day 7 behavior.

## Exit criteria

Day 6 is complete when bounded PNG/JPEG uploads produce private temporary assets and public-safe metadata, invalid inputs fail closed, protocol v0.1 is structurally frozen for both directions, all repository gates pass, and the local Day 6 record reflects actual evidence.
