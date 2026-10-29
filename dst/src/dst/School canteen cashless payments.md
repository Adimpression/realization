# School canteen cashless payments

A secondary school wants to reduce cash handling in the canteen without creating a lunch-time bottleneck or excluding students who forget their cards or phones. The school currently relies on cash payments at every food stall, and staff spend time resolving change shortages and queue disputes during the lunch rush.

## Actors

- school administration
- canteen vendors
- students
- parents
- payment provider

## Objectives

- reduce cash handling during lunch service
- shorten checkout queues
- avoid excluding students who arrive without a charged phone or enough balance

## Capabilities

- student stored-value payment cards
- parent balance top-up portal
- cashier override for exceptions
- daily settlement and transaction reports

## Dependencies

- vendor settlement process
- parent communication and onboarding
- payment devices at every stall

## Constraints

- lunch service cannot slow down
- some students will forget cards or arrive with low balance
- meal service must continue during device or network faults

## Boundaries

- school-to-payment-provider boundary
- school-to-vendor boundary
- parent-to-school support boundary

## States

- meals are paid mostly in cash at each stall
- most stalls accept a school payment card and staff can override exceptions
- stalls require app-based payment only

## Transitions

- introduce stored-value student cards with staff override
- extend the rollout with parent top-ups and settlement reporting
- require app-only cashless payment at every stall
