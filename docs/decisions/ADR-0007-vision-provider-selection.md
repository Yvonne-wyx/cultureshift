# ADR-0007: Vision provider selection

## Status

Accepted on 2026-08-16.

## Context

Day 8 needs a provider-neutral analysis boundary without sending user assets to
a live service. The dated comparison in
`docs/research/vision-provider-comparison-2026-08-16.json` reviews official
public information for OpenAI API, Google Vertex AI, and Amazon Bedrock. Vendor
terms, regions, features, and prices can change, so this record is not a
procurement approval.

## Decision

Approve `FakeProvider` only for deterministic fixture development and CI. No
live provider is approved. Do not add credentials, provider SDKs, paid calls, or
live-data paths under this decision.

## Approval gates

A later live-provider proposal must name and satisfy all of these gates:

1. accountable privacy owner;
2. explicit storage and processing-region requirement;
3. verified retention or zero-retention configuration for every used feature;
4. accountable budget owner;
5. dated pricing refresh and bounded cost estimate;
6. separate implementation approval with safety and schema evaluation evidence.

## Consequences

Tests remain offline, deterministic, and vendor-neutral. OpenAI API, Google
Vertex AI, and Amazon Bedrock remain research candidates only. Any future live
selection requires a new ADR and must preserve the same safety, privacy, Brand
Lock, and human-review boundaries.
