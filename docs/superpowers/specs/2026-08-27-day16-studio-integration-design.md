# Day 16 Connected Fixture Studio Design

**Date:** 2026-08-27
**Plan item:** Day 16 / T10
**Issue:** [#15](https://github.com/Yvonne-wyx/cultureshift/issues/15)
**Roles:** Person A (Engineering/AI/Backend) and Person B (Product/Frontend/Research)

## Summary

Day 16 connects one fixture-only Next.js Studio to the complete FastAPI workflow built through Day 15. A user selects one of the two authorized Orbit AI directions, supplies an authorized source ad and public provenance/rights references, confirms the analyzed Brand Lock, generates and reviews version 1, optionally requests the single structured revision, compares versions 1 and 2, exports the selected composition, and deletes the uploaded source asset.

The design deliberately uses one page, one pure state machine, and one typed API client. Run and asset capabilities remain in React memory only. There is no account system, server-side web session, browser persistence, live provider, background queue, or Day 17 browser E2E expansion.

## Approved product boundary

### Person A

- Connect the browser client to every existing public workflow endpoint required by the Studio.
- Keep the Run capability and asset-delete capability ephemeral and scoped to the current page session.
- Add exact local-development CORS origins rather than a wildcard.
- Extend composition export only enough to select result version 1 or 2.
- Preserve bounded public errors, artifact integrity checks, capability subject checks, and current 15-minute Run capability expiry.

### Person B

- Add one `/studio` route for both fixture directions.
- Provide authorized upload inputs, analysis and generation progress, Brand Lock confirmation, results, comparison, structured feedback, retry state, export, and source-asset deletion.
- Reuse the existing authorized Orbit AI fixture Brand Lock and evidence rather than creating an arbitrary-brand editor.
- Keep the fixture disclosure, human-review status, Critic outcome, rule IDs, evidence references, warnings, and pending cultural hypotheses visible.

### Explicit non-goals

- No live or paid provider, arbitrary product/brand onboarding, free-form prompt execution, or user-supplied logo/UI/layout assets.
- No account, login, refresh-token, server-side session store, browser storage, analytics, telemetry, or multi-user collaboration.
- No polling, queue, worker, websocket, streaming generation, or automatic retry loop.
- No approval, publishing, deployment, performance prediction, legal validation, or cultural validation claim.
- No full browser E2E or security regression campaign; those remain Day 17 and Day 18 work.
- No deletion claim beyond the uploaded source asset addressed by its exact delete capability.

## Selected architecture

### Direct browser API client

The browser calls FastAPI directly through a small `StudioApiClient`. Its base URL comes from `NEXT_PUBLIC_CULTURESHIFT_API_URL` and defaults to `http://127.0.0.1:8000` for local development. The client owns request construction and bounded response decoding, but it does not own UI state.

FastAPI adds `CORSMiddleware` with only these development origins by default:

- `http://localhost:3000`
- `http://127.0.0.1:3000`

An optional comma-separated environment value may replace that list with explicit origins. Wildcards and credentialed CORS are rejected. Allowed methods are `GET`, `POST`, and `DELETE`; allowed request headers are `Authorization`, `Content-Type`, `Idempotency-Key`, `X-Provenance-Ref`, and `X-Rights-Ref`.

This is smaller than a Next.js backend-for-frontend and matches the existing short-lived capability model. A BFF and persistent session store would add a new authentication subsystem without helping the fixture-only technical preview.

### Ephemeral Studio session

`StudioSession` is React state and contains only the data needed by the current page:

- direction and the selected immutable fixture bundle;
- source `File` preview URL and public provenance/rights inputs;
- uploaded source `AssetRef` and its delete capability;
- Run ID and Run capability;
- current workflow phase and the latest public API outputs;
- one feedback idempotency key and, only when eligible, one retry idempotency key;
- version 1 and version 2 composition object URLs created from authenticated export responses.

The session is never written to local storage, session storage, cookies, IndexedDB, query parameters, history state, logs, error text, or committed fixtures. Object URLs are revoked when replaced, after deletion, and on unmount. Reloading the page intentionally loses the Run capability; the UI explains that the session expired and offers a clean restart rather than pretending recovery is possible.

The API client never exposes tokens through error objects. It adds the Run token only as a Bearer header and the delete token only to the exact asset DELETE request. Idempotency keys are generated with `crypto.randomUUID()`, retained for exact replay of the same logical request, and replaced only when the user begins a genuinely new eligible operation.

## Studio flow

### 1. Configure and upload

The user selects China to UK or UK to China. The selected fixture supplies the authorized Orbit AI product facts, logo/UI asset IDs, benefit order, CTA meaning, layout template, and permitted localizable fields. The page does not allow switching those protected assets to arbitrary values.

The upload form requires:

- one PNG, JPEG, or WebP source ad no larger than 10 MiB;
- a public provenance reference;
- a public rights reference;
- an explicit checkbox confirming authority to process the source.

The client sends the file as the raw request body with its media type and the two metadata headers. A successful response stores the public asset metadata and delete capability in memory. A Run is then created in fixture mode with that source reference and the selected fixture Brand Lock.

### 2. Analyze and confirm Brand Lock

The page calls `/analyze` once and displays the returned detected locale, protected fields, warnings, and pending hypotheses. The existing `BrandLockForm` remains the editable-before-confirmation surface, but Day 16 supplies it with the live analysis result and the real confirmation callback.

Confirmation sends the exact displayed Brand Lock. After success, all protected fields are read-only. Any semantic drift, stale state, capability mismatch, or unsupported field fails closed with a bounded UI message.

### 3. Generate, compose, and review

One explicit “Generate fixture proposal” action runs the existing sequential calls:

1. `/draft`
2. `/composition`
3. `/critic`

The state machine exposes the active step and prevents duplicate actions. Existing idempotent backend behavior handles an exact repeat after a network interruption. The browser does not poll and does not automatically retry an unknown outcome.

When Critic returns `ready`, the page fetches the authenticated version-1 PNG and displays:

- source preview beside version 1;
- generated headline, body, CTA, and target locale;
- protected Brand Lock values;
- Critic status and bounded findings;
- rule IDs, evidence references, warnings, disclosure, and pending hypotheses.

A Critic reject becomes a final failure and never appears as an approved result.

### 4. One revision and bounded retry

The feedback panel appears only for a ready version 1. It contains:

- `shorten_headline` and `shorten_body` checkboxes;
- a bounded feedback context field that is never executed as an instruction;
- one submit action disabled when no structured change is selected or another operation is active.

Success stores the `RevisionCompleted` response and loads the authenticated version-2 PNG. The comparison surface shows immutable version 1 beside version 2, with distinct version labels, hashes, Critic evidence, and `human_revision_count = 1`. Replaying the same success replaces the same version-2 state and never appends version 3.

`revision_limit_reached`, `idempotency_conflict`, and `operation_in_progress` remain distinct conflicts. A retry control appears only after a server-authorized `failed_retryable` outcome. It reuses the stored revision request and sends no new feedback or change selection. Safety, cultural-human-review, exhausted, and final failures never enable retry.

### 5. Export and delete

The existing export URLs accept an optional `result_version=1|2` query parameter. Omitting it remains backward compatible and selects version 1. Version 2 is available only when the persisted Day 15 revision exists.

`CompositionExportService` resolves the selected immutable composition summary, loads the addressed artifact, and retains all current ID, SHA-256, byte-size, media-type, and 1600 x 900 checks. An absent version maps to `composition_unavailable`; an expired, missing, or inconsistent artifact maps to the existing bounded unavailable error. No filesystem path enters a response.

The Studio exposes PNG and JSON downloads for each visible version. It performs the authorized fetch, creates the browser download from returned bytes, and never places a capability in an anchor URL.

“Delete uploaded source and reset” sends DELETE with the exact asset-delete capability. On 204 it revokes object URLs and clears the entire in-memory Studio session. The copy states precisely that it deletes the uploaded source asset, not the Run, generated metadata, or already expired artifacts. The action is never automatic.

## Components and file boundaries

### Backend

- Modify `src/cultureshift/app.py` for strict CORS configuration and the export query parameter.
- Modify `src/cultureshift/composition_export.py` to resolve version 1 or the persisted version 2.
- Modify `tests/test_app.py` for CORS, version selection, capability isolation, and public error mapping.
- Modify `tests/test_composition_export.py` for version-2 integrity, absent-version, and artifact-unavailable cases.

No contract schema change is required because `result_version` is a bounded query input and both export payloads reuse `CompositionGenerated`.

### Frontend

- Create `apps/web/src/studio/studio-api.ts` for typed HTTP and binary-download calls.
- Create `apps/web/src/studio/studio-state.ts` for the pure discriminated state machine and derived action guards.
- Create focused tests beside both modules.
- Create `apps/web/src/app/studio/page.tsx`, a client component, and a scoped CSS module.
- Reuse existing fixture loading, `BrandLockForm`, evidence components, generated contracts, and revision-flow literals where practical.
- Add a visible link from the fixture lab home page to `/studio`.

The page may split presentation-only sections into focused components if the main client component becomes difficult to test, but it must not introduce a general component framework or unrelated restyling.

## State model

The state machine uses exact phases:

- `configure`
- `uploading`
- `analyzing`
- `awaiting_brand_lock`
- `generating_draft`
- `composing`
- `reviewing`
- `ready_v1`
- `submitting_revision`
- `ready_v2`
- `retryable_failure`
- `conflict`
- `final_failure`
- `deleting`

Every transition consumes a typed event and either advances with a public response or records one bounded error code. Derived guards control upload, confirmation, generation, feedback, retry, export, and delete actions. Unknown or impossible events leave the state unchanged in production and fail tests during development.

## Error handling

The API client accepts only JSON objects or expected binary media types. Non-JSON errors, malformed success bodies, network failures, and unexpected status codes become generic `service_unavailable` without copying response bodies or exception strings.

UI categories are:

- validation: file, provenance, rights, or structured feedback input must be corrected;
- session: invalid, expired, wrong-scope, or wrong-subject capability requires a clean restart;
- conflict: stale state, immutable Brand Lock, in-progress operation, idempotency conflict, or revision limit;
- retryable: only the bounded server-authorized revision failure enables retry;
- final: blocked content, Critic reject, safety failure, or exhausted failure;
- artifact: selected export is absent, expired, missing, or fails integrity checks;
- service: network or sanitized unexpected server failure.

No message echoes source bytes, raw feedback, tokens, local paths, provider details, or exception text. Cultural hypotheses remain hypotheses pending human review in every phase.

## Test strategy

Use strict RED-GREEN-REFACTOR cycles.

### Person A

- CORS permits the two exact default local origins and required methods/headers, rejects an unrelated origin, and never enables credentialed wildcard access.
- Export defaults to version 1, explicitly exports version 1, exports persisted version 2, and rejects missing version 2.
- Version-2 PNG/JSON retain artifact identity, SHA-256, dimensions, content type, attachment headers, and capability subject isolation.
- Malformed version input, wrong capability, absent artifact, and corrupt artifact remain bounded and leak no private data.
- API client tests assert exact paths, methods, headers, bodies, query parameters, binary handling, and sanitized errors.
- Token values are absent from URLs, persisted browser APIs, thrown messages, and rendered text.

### Person B

- Both fixture directions configure the correct immutable Brand Lock and target locale.
- Upload is gated by supported type, size, metadata, and authority confirmation.
- The state machine follows the exact upload-to-ready sequence and disables duplicate actions.
- Brand Lock is editable only before confirmation.
- Ready version 1 shows source/results/evidence; revision success shows exactly versions 1 and 2.
- Structured feedback deduplicates selections, preserves its idempotency key on replay, and cannot request version 3.
- Conflict classes remain distinct; only server-authorized retryable failure enables retry.
- Export selects the clicked visible version and never exposes a token in the download URL.
- Successful source deletion revokes previews and resets the session.
- Accessibility tests cover labels, progress status, error alerts, disabled states, keyboard-usable controls, and meaningful image alternatives.

### Release gate

- Full Python suite with an explicit writable pytest base temp.
- Ruff across the repository.
- Python contract export check and generated TypeScript contract check.
- Full Vitest, ESLint, TypeScript, and webpack production build.
- Public-boundary scan, `git diff --check`, and clean repository status except intended Day 16 files.
- A focused integration test proves both directions traverse the connected client contract through version 1; revision comparison is covered without claiming Day 17 full browser E2E.

## Delivery and publication

Day 16 delivery contains:

- GitHub Issue #15 and this approved design;
- a task-by-task implementation plan;
- focused TDD commits for backend integration, client/state, and Studio UI;
- `Day16.docx` in the private parent folder using the established Day 15 format;
- a non-force update of `main` only after rechecking the remote Day 15 baseline or reconciling a partner commit;
- successful GitHub Actions evidence;
- removal of explicitly named Day 16 test, render, and API-upload temporary directories.

## Acceptance boundary

Day 16 is complete when both authorized fixture directions can use the connected `/studio` flow from source upload through a Critic-reviewed version 1, the single structured revision can present exactly one version 2, selected versions export with integrity checks, the uploaded source can be explicitly deleted, capabilities remain ephemeral and isolated, the complete local release gate passes, `Day16.docx` is visually verified, and the verified tree is published to remote `main` without force.
