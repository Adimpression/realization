# Governed Wasm Hostcall Implementation Status

## Phase 12

Phase 12 completes the intended governed Wasm hostcall subset.

The subset includes `skill.invoke` and `tool.invoke` in
[host_abi.py](host_abi.py). The Wasm runtime in
[wasm_skill_runtime.py](wasm_skill_runtime.py) promotes nested
`nested_effect_traces` and `nested_capability_grants` from brokered Wasm
composition. [host_mediation.py](host_mediation.py) ingests those records into
parent state so Wasm composition remains inside the same constitutional trace
surface as Python execution.

Regression coverage in
[tests/test_host_mediation.py](tests/test_host_mediation.py) includes:

- Wasm `skill.invoke` of an installed governed skill, including nested trace
  and grant ingestion.
- Wasm `tool.invoke` of a named tool through the stable broker ABI.

The implementation plan and interface documentation are aligned with this
behavior:

- [BUNDLE_OPEN_GOVERNANCE_IMPLEMENTATION_PLAN.md](BUNDLE_OPEN_GOVERNANCE_IMPLEMENTATION_PLAN.md)
- [SKILL_INTERFACE.md](SKILL_INTERFACE.md)

## Validation Record

- `python3 -m unittest tests/test_host_mediation.py -v`: 28 tests passed in
  42.954 seconds.
- Broader governance/runtime slice: 117 tests passed in 137.443 seconds.
- Full suite: 249 tests passed in 457.643 seconds.

These timings record the Phase 12 qualification run; they are not current
performance guarantees.

## Bounded Follow-Up

Phase 13 hardening covers:

- Per-effect revocation and incident receipts inside constitutional traces.
- Richer registry and publication semantics.
- If required, broker coverage beyond the current stable Wasm subset,
  beginning with selected `net.*` surfaces rather than widening ambient
  capability access.
