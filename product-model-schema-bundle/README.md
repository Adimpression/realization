# Product Self-Representation Schema Bundle (v2.0.0)

This bundle provides a **JSON Schema** and companion materials for representing a product as a self-describing system:

- **Duties** (KR titles)
- **User journeys** (KR descriptions)
- **High-fidelity Given–When–Then (GWT) steps**
- **UX SLIs/SLOs** for critical journeys
- **Golden + anti-golden traces**
- **Real-world object/process architecture model**
- **Network boundary rule**: network separation is allowed only when the corresponding real-world process is **>= ~1s** (or explicitly approved as an exception)
- **Update protocol** with compatibility classification

## Contents

```text
product-model.schema.json
product-model.template.json
lexicon.md
semantic-rules.md
update-protocol.md
docs/forming-valid-product-model-json.md
examples/simple-library-reservation.json
examples/intermediate-cafe-pickup-order.json
examples/advanced-online-return-refund.json
examples/README.md
validation/semantic-validator-rules.json
validation/compatibility-checks.json
bundle-manifest.json
```

## What “valid” means

There are two levels of validity:

1. **Schematic validity**: the JSON matches `product-model.schema.json`.
2. **Semantic validity**: the model is *meaningful*:
   duties map to the real world, journeys truly fulfill duties, steps compose journeys, SLOs bind experience, and traces witness correctness and forbidden behavior.

JSON Schema is the skeleton. Semantic rules and the update protocol supply the muscles and immune system.

## What changed in v2.0.0 (vs v1.0.0)

- **ID discipline strengthened**:
  - All artifact IDs are **lowercase** and **type-prefixed**.
  - Anti-golden traces use the prefix `antitrace.` (lowercase).
- Added optional **duty composition** (`dependsOnDutyIds`) and **journey sub-duty calls** (`invokesDutyIds`).
- Added optional **journey flow graph** (`journey.flow`) to represent branches/variants explicitly.
- Added optional structured **state transitions** on steps (`step.stateTransitions`) to reduce ambiguity.
- Added optional **exception approvals** on network boundaries (`boundary.exceptionApproval`) to represent explicit approval when an under-1s interaction must be network-separated.

## Recommended use

1. Start from `product-model.template.json`.
2. Define **real-world objects and interactions** first.
3. Define **invariants**.
4. Define **network boundaries** with real-world timing justification.
5. Define **objectives**.
6. Define **duties** (KR titles).
7. Define **journeys** (KR descriptions).
8. Break journeys into **atomic GWT steps**.
9. Add **UX SLIs/SLOs** for critical journeys.
10. Add **golden and anti-golden traces**.
11. Record an **update entry** for every material change.
12. Validate schema, then run semantic and compatibility checks.
