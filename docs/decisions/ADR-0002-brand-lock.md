# ADR-0002: Brand Lock

## Status

Accepted

## Context

Localization can damage brand truth if identity, facts, UI, benefit hierarchy, CTA meaning, or structure changes implicitly.

## Decision

Logo, product name, verified product facts, real product UI, benefit order, CTA action meaning, and layout template are locked. Only narrative, use scenario, trust information, and language are localizable. Conflicts fail closed or require explicit human resolution.

## Consequences

Every downstream representation carries lock, provenance, and verification state. Transformation flexibility is deliberately limited, and silent relaxation is prohibited.
