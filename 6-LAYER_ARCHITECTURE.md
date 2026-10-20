# Six-Layer Architecture

This filename is legacy. The architecture is now six-layer.

## Layers

1. **Runtime + Skill Execution**
- owns executors, brokers, host ABI, Wasmtime/WASI linkage, child-runtime shims
- owns governed skill invocation and effect execution
- treats an ability declaration and its concrete host realizer as separate inputs;
  packaging or composition supplies realizers independently of ability admission
- does not parse CLI
- does not parse skill YAML

2. **Controller**
- owns recursive `Not` reduction, decomposition, reuse, closure, and answer orchestration
- may plan against host interactions
- must not depend on workstation session/chat machinery directly

3. **Governance**
- owns declaration, policy, lifecycle, approvals, revocation, incidents, admission, and current-use checks
- exposes narrow facades to controller, runtime, and workstation
- does not own prompt construction or CLI parsing

4. **LLM**
- owns prompt construction and model calls
- serves controller-side reasoning and workstation-side chat/skill routing
- does not own governance or host mediation rules

5. **Workstation**
- owns the host-owned shell/session surface
- owns attachments, workstation task contracts, capability mediation, session receipts, and conversational lifecycle operations
- uses skills and lower-level host interaction primitives
- does not replace the controller

6. **Entry / Exchange**
- owns CLI, import/export, run-bundle I/O, user-facing ingress/egress, and launch surfaces
- composes the selected host implementation and advertises its available
  executor or broker realizers
- may call all lower layers
- nothing below it should depend upward on it

## Ability Delivery Rule

Ability delivery crosses layers without collapsing their responsibilities:

```text
portable ability
    -> governance evaluates installation and admission
    -> admitted ability enters subject/global visibility
    -> controller/retrieval matches a request to the ability
    -> runtime mechanically binds the declared realizer
    -> the separately supplied host realizer performs the operation
    -> runtime records the result and receipts
```

The bindings are distinct:

- subject to ability is explicit scope and provenance
- request to ability is semantic candidate matching
- ability to host realization is an exact executor or broker identity

LLM judgment may assist semantic matching. Admission, authority, realizer
availability, and dispatch remain mechanical checks.

## Shared Substrate Rule

The controller and workstation should converge on a **shared host interaction substrate**, not on each other.

That substrate should eventually own:
- attachment resolution
- capability execution
- delegated-rights narrowing
- receipt emission
- governed skill invocation helpers

The governed runtime should consume that seam through a **pluggable host-interaction backend**:
- `host` for ordinary host-native execution
- `workstation` for workstation-backed attachment and capability scope

This should be modeled as one contract with multiple implementations, not as
workstation-specific branching inside the runtime. The current
`HostInteractionContext` implements descriptor and attachment/capability scope;
it is not yet a callable host-realizer provider registry.

This is a shared lower seam, not a seventh top-level layer.

## Dependency Rules

Allowed direction:
- `entry/exchange -> workstation`
- `entry/exchange -> controller`
- `workstation -> llm`
- `workstation -> governance`
- `workstation -> shared host interaction substrate`
- `controller -> llm`
- `controller -> governance`
- `controller -> shared host interaction substrate`
- `shared host interaction substrate -> runtime`

Disallowed direction:
- `controller -> workstation`
- `runtime -> workstation`
- `governed_semantic_reduction_runtime -> workstation/*`
- `workstation -> controller internals` as a hard dependency for normal prompt handling

## Practical Meaning

- The workstation remains the shell.
- Skills remain pluggable workers.
- Wasmtime remains one worker runtime.
- The controller remains a reasoning engine.

If controller and workstation are unified later, they should be unified by sharing a lower host-interaction contract, not by making the runtime execute “inside” workstation code.

## Diagrams

- [08_six_layer_architecture_context.puml](semantic_control_flow_diagrams/08_six_layer_architecture_context.puml)
- [09_workstation_and_shared_host_substrate.puml](semantic_control_flow_diagrams/09_workstation_and_shared_host_substrate.puml)
