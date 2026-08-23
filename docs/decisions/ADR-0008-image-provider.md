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
