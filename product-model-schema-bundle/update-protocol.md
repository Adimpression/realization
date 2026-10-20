# Update Protocol (v2.0.0)

This protocol governs changes to the **product model** (not the runtime system). It is designed to prevent accidental loss of product promises.

## Compatibility classes

- **Additive**: adds behavior or model content without changing existing guarantees.
- **Corrective**: clarifies or repairs the model without changing guarantees.
- **Strengthening**: makes an existing guarantee stricter.
- **Weakening**: loosens an existing guarantee; requires migration plan.
- **Breaking**: removes or changes an existing product promise; requires migration plan and approval.

## Stability rules

- **Artifact IDs are stable**. Do not rename IDs to “clean things up”.
- Prefer **deprecate/supersede** over renaming. If you must replace an artifact, create a new ID and record the relationship in an update entry.

## Safe update procedure

1. Identify target artifacts by stable ID.
2. Classify the change (additive/corrective/strengthening/weakening/breaking).
3. Validate against JSON Schema.
4. Resolve references.
5. Run semantic checks.
6. Run compatibility checks.
7. Update traces and invariants if affected.
8. For weakening or breaking changes, record a migration plan (who is affected, how to transition, when to remove old guarantees).
9. For architectural exceptions (e.g., separating an under-1s boundary), record explicit approval and mitigations.

Rule of thumb: a change is breaking if someone can reasonably say,
“the product used to promise X, and now it no longer does.”
