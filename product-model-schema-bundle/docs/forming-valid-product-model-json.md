# How to Form Valid Product Model JSON (v2.0.0)

## Order of creation

1. Metadata
2. Product description
3. Lexicon
4. Real-world objects
5. Real-world interactions
6. Invariants
7. Network boundaries
8. Objectives
9. Duties
10. Journeys
11. GWT steps
12. UX SLIs/SLOs
13. Golden and anti-golden traces
14. Update records
15. Open questions only when an external clarification is truly needed

## ID rules

Use **stable**, **lowercase**, type-prefixed IDs:

- `duty.reserve-book-copy`
- `journey.reserve-book-copy`
- `step.reserve-copy`
- `slo.confirm-under-1s`
- `trace.successful-book-reservation`
- `antitrace.double-reservation`

Do not rename IDs once published. Create a new artifact and record the replacement in an update entry.

## Duty naming

Use `Verb + Domain Object + Qualifier`.

Good: `Return an eligible delivered item and issue the correct refund`.
Weak: `Customer return flow`.

## GWT quality

Each step should be **atomic**, **observable**, and **testable**.
Avoid implementation-only wording unless it is part of the domain.

Optional but recommended:
- Use `step.stateTransitions` to make implied domain state changes machine-checkable.

## Journey flow

If a journey has meaningful branching (variants, loops, retries, failure paths), add `journey.flow`:
- It makes branching explicit and removes ambiguity about step ordering.

## Network boundary rule

- For **under-1s** real-world interactions, set `separationAllowed=false` unless you have a justified exception.
- If you set `separationAllowed=true` for an under-1s boundary, you must include `exceptionApproval` with approval status, reason, and mitigations.

## Ambiguity rule

If ambiguity remains, create an `openQuestions` item naming the **external fact** needed.
Do not hide uncertainty in vague text.
