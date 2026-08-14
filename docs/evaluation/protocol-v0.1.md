# CultureShift Bilateral Evaluation Protocol v0.1

## Status and version

- Protocol version: 0.1
- Status: frozen draft for later reviewer-readiness checks
- Recruitment status: not active in Day 6
- Scope: static advertisements for AI software/apps, China → UK and UK → China only

This draft freezes study structure, not study findings. No participant, reviewer, response, meeting, metric, or cultural conclusion is claimed.

## Evaluation question

For each supported direction, which of two blinded fixture variants is more suitable for continued accountable human review while preserving verified brand truth and clearly exposing evidence, uncertainty, and limitations?

The exercise captures reviewer observations, not cultural facts. It does not provide automated cultural validation and does not establish legal compliance or performance uplift.

## Materials and eligibility gate

Each comparison must use the same authorized source creative, exact Brand Lock, direction, product category, and static-ad format. Before presentation, the coordinator verifies rights references, fixture watermarking, non-live status, and the absence of private or personal content. A missing or changed locked field blocks that comparison.

## Blinded A/B procedure

1. Assign randomized A/B labels that do not reveal workflow, author, or preferred variant.
2. Use balanced presentation order within each direction so neither screen position is systematically favored.
3. Present the source, exact Brand Lock, two variants, rule IDs, pending hypotheses, evidence references, warnings, and limitations.
4. Ask the reviewer to score each rubric criterion from 1 to 5 and optionally provide a short reason that contains no personal data.
5. Ask for an overall preference only after the Brand Lock check.
6. Store only study IDs, direction, randomized order, scores, preference, optional minimized rationale, consent state, and withdrawal state.
7. Analyze each direction separately; do not pool China → UK and UK → China into a single cultural score.

## Evaluation rubric

The machine-readable source is `rubric-v0.1.json`. It freezes six five-point criteria:

1. Brand Lock preservation
2. Language naturalness
3. Task clarity
4. Evidence traceability
5. Safety and non-misleadingness
6. Overall preference

A score records one reviewer's bounded observation. It is not a population estimate, cultural truth, legal judgment, or campaign-performance prediction.

## Decision rules

- Brand Lock failure blocks preference selection and returns the case for correction.
- Report score distributions and A/B preference counts by direction; do not claim statistical significance without a separately approved analysis plan and adequate sample.
- A preferred variant remains pending human approval and retains all warnings and hypotheses.
- Ties, mixed evidence, or substantive safety concerns produce an unresolved outcome rather than a forced winner.

## Consent and withdrawal

Participation is voluntary. Before any later study, reviewers must receive the purpose, tasks, expected duration, data fields, foreseeable discomforts, compensation terms if any, contact route, retention period, and complaint route. Consent must be affirmative and recorded separately from responses.

A reviewer may skip a question or withdraw before anonymized aggregation. Withdrawal handling must remove the response link and associated identifiable recruitment record according to the later approved operating procedure. Day 6 does not activate collection.

## Recruitment structure

Recruitment status: not active in Day 6. A later coordinator may seek adult professional reviewers with relevant language and target-context experience, disclose conflicts of interest, and avoid protected or sensitive screening questions unless separately justified and approved. Screening assesses role relevance, language comfort, direction familiarity, and conflicts; it does not ask reviewers to represent an entire country or culture.

No invitation list, contact detail, compensation promise, or reviewer identity belongs in this public repository. Actual recruitment begins only after Day 7 authorization, finalized contact/complaint details, consent wording, privacy notice, retention/deletion procedure, and responsible human ownership are in place.

## Privacy and data handling

No personal data is collected by this draft. Later collection must use study IDs, separate contact information from responses, minimize free text, prohibit secrets and private client content, restrict access, define a deletion deadline, and never commit responses or recruitment records to Git. Public evidence may contain only aggregated, non-identifying results after an explicit disclosure review.

## Limitations

This protocol is a readiness artifact, not a completed evaluation. Reviewer feedback can reveal usability concerns and test pending hypotheses, but it cannot certify cultural correctness, representativeness, legality, accessibility compliance, or commercial uplift. Results remain context-specific and subject to accountable human interpretation.
