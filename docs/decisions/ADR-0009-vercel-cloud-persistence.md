# ADR-0009: Vercel deployment and cloud persistence

## Status

Accepted

## Context

The interactive CultureShift demo combines a Next.js Studio with a FastAPI workflow.
Its local implementation uses SQLite and purpose-limited filesystem storage. Vercel
Functions do not provide a durable shared filesystem, so the local persistence
implementations cannot support a deployed multi-request workflow.

## Decision

Deploy the Next.js frontend and FastAPI backend as two services within one Vercel
project and expose a single public origin. Route `/api/*` to FastAPI and all other
paths to Next.js.

Keep SQLite and filesystem stores for isolated local development and automated tests.
When production environment variables are present, select PostgreSQL for non-sensitive
workflow state and private object storage for authorized source and generated image
artifacts. Provider credentials remain server-side environment variables.

Cloud assets retain the existing 24-hour expiry metadata and explicit deletion
semantics. The migration does not expand the product scope, add accounts, retain raw
OCR output, or weaken capability-token and Brand Lock boundaries.

## Consequences

- Browser API calls use same-origin relative URLs by default.
- Production startup fails closed when durable persistence configuration is incomplete.
- Database and object-store regions should be selected near the Vercel function region.
- Expired-object cleanup requires a bounded scheduled operation in addition to explicit
  user deletion.
- Supabase is the initial managed PostgreSQL and object-storage integration, while
  application interfaces remain provider-neutral.
