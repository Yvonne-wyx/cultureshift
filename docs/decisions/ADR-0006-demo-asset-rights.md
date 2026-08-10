# ADR-0006: Demo asset provenance and rights enforcement

## Status

Accepted

## Context

Repository presence or public availability does not establish permission to reuse, modify, or publicly display an asset.

## Decision

Every demo asset must have machine-readable provenance, rights status, permitted use, derivative-work permission, public-display permission, and attribution requirements. Unknown or ambiguous rights fail closed. Private/customer/user assets cannot become demo assets.

## Consequences

Only rights-cleared assets may enter a public demo. Synthetic assets remain explicitly marked, and the validator rejects incomplete or unsupported permission states without inferring copyright status.
