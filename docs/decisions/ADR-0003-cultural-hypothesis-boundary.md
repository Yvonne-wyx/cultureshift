# ADR-0003: CulturalHypothesis boundary

## Status

Accepted

## Context

Cultural inference is uncertain and can become stereotyping or an unsupported truth claim when separated from evidence and review.

## Decision

Every cultural inference is represented as a `CulturalHypothesis` or explicitly described as a hypothesis, with target context, evidence references, uncertainty, rationale, validation requirement, and review status.

## Consequences

The system cannot claim automated cultural validation or guaranteed acceptance. Insufficient evidence produces an evidence gap or blocked outcome, and accountable human validation remains required.
