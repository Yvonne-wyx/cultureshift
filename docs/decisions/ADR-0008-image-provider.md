# ADR-0008: Fixture-only image provider

## Status

Accepted on 2026-08-23 for Day 12 fixture development.

## Context

Day 12 needs a provider-neutral background-generation boundary and deterministic composition,
but no live image provider, paid budget, privacy configuration, or provider data terms have been
approved. Brand Lock forbids an image model from rendering or redrawing Logo, product name,
product UI, statistics, product claims, or long advertisement copy.

## Decision

Use only `FixtureImageProvider`. It runs offline, emits a deterministic 1600 x 900 PNG from fixed
geometry, and accepts a structured request that rejects protected content. Pillow separately
composes the registered Logo, product UI, approved copy, CTA, and fixture disclosure.

Normal mode does not fall back to the fixture provider. No live SDK, credential, remote call, or
provider-specific prompt is introduced under this decision.

## Approval gates for a live provider

A later decision must record and approve the provider, background-only enforcement, reference
image behavior, brand-safety controls, processing region, retention/training policy, deletion,
price and budget owner, output licence, failure handling, and evaluation evidence. It must retain
the same deterministic protected-layer boundary.

## Consequences

Day 12 and CI remain deterministic, offline, reproducible, and honest about fixture execution.
The implementation cannot make claims about live image quality or provider fitness. Full export
and provider comparison remain later work.

## Day 13 export boundary

Day 13 adds read-only export of an already persisted fixture composition. It does not generate a
new background, extend artifact retention, mutate the run, or select a live provider. Before PNG
delivery, the server verifies the opaque artifact identifier, 24-hour TTL, byte size, SHA-256,
PNG decoding, and fixed 1600 x 900 dimensions against the immutable public composition summary.
The JSON attachment is a canonical serialization of only that bounded public summary.

Logo and product UI continue to resolve from the closed fixture registry through confirmed Brand
Lock identifiers. Public upload is limited to the authorized source advertisement and cannot
replace a locked Logo, product UI, or layout template. Golden decoded-RGBA checks, fixed geometry,
and deterministic English/Simplified Chinese wrapping provide technical preservation evidence;
they are not cultural, legal, brand, performance, or production approval. A live image provider
still requires a separate approved ADR satisfying every gate above.
