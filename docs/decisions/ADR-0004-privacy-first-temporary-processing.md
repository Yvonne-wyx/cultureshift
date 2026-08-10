# ADR-0004: Privacy-first temporary processing

## Status

Accepted

## Context

Uploads and extracted content may be private, licensed, or personal. Retaining them creates unnecessary exposure.

## Decision

Processing is purpose-limited and data-minimized. CultureShift-controlled temporary assets are intended to expire within 24 hours, deletion must be testable, and raw extracted text, private content, tokens, credentials, and personal data must not be logged.

## Consequences

Components use non-sensitive references where possible. Any future external processor requires separate review and disclosure of retention, training, logging, and deletion behavior.
