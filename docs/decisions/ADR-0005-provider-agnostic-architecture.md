# ADR-0005: Provider-agnostic architecture

## Status

Accepted

## Context

The product and safety contracts must remain valid before implementation technologies or service providers are evaluated.

## Decision

Architecture is defined through logical responsibilities, data contracts, trust boundaries, and failure behavior. T02 selects no model, extraction service, database, hosting provider, generation service, analytics system, authentication system, framework, or deployment stack.

## Consequences

Future provider selection must satisfy these contracts and receive a separate decision. T02 does not imply provider compatibility, procurement, or approval.
