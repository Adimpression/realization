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
- owns constitutional state, composition-chain, decision-flow, transcript, and
  replay-comparison projection over concrete controller state
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
- owns subject acquisition adapters, including external URL capture, at the
  subject application-service boundary rather than at repository root
- uses skills and lower-level host interaction primitives
- does not replace the controller

6. **Entry / Exchange**
- owns CLI, import/export, run-bundle I/O, user-facing ingress/egress, and launch surfaces
- owns portable skill-registry projection and governed run-bundle
  serialization, but not replay execution or controller-state semantics
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

The governed runtime consumes that seam through a **pluggable host-interaction backend**:
- `host` for ordinary host-native execution
- `workstation` for workstation-backed attachment and capability scope

This is modeled as one contract with multiple implementations, not as
workstation-specific branching inside the runtime. `HostInteractionContext`
holds descriptor and attachment/capability scope and may carry an immutable
`HostRealizerProvider`. Providers advertise exact executor and broker
identities plus inspectable prerequisites; application composition supplies
the concrete callbacks. No mutable process-global provider registry is part of
the contract.

This is a shared lower seam, not a seventh top-level layer.

## Skill Application Seam

Portable skill meaning remains dependency-light, while artifact-backed skill
operations need governance and runtime contracts. Those operations live in the
`realized-skill-application` application seam rather than in portable semantics,
workstation sessions, or entry/exchange adapters.

The seam owns:

- projection from a governed artifact into canonical skill IR
- deterministic projection from governed artifact records into portable skill
  kinds
- synthesis of portable boundary normalization from declared artifact inputs
  and outputs
- analysis and execution of explicit composition plans through a
  caller-supplied invoker

It does not parse YAML or foreign tool formats, decide admission or authority,
discover or supply host realizers, persist artifacts, select skills from a user
request, invoke an LLM, or own workstation state. Entry/exchange and workstation
code may call the seam; the seam depends only on semantic, governance, runtime,
and portable skill contracts. This is an application seam within the existing
Runtime + Skill Execution responsibility, not a seventh layer.

## Blend Application Seam

Blend domain values and pure rules remain dependency-light, while concrete
operator projection, skill-compose translation, workflow execution adaptation,
and JSON repositories require runtime and skill contracts. Those adapters live
in the `realized-blend-application` seam rather than in the Blend domain,
workstation controller, or repository-root compatibility paths.

The seam implements Blend's outbound ports and translation boundaries. It does
not define Blend truth, own workstation sessions, select an ability for a user
request, decide admission or authority, provide host realizers, invoke an LLM,
or parse exchange formats. Workstation runtime composes this seam with concrete
session and event behavior. This is a runtime-application seam within the
existing Runtime + Skill Execution responsibility, not a seventh layer.

## Exchange Adapter Seam

Artifact and portable-skill exchange is an outer representation boundary. The
`realized-exchange` package owns YAML hydration/rendering, supported
foreign-format translation, portable-skill compilation, deterministic bundle
naming, learning-context derived-skill materialization, and the concrete
workstation exchange provider. Subject core owns authoritative learning state
and deterministic subject documents; subject service coordinates persistence
and supplies pure derived-skill documents; exchange alone compiles and writes
their portable representation. Workstation consumers depend on the
transport-neutral `SkillExchangeProvider` contract; the executable entrypoint
registers the concrete adapter.

Exchange translation does not imply admission or availability. The seam does
not decide lifecycle, current use, authority, semantic commitment,
request-to-ability selection, realizer provision, or execution. Those values
flow inward to their existing governance, controller, and runtime owners. This
is an adapter seam within Entry / Exchange, not a seventh layer.

## Dependency Rules

Allowed direction:
- `entry/exchange -> workstation`
- `entry/exchange -> controller`
- `entry/exchange -> skill application seam`
- `workstation -> llm`
- `workstation -> governance`
- `workstation -> blend application seam`
- `workstation -> skill application seam`
- `workstation -> shared host interaction substrate`
- `controller -> llm`
- `controller -> governance`
- `controller -> shared host interaction substrate`
- `shared host interaction substrate -> runtime`
- `blend application seam -> blend domain`
- `blend application seam -> runtime contracts`
- `blend application seam -> skill application seam`
- `skill application seam -> governance`
- `skill application seam -> runtime contracts`
- `skill application seam -> semantic contracts`

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
