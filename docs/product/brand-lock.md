# Brand Lock contract

Brand Lock is the fail-closed contract that separates immutable brand truth and creative structure from the limited fields that may be localized. It applies before, during, and after any transformation.

## Immutable elements

| Element | Why it is locked |
| --- | --- |
| Logo | Preserves the authorized brand identifier and its integrity. |
| Product name | Prevents substitution or invention of product identity. |
| Verified product facts | Prevents localization from changing substantiated claims. |
| Real product UI | Prevents fabricated interfaces or product capabilities. |
| Benefit order | Preserves the brand-approved hierarchy of benefits. |
| CTA action meaning | Prevents a call to action from becoming a different commitment or transaction. |
| Layout template | Preserves the approved structural composition. |

Locked does not mean that a component is true or authorized merely because it was supplied. Verification and provenance remain required.

## Localizable elements

Only the following categories may change, and only within verified facts, rights, safety, and layout constraints:

| Element | Why localization is allowed |
| --- | --- |
| Narrative | The framing may be explored for the target context without changing brand truth. |
| Use scenario | An in-scope scenario may be proposed when it remains accurate and supportable. |
| Trust information | Relevant verified trust information may be selected or explained; it may not be invented. |
| Language | Wording may be translated or adapted while preserving meaning and claim strength. |

Localization permission is not evidence that a proposed change is culturally appropriate. Any cultural rationale remains a `CulturalHypothesis` requiring review.

## Conceptual representation

Each represented element must carry, conceptually:

- `field`: stable field identity;
- `value`: current value or reference;
- `lock_status`: `locked` or `localizable`;
- `provenance`: source or evidence reference;
- `verification_status`: `verified`, `unverified`, or `conflicted`.

Downstream components must preserve these attributes and record whether each value was retained, proposed for localization, rejected, or escalated. This is a logical contract, not a final application schema.

## Conflict behavior

If a requested transformation would alter a locked element, weaken its meaning, detach it from provenance, or exceed its verification status, processing must fail closed for that change. The system must preserve the original value and surface the conflict for explicit human resolution. It must never silently unlock, rewrite, reorder, replace, or omit a locked element.

Human resolution may correct source data or provide a newly verified Brand Lock declaration. It does not permit downstream components to infer an exception. Any approved contract change must be explicit, traceable, and revalidated before transformation continues.
