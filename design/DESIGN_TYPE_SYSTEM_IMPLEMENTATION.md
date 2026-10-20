# Typed Design Mediation Implementation Guidance

## I. Purpose

The design type system must be implementable in a way that preserves backward compatibility with simpler framework-bound implementations while enabling stronger semantic alignment over time.

The implementation purpose is therefore twofold:

1. preserve the mediation chain in machine-readable form,
2. make drift, invalid mapping, and recompilation detectable.

The why:

* because a theory without implementation discipline becomes decorative,
* because code will otherwise collapse meaning into components,
* and because teams need a structure that teaches them how to use the theory correctly while building.

---

## II. Governing Implementation Principle

Implement the type system additively and layer by layer.

Do not start by replacing framework code with a giant universal abstraction.

Instead:

* preserve existing terminal encodings,
* add typed wrappers and references,
* add alignment checks,
* add revision and drift checks,
* and only then tighten enforcement.

The why:

* because direct rewrites confuse terminal syntax with semantic progress,
* because compatibility matters,
* and because the type system should first illuminate the system before it constrains it.

So implementation should begin with **typing and traceability**, not with ideological replacement.

---

## III. Module Structure

A disciplined implementation should separate modules as follows.

### 1. `design.types.core`

Contains:

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

The why:

* this is the stable semantic center,
* this layer should survive framework changes,
* and this layer is the reference point for correctness.

---

### 2. `design.types.embodiment`

Contains framework-agnostic embodiments:

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

The why:

* because embodiment should be shareable across terminal vocabularies,
* because the same obligation may compile into different frameworks,
* and because this layer prevents premature commitment to Material, physical signage, or workflow tooling.

---

### 3. `design.types.framework`

Contains terminal adapters for concrete vocabularies.

Submodules may include:

* `design.types.framework.material`
* `design.types.framework.physical_service`
* `design.types.framework.high_risk_operational`
* `design.types.framework.collaborative_workflow`

Each encoding type should include:

* source obligation reference,
* admissible risk class,
* required invariants,
* required recoverability posture,
* implementation payload or component configuration,
* and trace identifiers.

The why:

* because a framework artifact without a source obligation is semantically weak,
* because terminal encodings should be checkable,
* and because cross-domain design only works if terminal layers are adapters, not the theory itself.

---

### 4. `design.types.reality`

Contains types representing actual state and events.

Examples:

* `ObservedSignal`
* `ActionEvent`
* `FeedbackEvent`
* `EnvironmentState`
* `ConstraintActivation`
* `BoundaryFriction`
* `HandoffFailure`
* `QueueCongestion`
* `OverrideEvent`
* `TrustFailure`
* `AdoptionDrift`

The why:

* because the implementation must compare design assumptions with reality,
* because runtime truth is not reducible to UI state,
* and because failure often occurs outside the rendering layer.

---

### 5. `design.types.trace`

Contains reference and linkage types:

* `ObjectiveRef`
* `IntentRef`
* `ObligationRef`
* `EmbodimentRef`
* `EncodingRef`
* `ObservationRef`
* `RevisionRef`
* `EvidenceLink`

The why:

* because traceability is the bridge-preservation mechanism,
* because explanations depend on upstream references,
* and because recomputation depends on knowing what a thing means, not only what it is called.

---

### 6. `design.types.revision`

Contains:

* `DesignSnapshot`
* `RealitySnapshot`
* `AlignmentCheck`
* `DriftReport`
* `InvalidatedEncoding`
* `RecompilationRequired`

The why:

* because the world changes,
* because static encodings become stale,
* and because revision must be treated as a typed event, not a vague feeling that the design is “off.”

---

### 7. `design.controllers`

Contains meta-control logic:

* `DesignCompiler`
* `ObligationValidator`
* `EncodingAdmissibilityChecker`
* `RealityAlignmentChecker`
* `DriftDetector`
* `RevisionPlanner`
* `EncodingRecompiler`

The why:

* because these functions govern correctness rather than directly render the system,
* because typed design needs both constructive and supervisory machinery,
* and because users of the package should be able to ask not just “what should I render?” but also “is this still justified?”

---

## IV. Minimal Type Contracts

### 1. Core semantic contract

Every semantic design type should minimally carry:

* `id`
* `name`
* `description`
* `source_refs`
* `metadata`

The why:

* because named semantics must be referenceable,
* because provenance matters,
* and because even abstract design objects need operational identity.

---

### 2. Embodiment contract

Every embodiment type should minimally carry:

* `embodiment_id`
* `obligation_refs`
* `invariant_refs`
* `risk_class`
* `recoverability_posture`
* `constraints`
* `implementation_notes`

The why:

* because embodiment is the first place where tradeoffs become visible,
* because obligations are many-to-one and one-to-many,
* and because risk compatibility must remain explicit.

---

### 3. Framework encoding contract

Every framework encoding type should minimally carry:

* `encoding_id`
* `framework_name`
* `embodiment_ref`
* `obligation_refs`
* `admissible_risk_classes`
* `required_invariant_refs`
* `payload`
* `trace_refs`

The why:

* because encoded artifacts need both implementation payload and semantic justification,
* because downstream code should be able to inspect what the artifact is for,
* and because runtime checks need a consistent target.

---

### 4. Reality evidence contract

Every reality/event type should minimally carry:

* `evidence_id`
* `time`
* `actor_or_system_source`
* `observed_fact`
* `affected_encoding_refs`
* `affected_obligation_refs`
* `severity`

The why:

* because runtime alignment is evidence-based,
* because observations must be linked to what they challenge or confirm,
* and because silent facts cannot drive recompilation.

---

## V. Implementation Phases

### Phase 1: Typed wrappers around current framework code

Do not replace current components.

Wrap them with:

* obligation references,
* embodiment references,
* risk metadata,
* and trace links.

The why:

* because this gives immediate semantic visibility,
* because it preserves compatibility,
* and because the system can begin learning without becoming brittle.

---

### Phase 2: Add compilers from obligation to embodiment and encoding

Introduce compilers such as:

* `compile_obligation_to_embodiment(...)`
* `compile_embodiment_to_material_encoding(...)`
* `compile_embodiment_to_physical_service_encoding(...)`
* `compile_embodiment_to_workflow_encoding(...)`

The why:

* because once the semantic chain is typed, compilation becomes systematic,
* because the case studies already describe the mapping discipline,
* and because direct component choice should become a derived operation.

---

### Phase 3: Add admissibility and alignment checking

Introduce validators such as:

* `is_encoding_admissible(...)`
* `check_alignment(...)`
* `detect_design_drift(...)`

The why:

* because a typed compiler without a checker still allows silent misuse,
* because not all legal components are semantically legal,
* and because a real design system must detect when reality has diverged from design assumptions.

---

### Phase 4: Add revision and recompilation

Introduce:

* snapshots,
* diffs,
* invalidation rules,
* and recompilation plans.

The why:

* because terminal encodings should change when reality changes,
* because rework should be explainable,
* and because revision should be structured rather than ad hoc.

---

## VI. Example Python Shapes

The implementation does not need a fully static type language to behave like a typed mediation system.

Plain Python dataclasses and protocols are enough.

Example semantic type:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class InteractionObligation:
    obligation_id: str
    name: str
    intent_refs: tuple[str, ...] = ()
    invariant_refs: tuple[str, ...] = ()
    constraint_refs: tuple[str, ...] = ()
    risk_class: str = "normal"
    metadata: dict[str, object] = field(default_factory=dict)
```

Example framework encoding:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class MaterialButtonEncoding:
    encoding_id: str
    embodiment_ref: str
    obligation_refs: tuple[str, ...]
    variant: str
    required_invariant_refs: tuple[str, ...] = ()
    admissible_risk_classes: tuple[str, ...] = ("low", "normal")
    payload: dict[str, object] = field(default_factory=dict)
```

Example drift report:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class DriftReport:
    report_id: str
    affected_encoding_refs: tuple[str, ...]
    affected_obligation_refs: tuple[str, ...]
    reasons: tuple[str, ...]
    recompilation_required: bool = False
    metadata: dict[str, object] = field(default_factory=dict)
```

The why:

* because the system needs inspectable objects more than language-level sophistication,
* because Python is sufficient for layered semantics if the discipline is strong,
* and because adoption improves when the types remain readable.

---

## VII. Compiler Discipline

The compiler should never accept:

[
\text{Objective} \rightarrow \text{FrameworkEncoding}
]

as a direct valid path.

It must require at least:

[
\text{Objective} \rightarrow \text{Intent} \rightarrow \text{TaskMorphology} \rightarrow \text{Invariant} \rightarrow \text{Obligation} \rightarrow \text{Embodiment} \rightarrow \text{FrameworkEncoding}
]

The why:

* because skipping layers destroys explainability,
* because every invalid shortcut makes the design less falsifiable,
* and because the bridge is the whole point of the theory.

So the compiler should reject direct objective-to-component mappings as formally incomplete.

---

## VIII. Alignment Discipline

A framework encoding should be treated as aligned only if:

1. its upstream obligation is still active,
2. its required invariants still apply,
3. its risk posture is still admissible,
4. runtime evidence does not contradict its assumptions,
5. no revision has invalidated its embodiment choice.

The why:

* because design correctness is temporal,
* because a once-correct encoding can become wrong without any local code change,
* and because the system must preserve semantic truth, not just artifact stability.

---

## IX. User-Facing Value

The type system should help not only implementers, but also users of the design package.

It should let them ask:

* what obligation does this artifact encode?
* why is this encoding valid?
* what assumptions does it make?
* what changed in reality?
* why is recompilation required?

The why:

* because users need guidance, not just abstractions,
* because a package that cannot explain itself will be misused,
* and because education is part of implementation discipline.

So the docs and code should expose the chain, not hide it.

---

## X. Package Guidance

If `design` is a separate package, it should begin with:

* package metadata,
* markdown theory docs,
* a small `__init__.py`,
* and then, over time, typed modules under the package boundary.

The why:

* because the package should be independently legible,
* because it should be consumable by other modules without dragging in one framework,
* and because the package should stand for the theory and its discipline, not just one implementation.

---

## XI. Final Implementation Rule

Never implement the design type system as a glorified component registry.

Implement it as a layered semantics-preservation system whose job is to:

* preserve meaning across abstraction layers,
* preserve traceability across implementations,
* preserve correctness across reality changes,
* and preserve the possibility of recompilation without theoretical collapse.

That is the why behind every module split, type definition, and controller.

Without that discipline, the design package becomes another vocabulary list.

With it, the package becomes a real mediation engine.
