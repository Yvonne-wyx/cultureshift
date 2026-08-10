# Cultural safety contract

## Required reasoning boundary

Every cultural inference must be represented as a `CulturalHypothesis` or explicitly described as a hypothesis. CultureShift does not know cultural truth and does not perform automated cultural validation.

## Evidence and hypothesis

**Evidence** is traceable source material or an observation whose provenance, context, limitations, and permitted use are recorded. Evidence is not automatically representative, current, applicable, or sufficient.

A **`CulturalHypothesis`** is a testable, uncertain proposition about how a creative choice may be interpreted in a defined target context. It is not a fact, audience-wide rule, or approval. Conceptually it includes:

- claim;
- target context;
- evidence references;
- uncertainty;
- rationale;
- validation requirement;
- review status.

This is a logical contract rather than a final software schema.

## Uncertainty and validation

Uncertainty must be explicit and proportionate to the evidence. A hypothesis must identify missing, conflicting, outdated, narrow, or indirect evidence. Validation requirements must name the human research or review needed without claiming it has occurred.

When evidence is insufficient, the system must not fill the gap with a cultural generalization. It must narrow or withhold the hypothesis, label the evidence gap, request appropriate research or human input, and block any dependent claim from being treated as approved.

Human reviewers must assess evidence quality, target-context relevance, potential harm, Brand Lock compatibility, and whether additional local research or professional advice is required. Review status must distinguish pending, rejected, and human-approved states; generation alone never changes that status to approved.

## Stereotyping safeguards

- Define the target context narrowly enough to avoid treating nationality as homogeneous.
- Do not infer preferences or behavior from nationality, ethnicity, language, or other identity alone.
- Do not turn limited observations into population-wide claims.
- Record counterevidence and plausible alternative explanations.
- Avoid essentialist, demeaning, exoticizing, or discriminatory framing.
- Do not simulate consensus or claim guaranteed local acceptance.
- Do not claim automated cultural truth, legal compliance, performance uplift, or campaign success.

## Prohibited MVP categories

The MVP must reject advertising in these categories:

- politics;
- medical;
- financial;
- gambling;
- tobacco;
- child-targeted advertising.

The exclusion applies even when the creative is otherwise a static advertisement or references AI software.
