# Examples (v2.0.0)

## Simple
`simple-library-reservation.json`: reserve one physical book copy.

## Intermediate
`intermediate-cafe-pickup-order.json`: paid cafe order becomes a kitchen ticket and prepared food.

## Advanced
`advanced-online-return-refund.json`: long-running return and refund process with inspection, money movement, and idempotency.

Notes:
- Anti-golden traces use the prefix `antitrace.` (lowercase).
- Examples include optional `journey.flow` and optional `step.stateTransitions` fields to demonstrate richer representations.
