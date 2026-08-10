# CultureShift MVP specification

## Product problem

Teams adapting a static advertisement for an AI software product between China and the UK need a structured way to explore localization while preserving verified brand truth. CultureShift organizes that exploration; it does not replace local research, professional advice, or accountable human review.

## Target users

The MVP supports brand, creative, and localization practitioners who are authorized to use the submitted material and who can arrange qualified human review in the target context.

## Supported scope

- Creative format: static advertising creatives only.
- Product category: AI software and AI applications only.
- Directions: China to UK and UK to China only.

## Supported inputs

- An authorized static advertising creative and its extracted or supplied text.
- Verified product facts and real product UI references.
- A Brand Lock declaration covering every immutable and localizable field.
- Source provenance, rights, privacy constraints, and target direction.
- Optional evidence for hypothesis-led localization reasoning.

Input acceptance does not establish copyright permission, cultural validity, or legal compliance. Missing authority, provenance, or required Brand Lock information causes the workflow to fail closed or return for human resolution.

## Supported outputs

- A proposed static advertising creative for the supported target direction.
- A record of preserved Brand Lock fields and localized fields.
- `CulturalHypothesis` records linked to their evidence, uncertainty, and validation requirements.
- Provenance and rights references carried forward from inputs and generated material.
- Review status and unresolved warnings.

Outputs are proposals for creative reasoning and localization exploration. They do not certify cultural correctness, local acceptance, legal compliance, or campaign performance.

## End-to-end workflow

1. Ingest authorized material and record provenance, privacy, and rights constraints.
2. Extract candidate content as untrusted data.
3. Build a brand-locked representation and resolve missing or conflicting lock information.
4. Create evidence-linked `CulturalHypothesis` records for any cultural inference.
5. Produce a proposed static transformation without changing locked fields.
6. Apply privacy, licensing, public-boundary, and scope checks.
7. Present the proposal, provenance, hypotheses, uncertainty, and warnings to a human reviewer.
8. Permit export or public-demo use only after explicit human approval and applicable rights checks.

## Product guarantees

Within the MVP contract, CultureShift must:

- preserve locked fields or fail closed;
- label cultural inferences as `CulturalHypothesis` records or explicitly as hypotheses;
- retain traceability from evidence and source material to relevant outputs;
- expose uncertainty and unresolved validation requirements;
- exclude prohibited categories and unsupported directions or formats;
- require human approval before an output is treated as approved or publicly displayed.

These are process guarantees, not guarantees about cultural, legal, or commercial outcomes.

## Non-goals

The MVP does not support dynamic, video, audio, interactive, or personalized advertising; products outside AI software/apps; directions other than China to UK or UK to China; autonomous publishing; automated cultural validation; legal certification; performance prediction; or guaranteed uplift. Politics, medical, financial, gambling, tobacco, and child-targeted advertising are excluded.

The specification does not select providers, application frameworks, persistence systems, authentication, analytics, or deployment infrastructure.

## Human-review boundary

The system may organize evidence, formulate hypotheses, and propose transformations. A human reviewer remains responsible for verifying brand truth, evaluating hypotheses with appropriate target-context research, resolving Brand Lock conflicts, confirming rights and privacy authority, obtaining legal advice where needed, and approving use or public display. A generated output is never implicitly approved.

## MVP acceptance boundary

An MVP workflow is acceptable only when it accepts an in-scope authorized input, preserves Brand Lock, represents each cultural inference as a traceable hypothesis, returns a static proposal with uncertainty and review state, fails closed on unresolved scope or rights conflicts, and requires human approval. Quality claims, market evidence, cultural findings, automated validation, and campaign results are outside this acceptance boundary.
