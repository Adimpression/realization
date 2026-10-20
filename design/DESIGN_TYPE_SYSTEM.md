# Typed Design Mediation

## I. Purpose

If cross-domain design mediation is the bridge from objective to embodiment, then a practical implementation needs a type system that preserves the bridge while concerns move across layers.

Without such a type system, the design process decays in predictable ways:

* objectives collapse into components,
* invariants disappear into framework conventions,
* embodiments drift away from the realities they were meant to mediate,
* and downstream implementations cannot explain why a given form exists.

The purpose of the design type system is therefore not merely to classify UI parts.

Its purpose is to preserve **semantic continuity** from objective through embodiment to runtime evidence.

The why is decisive:

* because the essence of a design is not the component,
* because component identity is downstream of interaction obligation,
* and because real systems change after implementation.

So the type system must preserve meaning, not just shape.

---

## II. Governing Principle

The type system must be layered.

No downstream layer may be valid unless it can be justified by the upstream layer from which it is derived.

Formally:

[
O \rightarrow I \rightarrow T \rightarrow V \rightarrow G \rightarrow E \rightarrow F(E) \rightarrow R
]

Where:

* (O) = objective types
* (I) = intent types
* (T) = task morphology types
* (V) = interaction invariant types
* (G) = interaction obligation types
* (E) = embodiment types
* (F(E)) = framework encoding types
* (R) = runtime and reality evidence types

The why is simple:

* if an implementation can skip directly from objective to component, then it is free to break the theory,
* if a component cannot point back to the obligation it encodes, then correctness cannot be checked,
* and if runtime evidence cannot point back to design intent, then drift cannot be detected.

Therefore the type system must be a **typed mediation system**, not merely a component taxonomy.

---

## III. Core Distinction

The type system must distinguish at least five fundamentally different things:

1. what the system is for,
2. what the agent is trying to do,
3. what the system must guarantee,
4. how the guarantee is embodied,
5. what the world actually contains or does.

These are not interchangeable.

The why is crucial:

* an objective is not an intent,
* an intent is not an obligation,
* an obligation is not a button or a sign,
* and a button or sign is not evidence that the obligation is still being satisfied.

If the implementation collapses these, it will eventually optimize the wrong layer.

---

## IV. Semantic Design Types

The first layer contains framework-independent semantic types.

These types should include at least:

* `Objective`
* `Intent`
* `TaskMorphology`
* `InteractionInvariant`
* `InteractionObligation`
* `Constraint`
* `RiskClass`
* `FeedbackRequirement`
* `RecoverabilityRequirement`
* `CoordinationRequirement`

These are the stable center of the system.

The why:

* these are the things that survive domain changes,
* these are the things that should remain true whether the terminal encoding is Material, a physical service counter, or a control room,
* and these are the things that let a design remain itself even when the final embodiment changes.

So this layer preserves the **essence** of the design.

---

## V. Embodiment Types

The next layer contains embodiment types that are still independent of any specific framework.

Examples:

* `ActionEmbodiment`
* `NavigationEmbodiment`
* `ContainmentEmbodiment`
* `StatusEmbodiment`
* `SelectionEmbodiment`
* `InputEmbodiment`
* `QueueEmbodiment`
* `HandoffEmbodiment`
* `InterlockEmbodiment`
* `AuditEmbodiment`

These are not framework components.

They are structured answers to the question:

> What kind of thing must exist so that this obligation can be realized?

The why:

* because multiple frameworks may legitimately realize the same obligation,
* because a design should not become captive to one terminal vocabulary,
* and because we want a reversible bridge between theory and implementation.

This layer makes embodiment plural without making meaning ambiguous.

---

## VI. Framework Encoding Types

The next layer contains framework-specific encoding types.

Examples:

* `MaterialButtonEncoding`
* `MaterialDialogEncoding`
* `MaterialCardEncoding`
* `MaterialNavigationBarEncoding`
* `PhysicalQueueEncoding`
* `ControlRoomAlarmEncoding`
* `CollaborativeBoardEncoding`

Each framework encoding must be typed not only by its framework identity, but also by the obligation class it is allowed to encode.

Each encoding should carry at least:

* its source obligation,
* its required invariants,
* its admissible risk range,
* its recoverability posture,
* and its explanatory trace back to the semantic layer.

The why:

* because a framework object is not self-justifying,
* because two different components may both be valid encodings of one obligation,
* and because many implementation errors come from using a legitimate component for an illegitimate obligation.

So framework encoding types should be treated as **typed terminal adapters**.

---

## VII. Reality Types

The next layer contains types that represent actual world state.

These types may refer to code-visible events, real-world conditions, or organizational conditions.

Examples:

* `Actor`
* `EnvironmentState`
* `ObservedSignal`
* `ActionEvent`
* `FeedbackEvent`
* `ConstraintActivation`
* `BoundaryFriction`
* `QueueCongestion`
* `HandoffFailure`
* `OverrideEvent`
* `TrustFailure`
* `AdoptionDrift`

These are not design-specification types.

They are types for reality.

The why:

* because the design exists to mediate reality, not to be internally elegant,
* because obligations are satisfied or violated in the world, not just in mockups,
* and because alignment can only be checked if the implementation can talk about what actually happened.

This layer keeps the design honest.

---

## VIII. Trace and Causality Types

To preserve meaning across layers, the type system must include explicit trace types.

Examples:

* `ObjectiveRef`
* `IntentRef`
* `ObligationRef`
* `EmbodimentRef`
* `EncodingRef`
* `ObservationRef`
* `RevisionRef`
* `EvidenceLink`

These types tie downstream artifacts back to the upstream rationale they instantiate.

The why:

* because otherwise the system cannot explain itself,
* because traceability is the only way to check whether an implementation still corresponds to its intended obligation,
* and because revision without traceability becomes guesswork.

So trace types preserve **causal intelligibility**.

---

## IX. Revision and Alignment Types

Since the world changes, the type system must include revision and alignment types.

Examples:

* `DesignSnapshot`
* `RealitySnapshot`
* `AlignmentCheck`
* `DriftReport`
* `InvalidatedEncoding`
* `RecompilationRequired`

This layer exists because the design may have been correct yesterday and wrong today.

The why:

* because task morphology changes,
* because constraints can activate or disappear,
* because users, teams, and environments drift,
* and because a terminal encoding must sometimes be recompiled without changing the upstream intent.

This layer prevents the implementation from confusing historical correctness with current correctness.

---

## X. Typed Separation of Code and Meta-Control

Some types will bind directly to implementation code.

Others will govern whether that code remains legitimate.

So the system should distinguish:

### Code-bound types

These directly drive or constrain implementation:

* UI or artifact encodings
* schema-bearing embodiment types
* runtime interface specifications
* layout or control contracts

### Meta-control types

These do not directly render the system.

They govern alignment:

* validators
* compilers
* drift detectors
* revision engines
* evidence aggregators
* obligation checkers

The why:

* because implementation and governance are different activities,
* because direct code artifacts should not have to carry all alignment logic themselves,
* and because a serious design system must contain both a constructive layer and a corrective layer.

---

## XI. Module Discipline

If the system is separated into modules, a clean partition is:

* `design.types.core`
* `design.types.embodiment`
* `design.types.framework`
* `design.types.reality`
* `design.types.trace`
* `design.types.revision`
* `design.controllers`

The why:

* because semantic design, embodiment, framework encoding, runtime reality, and revision are distinct concerns,
* because separation makes invalid shortcuts visible,
* and because it allows some modules to bind directly to code while others remain analytical or supervisory.

This is not separation for elegance alone.

It is separation so that the bridge cannot silently collapse.

---

## XII. Admissibility Rule for Encodings

A framework encoding is admissible only if:

1. it is derived from an obligation,
2. the obligation is derived from invariants appropriate to the task morphology,
3. the risk and recoverability posture are compatible with the encoding,
4. the runtime evidence does not contradict the encoding’s assumptions.

The why:

* because the same visible component may be correct in one mediation chain and incorrect in another,
* because design quality cannot be inferred from surface familiarity,
* and because alignment must be checkable as a typed property, not as taste.

So admissibility must be part of the type system, not only a human judgment.

---

## XIII. Compact Governing Formulation

The type system should be treated as a layered semantics-preservation system in which objectives, intents, task morphologies, invariants, obligations, embodiments, framework encodings, and runtime evidence are represented by distinct but connected types.

Its purpose is to ensure that:

* downstream forms remain justified by upstream obligations,
* framework encodings remain traceable,
* reality can invalidate an encoding without corrupting the core design intent,
* and redesign can occur as recompilation rather than theoretical collapse.

In compact form:

[
\text{Typed Design Mediation}
=
\text{Semantic Layer}
+
\text{Embodiment Layer}
+
\text{Encoding Layer}
+
\text{Reality Layer}
+
\text{Trace Layer}
+
\text{Revision Layer}
]

The why is the same throughout:

> preserve the meaning of the design while it moves through code, artifacts, events, and changing reality.

That is the point of the type system.
