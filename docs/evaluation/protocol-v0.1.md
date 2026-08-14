# CultureShift Bilateral Evaluation Protocol v0.2

## Status and version

- Protocol version: 0.2
- Status: frozen
- Recruitment status: pending human activation; no outreach evidence is recorded
- Scope: static advertisements for AI software/apps, China to UK and UK to China only

This protocol freezes the study before any score is collected. It claims no
participant, response, metric, cultural conclusion, or completed recruitment.

## Evaluation question

For each supported direction, which blinded variant is more suitable for
continued accountable human review while preserving verified brand truth and
exposing evidence, uncertainty, and limitations?

Reviewer observations are not cultural facts. The study does not provide
automated cultural validation and does not establish legal compliance or
performance uplift.

## Materials and eligibility gate

The control is a language-only baseline: a mechanical translation that keeps
the source narrative, scenario, trust information, benefit order, CTA meaning,
and layout. The candidate is CultureShift's one preregistered localized concept.
Both variants use the same authorized source, exact Brand Lock, direction,
category, canvas, and static-ad format. A changed or missing locked field blocks
the comparison.

## Sampling and assignment

The planned set contains 12 cases, six per direction. Each case requires at
least three independent target-context-relevant ratings. The planned pool is
6-8 reviewers, with balanced assignments so no reviewer must rate every case.
China-to-UK and UK-to-China results are analyzed separately before any optional
combined descriptive summary. This convenience sample supports no population
claim or significance test.

## Blinded A/B procedure

1. Assign randomized A/B labels that conceal workflow, author, provider, and prompt.
2. Balance left/right presentation order within each direction.
3. Keep the private randomization seed outside Git and outside reviewer materials.
4. Present source, exact Brand Lock, both variants, rule IDs, pending hypotheses,
   evidence references, warnings, and limitations.
5. Score each rubric criterion from 1 to 5 and record the five Boolean severe-risk flags.
6. Ask for overall preference only after the Brand Lock check.
7. Store only a study ID, direction, randomized order, scores, flags, preference,
   optional minimized rationale, consent state, and withdrawal state.
8. Analyze each direction separately; never collapse both directions into a
   single claim of cultural suitability.

## Evaluation rubric

The machine-readable source is `rubric-v0.1.json`. It freezes six five-point
criteria and five Boolean severe-risk flags. A score is one reviewer's bounded
observation, not a population estimate, cultural truth, legal judgment, or
campaign-performance prediction.

## Decision rules

- Brand Lock failure blocks preference selection and returns the case for correction.
- Any severe-risk flag requires human adjudication before the case can contribute
  to a validated-release gate.
- Report distributions and preference counts by direction without unsupported
  statistical significance.
- Ties, mixed evidence, or unresolved safety concerns remain unresolved.
- A preferred variant remains pending accountable human approval and retains
  hypotheses, warnings, and limitations.

## Consent and withdrawal

Participation is voluntary. Consent separately covers participation, storage of
raw responses, anonymized aggregate reporting, public attribution, and quotation.
A reviewer may participate without agreeing to identification, attribution, or
quotation. Only responses with consent for anonymized aggregate reporting may
enter public statistics or validated-release gate counts.

A reviewer may skip a question or withdraw before the stated aggregate-freeze
deadline. Before participation, the human coordinator must disclose purpose,
tasks, duration, data fields, foreseeable discomforts, compensation terms if
any, private contact and complaint routes, retention, deletion, and the limit
that a published non-identifiable aggregate may no longer permit removal of one
contribution.

## Recruitment structure

Recruit against relevant language, living, advertising, design, or product
experience rather than nationality. Screen only adult reviewers for direction
familiarity, language comfort, role relevance, and conflicts of interest. No
reviewer represents an entire country or culture.

Recruitment may start only when the activation requirements in
`recruitment-status.json` are genuinely satisfied by a human coordinator. The
public repository contains no invitation list, contact detail, reviewer
identity, consent record, assignment key, or raw response.

## Privacy and data handling

The human coordinator keeps identities and contact details in a protected vault,
separate from random reviewer IDs and responses. Minimize free text; prohibit
secrets and private client content; restrict access; set deletion deadlines; and
never commit private recruitment or evaluation data. Public evidence may contain
only consented, aggregated, non-identifying results after disclosure review.

## Limitations

This frozen protocol and recruitment-ready package are not a completed human
evaluation. Feedback may test pending hypotheses and reveal usability concerns,
but it cannot certify cultural correctness, representativeness, accessibility,
legality, or commercial uplift. Results remain context-specific and require
accountable human interpretation.
