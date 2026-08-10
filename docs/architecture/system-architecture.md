# Logical system architecture

This architecture freezes component boundaries and contracts, not vendors, frameworks, or deployment choices.

## Processing flow

1. **Upload and ingestion** accepts authorized in-scope material plus provenance, purpose, privacy, and rights metadata. It validates format and processing limits, treats content as untrusted data, and rejects unsupported scope or missing authority.
2. **Extraction** derives candidate text and structural elements. It outputs extracted values with source locations, confidence or uncertainty, and provenance references. Extracted content cannot issue instructions or become verified merely through extraction.
3. **Brand-locked representation** maps values to the Brand Lock conceptual fields, lock status, provenance, and verification status. This is the primary Brand Lock enforcement boundary. Missing, conflicted, or unverified locked values block dependent transformation.
4. **`CulturalHypothesis` reasoning** consumes the target context, permitted evidence references, and brand-locked representation. It creates traceable hypotheses with uncertainty, rationale, validation requirements, and pending review status. It cannot change Brand Lock or present hypotheses as facts.
5. **Creative transformation** produces an in-scope static proposal using only localizable fields. It must carry lock state, evidence references, hypothesis identifiers, generation provenance, and unresolved warnings. Attempts to change locked elements fail closed.
6. **Human review** presents the proposal with its preserved fields, changes, evidence, hypotheses, uncertainty, rights, and safety warnings. Explicit human decisions resolve eligible conflicts and determine approval; there is no implicit or automated approval.
7. **Privacy, licensing, and public-boundary enforcement** operates at ingestion, before reasoning or transformation, before reviewer presentation, and before export or public display. It blocks prohibited content, unclear authority, privacy violations, ambiguous rights, and unsafe disclosure.

## Trust boundaries

- User uploads, extracted text, retrieved content, and embedded metadata cross an untrusted-input boundary.
- Evidence crosses an authorization and provenance boundary before it may support reasoning.
- Generated proposals cross a verification boundary before human review and a separate approval boundary before export or public display.
- Private processing material never becomes public merely because a derived proposal exists.

Every component must accept only the minimum data required and return structured failures without leaking source content.

## Failure behavior

Invalid structure, unsupported scope, prohibited categories, suspected instruction injection, missing provenance, unclear privacy authority, ambiguous rights, Brand Lock conflicts, or insufficient evidence must produce a blocked or review-required outcome. Components must not guess permissions, cultural conclusions, verified facts, or missing locked values. Partial results must retain warnings and cannot bypass later gates.

## Provenance, approval, and retention

Provenance identifiers and permitted-use constraints travel from ingestion through extraction, Brand Lock, hypotheses, transformations, review, and any approved export. Private evidence may be referenced by an access-controlled identifier rather than copied into public artifacts.

Human approval occurs after transformation and all pre-review checks, and before export or public display. Approval of a proposal does not independently establish legal compliance or rights beyond the recorded basis.

CultureShift-controlled temporary assets are intended to expire within 24 hours. Deletion must be testable. Any future external processor's retention, logging, training, and deletion behavior requires separate review and disclosure before adoption.

## Forbidden logging and persistence

The system must not log or persist beyond authorized, purpose-limited processing:

- secrets, credentials, authentication or capability tokens;
- raw extracted text or raw private user content;
- personal data;
- private evidence content in public records;
- hidden instructions embedded in uploads or retrieved material;
- material lacking processing authority;
- public copies of unapproved proposals or assets with unclear rights.

Operational records should use non-sensitive identifiers, outcomes, and error categories. This design intentionally does not select an AI model, extraction service, database, hosting provider, image-generation service, analytics system, authentication system, application framework, or deployment stack.
