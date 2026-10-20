# Lexicon

## Duty
A world-anchored obligation or capability the product must support. A Duty is the **KR Title** and should be named as `Verb + Domain Object + Qualifier`.

## User Journey
The canonical end-to-end flow that fulfills one primary Duty. A Journey is the **KR Description**.

## Given–When–Then Step
An atomic behavioral transition: **Given** preconditions, **When** a trigger occurs, **Then** observable postconditions hold.

## UX SLI
A measurable indicator of user-experienced quality: latency, correctness, freshness, recoverability, clarity, or reliability.

## UX SLO
A target threshold for a UX SLI that defines acceptable experience.

## Golden Trace
A concrete end-to-end execution that demonstrates correct behavior.

## Anti-Golden Trace
A concrete execution that demonstrates forbidden, misleading, or unacceptable behavior.

## Real-World Object
A domain entity meaningful outside implementation (e.g., Book Copy, Kitchen Ticket, Return Request).

## Real-World Interaction
A process involving real-world objects (e.g., place hold, prepare food, ship parcel, issue refund).

## Invariant
A product law that must remain true across all valid states and transitions.

## Network Boundary
An architectural separation justified by real-world time, externality, or human/physical delay.
- If the real-world process is **under ~1 second**, separation is normally **forbidden** (must remain causally tight).
- If an under-1s interaction *must* be separated, it requires an explicit **exception approval** in the model.
