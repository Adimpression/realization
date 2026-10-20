# Coordinated Transformation in Federated Systems (CTFS) Theory Implementation

Implementation plan for wiring
[COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md](COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md)
into the workstation subject workflow.

This file is intentionally concrete.

It describes:

- where coordinated-transformation construct discovery should happen
- where explicit model curation should happen
- how LLM assistance should be used without replacing governed structure
- how the theory should feed `Draft`, `Review`, and later `Publication`

This implementation note is aligned to the repo design and publication contracts.

There is no `PRODUCTION.md` in the repo root at the time of writing.
The publication-facing contract is therefore taken from `PUBLICATION.md`.

There is now an additional workstation-shape constraint:

- the user should experience one case workspace rather than separate theory tools
- the stable DST lenses should be:
  - `Frame`
  - `Model`
  - `Explore`
- those lenses should be hosted inside the existing workstation shell rather than introduced as a second top-level navigation model

## Incremental Change and Model Evolution

### 1. Purpose

A `CTFS` implementation must support systems whose structure changes over time.

In real federated systems:

- new actors may join
- actors may leave
- constraints may be introduced
- constraints may become inactive
- dependencies may become satisfied or unsatisfied
- capabilities may be introduced, retired, or modified
- transitions may become newly admissible or newly blocked
- boundary friction may appear or disappear

Therefore, a `CTFS` implementation must not treat the system as one frozen model.

It must treat the system as an evolving sequence of valid `CTFS` model snapshots.

### 2. Governing principle

The `CTFS` core theory defines admissibility within a model snapshot.

Incremental change defines how one model snapshot becomes another.

Thus:

$$CTFS_{core}$$

governs the internal validity of each model, while:

$$CTFS_{revision}$$

governs change between models.

The implementation must distinguish:

$$\text{state transition}$$

from:

$$\text{model revision}$$

These are different kinds of change.

### 3. State transition versus model revision

### 3.1 State transition

A state transition changes the state of the system inside a fixed model.

Formally:

$$\tau : s_1 \rightarrow s_2$$

with:

$$source(\tau)=s_1$$

$$target(\tau)=s_2$$

A state transition answers:

> Given the current model, what admissible next state can the system move to?

### 3.2 Model revision

A model revision changes the model itself.

A revision may add, remove, activate, deactivate, or reinterpret elements of the system.

Formally, the implementation should treat model evolution as:

$$M_{t_0} \leadsto M_{t_1}$$

where each $M_t$ is a valid `CTFS` model snapshot.

A model revision answers:

> What has changed in the structure against which future decisions must be evaluated?

### 4. Time-indexed model snapshots

A `CTFS` implementation should maintain a sequence of model snapshots:

$$\left(M_t\right)_{t \in Time}$$

Each snapshot has the structure:

$$
M_t =
(A_t,O_t,K_t,D_t,Q_t,B_t,S_t,T_t,\Delta_t,\Theta_t;\text{relations}_t;\text{functions}_t)
$$

where:

- $A_t$ interprets `Actor` at time $t$
- $O_t$ interprets `Objective` at time $t$
- $K_t$ interprets `Capability` at time $t$
- $D_t$ interprets `Dependency` at time $t$
- $Q_t$ interprets `Constraint` at time $t$
- $B_t$ interprets `Boundary` at time $t$
- $S_t$ interprets `State` at time $t$
- $T_t$ interprets `Transition` at time $t$
- $\Delta_t$ interprets `Decision` at time $t$
- $\Theta_t$ interprets `Time`

Each snapshot must satisfy the `CTFS` core axioms.

### 5. Implementation rule: preserve the core theory

The `CTFS` core must remain stable.

A new actor, constraint, dependency, or admissibility fact must not alter the meaning of the core predicates.

The following definitions must remain invariant across snapshots:

- `Admissible(k,s)`
- `AdmissibleTransition(τ,s)`
- `ReadyCapability(k,s)`
- `ReadyTransition(τ,s)`
- `RiskCapability(k,s)`
- `RiskTransition(τ,s)`
- `RequiresCoordinationCapability(k)`
- `RequiresCoordinationTransition(τ)`
- `Coexists(k1,k2,s)`
- `MixedMode(s)`
- `BoundaryFriction(β,s)`

Their truth values may change because the model facts change.

Their definitions must not change.

### 6. Revision layer

To implement incremental change, introduce a revision layer.

### 6.1 New sort

Add one implementation-level sort:

- `Revision`

This sort is not part of the closed `CTFS` core.

It belongs to the implementation guidance layer.

### 6.2 Revision predicates

A revision records a change from one model snapshot to another.

Primitive implementation predicates may include:

- `RevisionAt(r,t)`
- `BeforeRevision(r,M1)`
- `AfterRevision(r,M2)`

If the implementation does not represent models as first-class objects, then `BeforeRevision` and `AfterRevision` may be represented operationally through version identifiers.

### 6.3 Revision operations

A `CTFS` implementation should support at least the following revision operations.

Actor revisions:

- `AddsActor(r,a)`
- `RemovesActor(r,a)`
- `ActivatesActor(r,a)`
- `DeactivatesActor(r,a)`

Capability revisions:

- `AddsCapability(r,k)`
- `RetiresCapability(r,k)`
- `MakesAvailable(r,k,s)`
- `MakesOperational(r,k,s)`
- `MakesNonOperational(r,k,s)`

Dependency revisions:

- `AddsDependency(r,d)`
- `MakesSatisfied(r,d,s)`
- `MakesUnsatisfied(r,d,s)`

Constraint revisions:

- `AddsConstraint(r,q)`
- `ActivatesConstraint(r,q,s)`
- `DeactivatesConstraint(r,q,s)`
- `AddsCapabilityConstraint(r,k,q)`
- `AddsTransitionConstraint(r,τ,q)`

Boundary revisions:

- `AddsBoundary(r,β)`
- `AddsBoundaryFriction(r,β,s)`
- `RemovesBoundaryFriction(r,β,s)`

Transition revisions:

- `AddsTransition(r,τ)`
- `RetiresTransition(r,τ)`
- `ChangesSource(r,τ,s)`
- `ChangesTarget(r,τ,s)`
- `AddsTransitionDependency(r,τ,d)`
- `AddsTransitionBoundaryCrossing(r,τ,β)`
- `MakesTransitionAdmissibleUnder(r,τ,q,s)`
- `MakesTransitionInadmissibleUnder(r,τ,q,s)`

Decision revisions:

- `AddsDecisionCandidate(r,δ)`
- `RetiresDecisionCandidate(r,δ)`
- `AssignsDecisionActor(r,δ,a,k)`
- `RemovesDecisionAssignment(r,δ,a,k)`

### 7. No direct magical unblocking

A `CTFS` implementation must not treat actors as directly deleting constraints merely by existing.

An actor joining the system may unblock progress only through an explicit admissibility-relevant mechanism.

Permitted mechanisms include:

1. satisfying a dependency
2. making a transition admissible under an active constraint
3. deactivating a constraint
4. introducing an alternative transition
5. making a capability available or operational
6. removing or reducing boundary friction
7. enabling a required assignment or decision capability

This rule is essential.

Actors do not bypass the theory.

Actors change the facts under which the theory is evaluated.

### 8. Example: new constraint blocks progress

Assume that at time $t_0$, transition $\tau$ is admissible in state $s$:

$$AdmissibleTransition(\tau,s)$$

This means:

$$source(\tau)=s$$

$$\forall d(RequiresForTransition(\tau,d)\rightarrow Satisfied(d,s))$$

$$\forall q((ConstrainedByTransition(\tau,q)\wedge Active(q,s))\rightarrow TransitionAdmissibleUnder(\tau,q,s))$$

At time $t_1$, a revision $r_1$ introduces a new constraint $q_{block}$:

$$AddsConstraint(r_1,q_{block})$$

$$AddsTransitionConstraint(r_1,\tau,q_{block})$$

$$ActivatesConstraint(r_1,q_{block},s)$$

and the transition is not admissible under it:

$$\neg TransitionAdmissibleUnder(\tau,q_{block},s)$$

Therefore, in the new snapshot $M_{t_1}$:

$$\neg AdmissibleTransition(\tau,s)$$

The transition is blocked.

The core theory did not change.

Only the model facts changed.

### 9. Example: new actor removes the blockage

At time $t_2$, a new actor $a_{new}$ joins:

$$AddsActor(r_2,a_{new})$$

This alone does not unblock the transition.

The actor must alter the admissibility structure by one of the allowed mechanisms.

### 9.1 Mechanism A: actor satisfies a dependency

Suppose the transition requires dependency $d_{cert}$:

$$RequiresForTransition(\tau,d_{cert})$$

At $t_1$:

$$\neg Satisfied(d_{cert},s)$$

At $t_2$, the new actor enables:

$$MakesSatisfied(r_2,d_{cert},s)$$

Thus in $M_{t_2}$:

$$Satisfied(d_{cert},s)$$

If all other dependencies and constraints are satisfied, then:

$$AdmissibleTransition(\tau,s)$$

### 9.2 Mechanism B: actor makes transition admissible under the constraint

The constraint remains active:

$$Active(q_{block},s)$$

But the new actor enables:

$$MakesTransitionAdmissibleUnder(r_2,\tau,q_{block},s)$$

Thus in $M_{t_2}$:

$$TransitionAdmissibleUnder(\tau,q_{block},s)$$

If all other requirements hold:

$$AdmissibleTransition(\tau,s)$$

This is the clean formal pattern for certification, audit, assurance, approval, or oversight.

### 9.3 Mechanism C: actor deactivates the constraint

The actor may participate in a governance process that makes the constraint inactive:

$$DeactivatesConstraint(r_2,q_{block},s)$$

Thus in $M_{t_2}$:

$$\neg Active(q_{block},s)$$

Since inactive constraints do not block admissibility:

$$AdmissibleTransition(\tau,s)$$

provided other requirements hold.

### 9.4 Mechanism D: actor enables an alternative transition

The original transition remains blocked:

$$\neg AdmissibleTransition(\tau,s)$$

But the actor introduces or enables another transition:

$$AddsTransition(r_2,\tau_{alt})$$

$$source(\tau_{alt})=s$$

$$AdmissibleTransition(\tau_{alt},s)$$

Then progress resumes through a different path.

This is often the most realistic pattern in federated systems.

The old path remains blocked, but the decision space expands.

### 10. Decision algorithm guidance

A `CTFS` decision algorithm should operate over a specific model snapshot.

Given snapshot $M_t$ and current state $s$, the algorithm evaluates:

$$CandidateTransitions(M_t,s)$$

$$CandidateDecisions(M_t,s)$$

$$ValidDecisions(M_t,s)$$

$$ExecutableDecisions(M_t,s)$$

A minimal evaluation pipeline is:

1. select transitions whose source is $s$
2. test transition admissibility
3. collect decisions selecting admissible transitions
4. test assignment validity
5. test executability
6. rank or present the remaining decisions

Semi-formally:

$$CandidateTransitions(M_t,s)=\{\tau\in T_t \mid source(\tau)=s\}$$

$$AdmissibleCandidates(M_t,s)=\{\tau\in CandidateTransitions(M_t,s) \mid AdmissibleTransition(\tau,s)\}$$

$$ValidDecisions(M_t,s)=\{\delta\in \Delta_t \mid Valid(\delta,s)\}$$

$$ExecutableDecisions(M_t,s)=\{\delta\in \Delta_t \mid Executable(\delta,s)\}$$

When a revision occurs:

$$M_t \leadsto M_{t+1}$$

the algorithm must recompute admissibility against $M_{t+1}$.

It must not reuse old admissibility conclusions unless the affected predicates are unchanged.

### 11. Revision invalidation rules

A revision invalidates previous admissibility judgments if it changes any predicate involved in admissibility.

### 11.1 Capability admissibility dependencies

A previous judgment about:

$$Admissible(k,s)$$

must be recomputed if the revision changes any of:

- `Requires(k,d)`
- `Satisfied(d,s)`
- `LimitedBy(k,q)`
- `Active(q,s)`
- `AdmissibleUnder(k,q,s)`

### 11.2 Transition admissibility dependencies

A previous judgment about:

$$AdmissibleTransition(\tau,s)$$

must be recomputed if the revision changes any of:

- `source(τ)`
- `RequiresForTransition(τ,d)`
- `Satisfied(d,s)`
- `ConstrainedByTransition(τ,q)`
- `Active(q,s)`
- `TransitionAdmissibleUnder(τ,q,s)`

### 11.3 Risk dependencies

A previous judgment about:

$$RiskCapability(k,s)$$

must be recomputed if the revision changes any of:

- `Requires(k,d)`
- `Satisfied(d,s)`
- `LimitedBy(k,q)`
- `Active(q,s)`
- `AdmissibleUnder(k,q,s)`
- `Crosses(k,β)`
- `FrictionAt(β,s)`

A previous judgment about:

$$RiskTransition(\tau,s)$$

must be recomputed if the revision changes any of:

- `RequiresForTransition(τ,d)`
- `Satisfied(d,s)`
- `ConstrainedByTransition(τ,q)`
- `Active(q,s)`
- `TransitionAdmissibleUnder(τ,q,s)`
- `CrossesTransition(τ,β)`
- `FrictionAt(β,s)`

### 12. Implementation invariant

Every snapshot must satisfy the `CTFS` core.

For all $t$:

$$M_t \models CTFS_{core}$$

A revision is valid only if its resulting snapshot also satisfies the core:

$$ValidRevision(r,M_t,M_{t+1}) \rightarrow M_{t+1}\models CTFS_{core}$$

This is the central implementation invariant.

No revision may produce an ill-formed `CTFS` model.

### 13. Revision traceability

Each implementation should preserve a revision history.

A revision record should minimally contain:

- revision identifier
- time
- authoring or triggering actor, if known
- added facts
- removed facts
- changed facts
- affected capabilities
- affected transitions
- affected decisions
- recomputation scope
- resulting blocked or unblocked transitions

This supports explainability.

For example:

```text
Revision r17
Time: t2
Change: Added actor CertificationAuthority
Affected transition: τ_migrate
Mechanism: TransitionAdmissibleUnder(τ_migrate, q_certification, s_current)
Previous result: ¬AdmissibleTransition(τ_migrate, s_current)
New result: AdmissibleTransition(τ_migrate, s_current)
Explanation: The certification constraint remains active, but the transition is now admissible under it.
```

### 14. Guidance for user interfaces

A `CTFS` interface should not merely show the current recommendation.

It should show the revision-sensitive structure of admissibility.

For each transition or decision, the interface should expose:

- current admissibility status
- blocking dependencies
- blocking active constraints
- boundary friction
- actors relevant through control or assignment
- changes since the previous snapshot
- what revision would unblock the transition

A useful UI distinction is:

| Status | Meaning |
| --- | --- |
| `Admissible` | The transition satisfies current dependencies and active constraints |
| `BlockedByDependency` | One or more required dependencies are unsatisfied |
| `BlockedByConstraint` | One or more active constraints reject the transition |
| `RiskyButAdmissible` | The transition is admissible but has boundary or other risk |
| `NewlyBlocked` | A prior admissible transition became inadmissible after revision |
| `NewlyUnblocked` | A prior inadmissible transition became admissible after revision |
| `AlternativeAvailable` | Original transition remains blocked, but another admissible path exists |

This helps users understand that `CTFS` is not a static answer engine.

It is a structure for reasoning over a moving system.

### 15. Design principle for implementation

The implementation should obey the following principle:

> Never encode change by weakening the theory.
> Encode change by revising the model and recomputing admissibility.

This avoids arbitrary exceptions.

It also preserves mathematical cleanliness.

The `CTFS` core remains the grammar of admissible transformation.

The revision layer records how the world changes.

The decision layer evaluates what can be done now.

### 16. Final implementation architecture

A rigorous `CTFS` implementation should therefore have four layers.

### Layer 1: Core theory

Contains:

- primitive sorts
- primitive predicates
- primitive functions
- core axioms
- definitional predicates

This layer should be stable.

### Layer 2: Model snapshot

Contains the current interpreted facts:

- actors
- objectives
- capabilities
- dependencies
- constraints
- boundaries
- states
- transitions
- decisions
- predicate valuations

This layer changes over time.

### Layer 3: Revision engine

Applies controlled changes:

- add actor
- add constraint
- activate constraint
- satisfy dependency
- introduce transition
- change admissibility-under relation
- add boundary friction
- remove boundary friction

This layer creates:

$$M_t \leadsto M_{t+1}$$

### Layer 4: Decision engine

Evaluates:

- readiness
- admissibility
- risk
- validity
- executability
- reachability
- decision options

This layer always runs against a specific snapshot:

$$DecisionEngine(M_t,s)$$

### 17. Compact governing formulation

A `CTFS` implementation should treat coordinated transformation as a sequence of valid model snapshots, where operational transitions move between states inside a snapshot, while revisions alter the snapshot itself by changing actors, capabilities, dependencies, constraints, boundaries, transitions, decisions, or predicate valuations.

A new constraint may block progress by changing transition admissibility. A new actor may unblock progress only by changing an explicit admissibility-relevant fact: satisfying a dependency, making a transition admissible under an active constraint, deactivating the constraint, enabling a capability, reducing boundary friction, or introducing an alternative transition.

In short:

$$CTFS = CTFS_{core} + CTFS_{revision} + CTFS_{decision}$$

where:

$$M_t \models CTFS_{core}$$

$$Revision(M_t)=M_{t+1}$$

$$DecisionEngine(M_t,s)=\{\delta \mid Executable(\delta,s)\}$$

That is the implementation discipline.

## Current Position

The repo already has the essential ingredients:

1. the closed theory and executable core
- [COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md](COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md)
- [coordinated_transformation/core.py](coordinated_transformation/core.py)

2. the upstream typed normalization layer
- `ITEMIZE.md`
- `itemize.py`

3. the draft/review/decision substrate
- `REVIEW.md`
- `DECISION_REVIEW.md`
- `review_composition.py`
- `decision_review.py`
- `decision_review_projection.py`
- `decision_review_policy.py`
- `workstation/subject_workflow.py`

4. the downstream publication layer
- `PUBLICATION.md`
- `publication_projection.py`

What exists now in narrow form:

- `Itemize` can produce typed candidates and decision-role candidates
- `Draft` can create a `DecisionFrame`
- `Draft` can add selected draft items to that frame
- the existing bridge can map reviewed items into `coordinated_transformation.Model`
- policy evaluation and publication outputs already exist in a bounded slice

What does not yet exist is the right workstation interaction model for finding the actual theory constructs.

Right now the theory bridge starts too late and too coarsely.

The missing step is:

- discover the real `Actor`, `Objective`, `Capability`, `Dependency`, `Constraint`, `Boundary`, `State`, `Transition`, and `Decision` constructs from the corpus before analysis

More precisely, the repo now has the first runtime-backed DST orchestrator seam, but it still lacks the persisted workstation-integrated version of that path:

- run `reduce_not` with the DST candidate-path framing from live workstation/corpus input
- carry the governed discovery result into the typed DST normalization contract
- normalize the resulting sort atoms and relations
- persist them into the draft-side `DecisionFrame`

The prompt-tightening step is now in place at the DST seam: the discovery prompt is structured around the DST lexicon and fixed output sections. A first live executor binding now exists through the runtime proposal surface. What is still missing is the full workstation-bound path and a richer frontier-native `reduce_not` execution mode.

So the current gap is not only UI-level.
It is the still-missing live construct-discovery and normalization execution path.

## Design And Publication Alignment

This implementation has to satisfy two constraints at the same time.

### From `../design/AXIOMATIC_SYSTEM_FOR_DESIGN.md`

The workstation change must preserve:

- perceptual clarity
- cognitive coherence
- actionability
- feedback immediacy
- progressive disclosure
- hierarchical structuring
- effort minimization
- error prevention over correction

That means in practice:

- do not add another top-level tab yet
- do not make the operator discover, model, review, and publish in one surface
- do not require manual promotion of every candidate before `Draft` can even start
- show one dominant next step at a time
- surface blocking conditions immediately after model edits

### From `PUBLICATION.md`

The publication layer must continue to consume typed governed inputs.

That means:

- publication must not infer the coordinated-transformation model from prose at build time
- publication must not consume raw LLM suggestions directly
- publication should consume accepted constructs, accepted relations, approved analysis receipts, and approved draft structure
- theory-backed publication output should be emitted as typed publication blocks, claims, tables, figures, and receipts, not as an opaque prose dump

This changes the practical interpretation of the theory wiring:

- `Itemize` discovers construct candidates
- `Draft` curates and models them
- `Review` approves the shaped draft and theory-backed receipts
- `Publication` consumes only approved typed outputs

## Problem

The theory is explicit, typed, and narrow.

The corpus is not.

One admitted subject item may contain:

- one actor
- two constraints
- a current-state fact
- a target-state fact
- a transition candidate

If the workstation jumps directly from broad review items into a decision model, then:

- the mapping is too implicit
- LLM assistance becomes magical instead of inspectable
- missing constructs are hard to see
- publication can look decision-grade while the model underneath is still muddy

So the real problem is not “how to run the theory”.

It is:

- how to discover and govern the theory constructs before the theory is run

## Core Implementation Decision

Do not add a new top-level workstation tab yet.

Use the existing workflow stages, but give them sharper responsibilities:

1. `Gather`
- admit subject material
- do not do theory mapping here

2. `Itemize`
- discover construct candidates
- split broad subject material into theory-relevant seeds
- keep this at candidate level, not final model level

3. `Draft`
- become the actual coordinated-transformation modeling workbench
- curate accepted constructs
- bind them into `DecisionFrame` and explicit model relations
- run analysis and inspect missingness

4. `Review`
- validate maintained-file alignment and approve the draft/report plan
- inspect decision-analysis receipts
- do not own first-pass construct finding

5. `Publication`
- consume approved model outputs into decision aids and recommendation sections
- do not infer the model from prose

Inside that existing flow, DST should converge toward one stable case workspace with three lenses:

- `Frame`
  - what is this case
- `Model`
  - how is it structured
- `Explore`
  - what solutions or paths exist

Those lenses should not replace the workstation phases.

They should sit inside the DST-capable workbench, principally in `Draft`, while preserving the same selected object and inspector across lens changes.

This is the correct split because:

- `Itemize` is for discovery and normalization
- `Draft` is for structure and decision shaping
- `Review` is for approval

That is consistent with:

- `../design/AXIOMATIC_SYSTEM_FOR_DESIGN.md`
  - progressive disclosure
  - effort minimization
  - hierarchical structuring
  - error prevention over correction
- `PUBLICATION.md`
  - publication must be built from typed governed inputs, not free prose inference

## Tab Ownership

## `Gather`

`Gather` should own:

- source admission
- subject activation
- maintained-file comparison when needed

`Gather` should not own:

- theory construct discovery
- decision-role assignment
- explicit state/transition modeling

Reason:

- this phase should stay low-ambiguity and low-cognitive-load
- adding theory work here would mix intake with modeling too early

## `Itemize`

`Itemize` should own:

- first-pass construct discovery
- candidate splitting
- candidate typing
- candidate confidence
- candidate rejection

Specifically, `Itemize` should be the phase where the system asks:

- does this item contain an actor?
- does this item contain an objective?
- does this item contain a capability?
- does this item contain a dependency?
- does this item contain a constraint?
- does this item contain a boundary?
- does this item contain a current or target state?
- does this item contain a transition candidate?
- does this item contain a decision candidate?

This should be candidate-level only.

`Itemize` should not yet decide:

- whether the candidate is part of the active frame
- how it relates to every other candidate
- whether it produces a final recommendation

`Itemize` should also not become a manual gate that forces the operator to promote every candidate one by one before `Draft` can begin.

The correct effort-minimizing rule is:

- all non-rejected construct candidates should carry into `Draft` automatically
- `promoted` remains a useful positive signal, not a prerequisite for visibility in `Draft`

The user should first see the whole construct field in `Draft`, then narrow it there.

This means `Itemize` is the first practical entry into the `Frame` lens, but not the permanent host for the full DST workspace.

### Itemize Actions To Add

The next clean actions in `Itemize` should be:

- `Suggest Transformation Constructs`
- `Cycle Theory Sort`
- `Split Into Constructs`
- `Promote To Construct Seed`
- `Reject Construct Seed`
- `Suggest Missing Constructs For Selected Item`
- `Open Source Basis`

### Itemize Result Shape

The result of `Itemize` should be a set of persisted construct candidates such as:

- `actor_candidate`
- `objective_candidate`
- `capability_candidate`
- `dependency_candidate`
- `constraint_candidate`
- `boundary_candidate`
- `current_state_candidate`
- `target_state_candidate`
- `transition_candidate`
- `decision_candidate`

These can remain one broad `decision_role_candidate` internally at first if needed, but the user-facing direction should move toward the actual theory sorts.

The visible output of `Itemize` should therefore be:

- a normalized candidate inventory
- explicit candidate sort hints
- confidence and source basis
- candidate status

It should not yet look like a full theory editor.

## `Draft`

`Draft` should be the main coordinated-transformation workbench.

This is where the operator should:

- create or select a `DecisionFrame`
- choose which construct seeds are in or out
- convert seeds into accepted theory constructs
- bind relations across constructs
- inspect model completeness
- run analysis
- inspect admissibility / validity / executability / risk / reachability

This is the correct home because:

- `Draft` already owns composition and shaping
- the theory model is part of shaping decision-grade report structure
- `Review` should not do first-pass modeling

`Draft` must not become a wall of equal-priority panes.

The operator should be able to move through:

1. candidate field
2. accepted constructs
3. relation binding
4. model completeness
5. analysis receipt

without all five competing at once.

`Draft` should therefore converge toward explicit `Frame | Model | Explore` lens controls over the same case object:

- `Frame`
  - case summary
  - actors
  - objectives
  - assumptions
  - ambiguities
  - missing information
- `Model`
  - accepted constructs
  - lanes
  - relations
  - states
  - transitions
  - decisions
  - assignments
- `Explore`
  - alternative paths
  - admissibility and executability comparison
  - rationale and receipts

The same selected object should remain focused across these lenses, and the same inspector should keep showing:

- what is selected
- what it means
- what it links to
- what is missing
- why it matters

### Draft Needs Two Submodes

Do not add another top-level tab yet.

Inside `Draft`, add a bounded mode split:

1. `Compose`
- current review/draft composition behavior

2. `Model`
- coordinated-transformation workbench

That preserves progressive disclosure and keeps the user from facing too many equal-priority surfaces at once.

The important constraint is:

- this is a mode split, not another grid of permanent peer panes

Only one of `Compose` or `Model` should be the dominant active work surface at a time.

### Draft / Model Workbench

The `Model` submode should expose:

1. `Decision Frame`
- question
- decision mode
- current states
- target states
- objectives
- scope boundaries

2. `Construct Lanes`
- actors
- capabilities
- dependencies
- constraints
- boundaries
- states
- transitions
- decisions

3. `Relation Editing`
- transition source -> target
- transition -> changed capability
- capability -> dependency
- capability -> constraint
- transition -> dependency
- transition -> constraint
- actor -> can decide decision
- decision -> selects transition
- decision -> assigns actor to capability

4. `Model Preview`
- construct counts
- missing required relations
- axiom violations
- blocked analysis reasons

5. `Analysis Receipt`
- admissible transitions
- valid decisions
- executable decisions
- risk summary
- reachable states
- blocking conditions

The order above is intentional.

The operator should move from construct selection to relation binding to explicit analysis, not jump straight from text to recommendation.

### Draft Actions To Add

In the `Model` submode, the first good actions are:

- `Create Decision Frame`
- `Add Selected Candidate To Frame`
- `Accept As Actor`
- `Accept As Objective`
- `Accept As Capability`
- `Accept As Dependency`
- `Accept As Constraint`
- `Accept As Boundary`
- `Accept As Current State`
- `Accept As Target State`
- `Accept As Transition`
- `Accept As Decision`
- `Bind Transition`
- `Bind Decision Selection`
- `Bind Assignment`
- `Suggest Missing Constructs`
- `Suggest Missing Relations`
- `Analyze Model`

## `Review`

`Review` should own:

- maintained-file comparison
- report-plan approval
- decision-analysis receipt inspection
- approval or rejection of the decision-bearing draft

`Review` should not own:

- first-pass construct extraction
- relation modeling
- theory candidate discovery

The key rule is:

- if the user is still discovering what the actors, constraints, and transitions are, they are still in `Draft`

## `Publication`

`Publication` should continue to own:

- build and release of approved decision outputs

It should consume:

- approved report plan
- approved decision frame
- approved accepted constructs
- approved accepted relations
- approved theory-backed receipts

It should not:

- infer the decision model from prose at build time
- render raw candidate inventories as if they were final publication truth

The publication-facing outputs should be typed and narrow, for example:

- decision summary blocks
- option matrices
- dependency checklists
- risk matrices
- transition roadmaps
- decision model diagrams
- recommendation receipts

If a coordinated-transformation output cannot be expressed as a typed publication block, claim, table, figure, or receipt, it is not ready for `Publication`.

## LLM Role

The LLM should help with construct finding, but only in bounded places.

## Allowed LLM Uses In `Itemize`

- classify a selected candidate into one of the theory sorts
- split one broad candidate into multiple construct seeds
- propose aliases or canonical labels
- propose confidence and rationale

## Allowed LLM Uses In `Draft`

- suggest missing constructs for the active decision frame
- suggest missing relations in the current model
- explain why a current model is blocked
- suggest candidate transitions or assignments from accepted seeds
- summarize risk or missingness from explicit model state

## Forbidden LLM Uses

- silently creating final theory truth without persisted accepted constructs
- silently selecting the final recommendation
- mutating publication outputs without explicit reviewed model changes

The LLM should propose.

The workstation should persist explicit constructs and relations.

That is required by both design and publication constraints:

- design requires inspectable feedback and low ambiguity
- publication requires governed typed inputs

## Proposed Object Layer

The current `DecisionReviewItem` is useful, but too coarse for first-pass construct finding.

The cleaner intermediate layer is:

`ItemizedSubjectItem -> TransformationConstructCandidate -> DecisionReviewItem -> coordinated_transformation.Model`

### `TransformationConstructCandidate`

Recommended fields:

- `construct_candidate_id`
- `subject_id`
- `itemized_item_id`
- `review_item_id`
- `sort_kind`
- `canonical_label`
- `summary`
- `source_refs`
- `confidence`
- `status`
- `notes`
- `relation_hints`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`

### `sort_kind`

The first narrow set should be:

- `actor`
- `objective`
- `capability`
- `dependency`
- `constraint`
- `boundary`
- `state`
- `transition`
- `decision`

`time` can remain deferred initially unless the user has explicit time-bearing decisions that matter in the report slice.

## Deterministic-First Discovery

Construct finding should stay deterministic-first.

Good deterministic seeds:

- entity-like item -> actor or boundary candidate
- goal/desired outcome claim -> objective candidate
- process/mechanism item -> capability candidate
- prerequisite/xref/support item -> dependency candidate
- policy/prohibition/threshold item -> constraint candidate
- current situation statement -> current-state candidate
- target outcome statement -> target-state candidate
- roadmap/change path item -> transition candidate
- option/recommendation item -> decision candidate

Then the LLM can refine, split, or suggest missing pieces.

The system should prefer:

1. deterministic seed
2. explicit operator-visible refinement
3. explicit acceptance into the active model
4. theory execution
5. publication consumption

and avoid:

1. prose
2. hidden semantic leap
3. direct recommendation

## Recommended Module Additions

The first concrete additions should likely be:

- `decision_review_constructs.py`
- `decision_review_construct_projection.py`
- `decision_review_construct_validation.py`

These should sit beside:

- `decision_review.py`
- `decision_review_projection.py`

The goal is to avoid making `decision_review.py` carry both:

- candidate-finding concerns
- final model/projection concerns

## Implementation Phases

### Phase 1. Construct Candidates In `Itemize`

Add:

- construct-candidate persistence
- LLM-assisted construct suggestion from selected itemized candidates
- theory-sort cycling and split flows

Acceptance:

- `Itemize` can persist explicit candidate constructs
- the user can move from one broad item to multiple theory-relevant construct seeds
- all non-rejected construct candidates automatically appear in `Draft`

### Phase 2. Draft `Model` Submode

Add:

- `Compose | Model` split inside `Draft`
- decision-frame editing in the model submode
- construct-lane views

Acceptance:

- the user can enter `Draft` and work on a model without leaving the draft workbench
- `Draft` starts from the carried-forward candidate inventory, not from an empty modeling surface
- `Compose` and `Model` do not compete as equal simultaneous surfaces

### Phase 3. Relation Editing And Validation

Add:

- transition/source/target binding
- decision/selection binding
- assignment binding
- missing-relation detection

Acceptance:

- the user can create a concrete `coordinated_transformation.Model`
- validation failures are inspectable before publication

### Phase 4. Analysis And Missingness

Add:

- analysis receipt generation from the explicit model
- LLM-assisted missingness suggestions from that explicit model

Acceptance:

- analysis can distinguish:
  - valid but not executable
  - blocked by dependency
  - blocked by constraint
  - boundary-friction-heavy
  - missing assignment

### Phase 5. Publication Consumption

Add:

- publication blocks that consume the approved frame/model/receipt directly

Acceptance:
- publication can emit decision aids from explicit governed model state
- recommendation text is backed by explicit approved model state and policy evaluation
- publication build does not need to rediscover theory constructs from prose
- decision aids are built from approved modeled structure, not prose inference

## Non-Goals

This implementation is not trying to:

- make `Gather` a modeling phase
- make `Review` discover constructs
- let the LLM silently author the model
- make `Publication` infer a decision model from rendered draft text
- add another top-level workstation tab before the existing five-phase workflow is saturated

## Recommended Immediate Next Step

The first coherent slice is now in place:

1. persisted `TransformationConstructCandidate` support under `Itemize`
2. `Suggest Constructs` on the selected itemized candidate
3. a bounded `Model` submode inside `Draft`
4. acceptance of curated constructs into persisted `DecisionFrame` lanes
5. existing coordinated-transformation analysis can now run over that explicit curated set
6. `Draft Model` now exposes the first explicit `Frame | Model | Explore` lens strip over the same selected construct
7. accepted capabilities can now bind required dependencies and crossed boundaries
8. `Explore` now surfaces a first bounded admissible multi-step path summary from the formal model

The next clean slice is:

1. continue widening `Draft Model` beyond the completed lane/relation and assignment slice:
   - richer construct-lane views
   - broader many-to-many relation editing beyond the completed capability/dependency and capability/boundary slice
   - clearer missingness and assignment summaries
2. preserve and deepen accepted construct relations so `coordinated_transformation` receives more than isolated sort atoms
3. widen the theory bridge beyond the first bounded multi-step path summary into richer multi-step path evaluation

That keeps the path coherent:

- theory on paper
- explicit workstation construct finding
- explicit curated model state
- governed modeled decision output

without adding another top-level tab or collapsing the theory into LLM guesswork.

## External References

These are repo-wide references that sit outside `dst` and `coordinated_transformation`:

- `../design/AXIOMATIC_SYSTEM_FOR_DESIGN.md`
- `PUBLICATION.md`
- `ITEMIZE.md`
- `REVIEW.md`
- `DECISION_REVIEW.md`
- `itemize.py`
- `review_composition.py`
- `decision_review.py`
- `decision_review_projection.py`
- `decision_review_policy.py`
- `publication_projection.py`
- `workstation/subject_workflow.py`
- `DST_PROMPT.md`
