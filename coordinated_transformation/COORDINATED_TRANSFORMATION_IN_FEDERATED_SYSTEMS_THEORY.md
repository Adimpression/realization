# Coordinated Transformation in Federated Systems (CTFS)

## Closed many-sorted first-order core theory

---

## 0. Scope of the closed core

This document defines the closed core theory of coordinated transformation in federated systems (`CTFS`).

The core theory governs:

- the typed objects that exist inside a model
- the predicates and functions that define their relations
- the admissibility, readiness, risk, validity, executability, and reachability judgments that hold inside a model snapshot

The closed core does not define model revision as part of the core language.

So the core must distinguish two different kinds of change:

- state transition inside a fixed model
- model revision that changes the interpreted facts or available objects of the model itself

Formally, the core is snapshot-local.
It tells us what is true in a given model $M$.
It does not, by itself, define how $M_{t_0}$ becomes $M_{t_1}$.

That implementation-level revision discipline belongs in:

- [COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY_IMLEMENTATION.md](COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY_IMLEMENTATION.md)

This separation is intentional.

The closed core remains stable.
Model evolution changes facts, memberships, and valuations across snapshots without changing the meaning of the core predicates and definitional extensions.

---

## 1. Logical framework

We work in a **many-sorted first-order language** with equality.

### 1.1 Sorts

Primitive sorts:

* `Actor`
* `Objective`
* `Capability`
* `Dependency`
* `Constraint`
* `Boundary`
* `State`
* `Transition`
* `Decision`
* `Time`

These are the only primitive sorts.

---

## 2. Signature

## 2.1 Variables

Typed variables:

* `a,b,c : Actor`
* `o : Objective`
* `k,k1,k2 : Capability`
* `d : Dependency`
* `q : Constraint`
* `β : Boundary`
* `s,s1,s2,s3 : State`
* `τ,τ1,τ2 : Transition`
* `δ,δ1,δ2 : Decision`
* `t : Time`

---

## 2.2 Primitive predicates

### Actor predicates

* `Pursues(a,o)`
* `Controls(a,k)`
* `BenefitsFrom(a,k)`
* `BearsCost(a,k)`
* `BearsRisk(a,k)`
* `CanDecide(a,δ)`

### Capability predicates

* `Advances(k,o)`
* `Requires(k,d)`
* `LimitedBy(k,q)`
* `Crosses(k,β)`
* `Available(k,s)`
* `Operational(k,s)`

### Dependency predicate

* `Satisfied(d,s)`

### Constraint predicates

* `Active(q,s)`
* `AdmissibleUnder(k,q,s)`

### Boundary predicates

Because many-sorted FOL does not permit the original overloaded
`Separates(β,x,y)` with variable sort positions, we replace it by three typed predicates:

* `SeparatesActor(β,a,b)`
* `SeparatesCapability(β,k1,k2)`
* `SeparatesState(β,s1,s2)`
* `FrictionAt(β,s)`

### State predicates

* `Current(s)`
* `Target(s)`
* `Reachable(s1,s2)`

### Transition predicates

* `Changes(τ,k)`
* `RequiresForTransition(τ,d)`
* `ConstrainedByTransition(τ,q)`
* `CrossesTransition(τ,β)`
* `TransitionAdmissibleUnder(τ,q,s)`

### Decision predicates

* `Selects(δ,τ)`
* `Assigns(δ,a,k)`
* `AtTime(δ,t)`
* `Valid(δ,s)`
* `Executable(δ,s)`

---

## 2.3 Primitive functions

* `source : Transition → State`
* `target : Transition → State`

That is all.

No additional primitive functions are assumed.

---

## 3. Primitive theory

The following axioms constitute the core theory.

---

## 3.1 Structural axioms

### A1. Decision single-selection

A decision selects at most one transition.

$$\forall \delta \forall \tau_1 \forall \tau_2 \big((Selects(\delta,\tau_1)\wedge Selects(\delta,\tau_2)) \rightarrow \tau_1=\tau_2\big)$$

### A2. Operational implies available

$$\forall k \forall s \big(Operational(k,s) \rightarrow Available(k,s)\big)$$

### A3. Executable implies valid

$$\forall \delta \forall s \big(Executable(\delta,s) \rightarrow Valid(\delta,s)\big)$$

### A4. Valid decisions originate in the evaluated state

$$\forall \delta \forall s \Big(
Valid(\delta,s) \rightarrow
\exists \tau \big(Selects(\delta,\tau)\wedge source(\tau)=s\big)
\Big)$$

### A5. Assigned actors are decision-capable

$$\forall \delta \forall a \forall k \big(Assigns(\delta,a,k) \rightarrow CanDecide(a,\delta)\big)$$

### A6. Assignments refer only to changed capabilities of the selected transition

$$\forall \delta \forall a \forall k \Big(
Assigns(\delta,a,k) \rightarrow
\exists \tau \big(Selects(\delta,\tau)\wedge Changes(\tau,k)\big)
\Big)$$

---

## 3.2 Definitional extensions

Everything below is definitional, not primitive.

### D1. Capability admissibility

[Admissible(k,s) ;:!!\leftrightarrow;
\Big$$\forall d(Requires(k,d)\rightarrow Satisfied(d,s))
;\wedge;
\forall q((LimitedBy(k,q)\wedge Active(q,s))\rightarrow AdmissibleUnder(k,q,s))
\BigS]

### D2. Transition admissibility

[AdmissibleTransition(\tau,s) ;:!!\leftrightarrow;
\Big$$source(\tau)=s
;\wedge;
\forall d(RequiresForTransition(\tau,d)\rightarrow Satisfied(d,s))
;\wedge;
\forall q((ConstrainedByTransition(\tau,q)\wedge Active(q,s))\rightarrow TransitionAdmissibleUnder(\tau,q,s))
\Big]]

### D3. Capability readiness

$$ReadyCapability(k,s) ;:!!\leftrightarrow; Admissible(k,s)$$

### D4. Transition readiness

$$ReadyTransition(\tau,s) ;:!!\leftrightarrow; AdmissibleTransition(\tau,s)$$

### D5. Capability risk

[RiskCapability(k,s) ;:!!\leftrightarrow;
\Big$$\exists d(Requires(k,d)\wedge \neg Satisfied(d,s))
;\vee;
\exists q(LimitedBy(k,q)\wedge Active(q,s)\wedge \neg AdmissibleUnder(k,q,s))
;\vee;
\exists \beta(Crosses(k,\beta)\wedge FrictionAt(\beta,s))
\Big]$$

### D6. Transition risk

$$
RiskTransition(\tau,s) ;:!!\leftrightarrow;
\Big[
\exists d(RequiresForTransition(\tau,d)\wedge \neg Satisfied(d,s))
;\vee;
\exists q(ConstrainedByTransition(\tau,q)\wedge Active(q,s)\wedge \neg TransitionAdmissibleUnder(\tau,q,s))
;\vee;
\exists \beta(CrossesTransition(\tau,\beta)\wedge FrictionAt(\beta,s))
\Big]
$$

### D7. Capability coordination requirement

Since the original theory relied on an undeclared predicate `Influences(a,k)`, we replace that with the weakest available formal notion: joint control.

$$RequiresCoordinationCapability(k) ;:!!\leftrightarrow; \exists a \exists b \big(a\neq b \wedge Controls(a,k)\wedge Controls(b,k)\big)$$

### D8. Transition coordination requirement

$$RequiresCoordinationTransition(\tau) ;:!!\leftrightarrow;
\exists a \exists b \exists k \big(
a\neq b \wedge Changes(\tau,k)\wedge Controls(a,k)\wedge Controls(b,k)
\big)$$

### D9. Capability coexistence

$$Coexists(k1,k2,s) ;:!!\leftrightarrow; Available(k1,s)\wedge Available(k2,s)$$

### D10. Mixed-mode state

To avoid assuming any unintroduced “legacy/new” relation, mixed-mode is defined exactly and only by coexistence of distinct capabilities.

$$MixedMode(s) ;:!!\leftrightarrow; \exists k1 \exists k2 \big(k1\neq k2 \wedge Coexists(k1,k2,s)\big)$$

### D11. Boundary friction

$$BoundaryFriction(\beta,s) ;:!!\leftrightarrow; FrictionAt(\beta,s)$$

### D12. Fallback

The original fallback definition used an undeclared predicate `Degraded`. To avoid assumptions, fallback cannot be defined in the core from available symbols. Therefore it is removed from the closed core theory.

It may be added only in a domain extension.

---

## 3.3 Semantic axioms relating validity and executability to admissibility

### A7. Validity requires selection of an admissible transition from the given state

$$\forall \delta \forall s \Big(
Valid(\delta,s) \rightarrow
\exists \tau(Selects(\delta,\tau)\wedge AdmissibleTransition(\tau,s))
\Big)$$

### A8. Executability preserves transition admissibility

$$\forall \delta \forall s \forall \tau \Big(
(Executable(\delta,s)\wedge Selects(\delta,\tau)) \rightarrow AdmissibleTransition(\tau,s)
\Big)$$

### A9. Validity requires at least one assignment for each changed capability

$$\forall \delta \forall s \forall \tau \forall k \Big(
(Valid(\delta,s)\wedge Selects(\delta,\tau)\wedge Changes(\tau,k))
\rightarrow
\exists a, Assigns(\delta,a,k)
\Big)$$

This avoids the earlier undeclared appeal to agency relevance via `Influences`.

### A10. Executability requires validity plus assigned decision capability

$$\forall \delta \forall s \Big(
Executable(\delta,s) \rightarrow
Valid(\delta,s)\wedge
\forall a \forall k (Assigns(\delta,a,k)\rightarrow CanDecide(a,\delta))
\Big)$$

This remains first-order and closed.

---

## 3.4 Reachability axioms

The original statement made `Reachable` only a one-step consequence. To keep the theory first-order while making `Reachable` nontrivial, we axiomatize it as a reflexive transitive relation containing admissible one-step moves.

### A11. Reflexivity

$$\forall s , Reachable(s,s)$$

### A12. One-step admissible transitions imply reachability

$$\forall \tau \forall s \Big(
AdmissibleTransition(\tau,s) \rightarrow Reachable(s,target(\tau))
\Big)$$

### A13. Transitivity

$$\forall s_1 \forall s_2 \forall s_3 \Big(
(Reachable(s_1,s_2)\wedge Reachable(s_2,s_3)) \rightarrow Reachable(s_1,s_3)
\Big)$$

This does not force `Reachable` to be the smallest such relation, because minimality is not first-order expressible here, but it gives a rigorous first-order semantics without pretending to define transitive closure.

---

## 4. Formal definitions of the constructs

These are now strict and minimal.

### Definition 1. Actor

An `Actor` is an element of sort `Actor`.

Its formal role is exhausted by the primitive predicates in which it occurs:
`Pursues`, `Controls`, `BenefitsFrom`, `BearsCost`, `BearsRisk`, `CanDecide`, `Assigns`.

### Definition 2. Objective

An `Objective` is an element of sort `Objective`.

Its formal role is to be pursued by actors and advanced by capabilities.

### Definition 3. Capability

A `Capability` is an element of sort `Capability`.

Its formal role is to:

* advance objectives,
* require dependencies,
* be limited by constraints,
* cross boundaries,
* be available or operational in states,
* and be changed by transitions.

### Definition 4. Dependency

A `Dependency` is an element of sort `Dependency`.

Its formal role is to be required by capabilities or transitions and satisfied or unsatisfied in states.

### Definition 5. Constraint

A `Constraint` is an element of sort `Constraint`.

Its formal role is to restrict capability or transition admissibility through state-indexed activity.

### Definition 6. Boundary

A `Boundary` is an element of sort `Boundary`.

Its formal role is to separate typed entities through typed separation predicates and to exhibit friction in states.

### Definition 7. State

A `State` is an element of sort `State`.

Its formal role is to host availability, operationality, dependency satisfaction, constraint activity, and boundary friction, and to serve as source or target of transitions.

### Definition 8. Transition

A `Transition` is an element of sort `Transition`.

Its formal role is given by `source`, `target`, `Changes`, `RequiresForTransition`, `ConstrainedByTransition`, and `CrossesTransition`.

### Definition 9. Decision

A `Decision` is an element of sort `Decision`.

Its formal role is given by `Selects`, `Assigns`, `AtTime`, `Valid`, and `Executable`.

No tuple reduction is assumed in the core theory.

---

## 5. What has been removed because it could not be justified without extra assumptions

The following notions were present before but are not definable from the declared core signature without introducing new primitives. Therefore they are **not part of the closed core theory**:

* `Influences(a,k)`
* `CoordinatesOn(a,k)`
* `DependsOnActorFor(a,k)`
* `PotentialBoundaryEffect(β)`
* `BoundaryRisk(β,s)`
* `RelevantActorPrepared(a,k,s)`
* `AuthorityOver(b,q)`
* `GovernanceDependent(a,k,s)`
* `Degraded(s1,s2)`
* `FallbackFor(τf,τ)` as previously defined
* `AgencyConsistent(δ)`
* `ConstraintConsistent(δ,s)`
* `CoordinationSatisfied(δ,s)`
* `PreparationSatisfied(δ,s)`
* `RelevantTo(a,x)`
* `View_a`
* the preorder `\(\succeq_{a,s}\)` unless added as a second-order or indexed relational extension

They may all be added later, but only as an explicit extension layer.

---

## 6. Extension discipline

To preserve rigor, any future extension must be introduced in one of only two ways.

### 6.1 Definitional extension

A new symbol is allowed if it is introduced by a biconditional over already existing symbols.

Example form:
$$NewSymbol(\bar{x}) ;:!!\leftrightarrow; \varphi(\bar{x})$$

### 6.2 Primitive extension

A new symbol may be added to the signature only if:

* its sort and arity are declared,
* and its governing axioms are explicitly added.

Nothing else is allowed.

---

## 7. Closed lexicon

## 7.1 Primitive sorts

* `Actor`
* `Objective`
* `Capability`
* `Dependency`
* `Constraint`
* `Boundary`
* `State`
* `Transition`
* `Decision`
* `Time`

## 7.2 Primitive predicates

* `Pursues(a,o)`
* `Controls(a,k)`
* `BenefitsFrom(a,k)`
* `BearsCost(a,k)`
* `BearsRisk(a,k)`
* `CanDecide(a,δ)`
* `Advances(k,o)`
* `Requires(k,d)`
* `LimitedBy(k,q)`
* `Crosses(k,β)`
* `Available(k,s)`
* `Operational(k,s)`
* `Satisfied(d,s)`
* `Active(q,s)`
* `AdmissibleUnder(k,q,s)`
* `SeparatesActor(β,a,b)`
* `SeparatesCapability(β,k1,k2)`
* `SeparatesState(β,s1,s2)`
* `FrictionAt(β,s)`
* `Current(s)`
* `Target(s)`
* `Reachable(s1,s2)`
* `Changes(τ,k)`
* `RequiresForTransition(τ,d)`
* `ConstrainedByTransition(τ,q)`
* `CrossesTransition(τ,β)`
* `TransitionAdmissibleUnder(τ,q,s)`
* `Selects(δ,τ)`
* `Assigns(δ,a,k)`
* `AtTime(δ,t)`
* `Valid(δ,s)`
* `Executable(δ,s)`

## 7.3 Primitive functions

* `source : Transition → State`
* `target : Transition → State`

## 7.4 Defined predicates

* `Admissible(k,s)`
* `AdmissibleTransition(τ,s)`
* `ReadyCapability(k,s)`
* `ReadyTransition(τ,s)`
* `RiskCapability(k,s)`
* `RiskTransition(τ,s)`
* `RequiresCoordinationCapability(k)`
* `RequiresCoordinationTransition(τ)`
* `Coexists(k1,k2,s)`
* `MixedMode(s)`
* `BoundaryFriction(β,s)`

---

## 8. Minimal model structure

A model of the closed theory is a many-sorted structure

$$\mathcal{M} =
(A,O,K,D,Q,B,S,T,\Delta,\Theta; \text{relations}; \text{functions})$$

where:

* `A` interprets `Actor`
* `O` interprets `Objective`
* `K` interprets `Capability`
* `D` interprets `Dependency`
* `Q` interprets `Constraint`
* `B` interprets `Boundary`
* `S` interprets `State`
* `T` interprets `Transition`
* `Δ` interprets `Decision`
* `Θ` interprets `Time`

and all primitive predicates and functions are interpreted over those domains subject to A1–A13.

---

## 10. Governing sentence, repaired

A coordinated transformation system is a many-sorted structure in which actors pursue objectives through decisions that select transitions between states, where the admissibility of capabilities and transitions depends on dependencies and constraints, and where boundary friction may create risk for capabilities or transitions that cross boundaries.

That sentence is now strictly faithful to the formal core.

---

## 11. Exact status of the repaired theory

This version fixes the original defects:

* no overloaded `Separates`,
* no undeclared symbols,
* no tuple-identification assumptions for decisions,
* no silent appeal to undefined actor influence,
* no pseudo-definition of fallback without an ordering or degradation relation,
* no false claim that transitive reachability was fully defined when it was only implied one-step.

What it does **not** do is smuggle in richer governance, actor-view, or decision-ranking semantics. Those require an explicit extension.

That is the price of rigor.

---

## 12. Proposed extension layer

The next mathematically proper move is to build **Extension Layer 1** with only explicitly declared new primitives:

* `Influences(a,k)`
* `AuthorityOver(a,q)`
* `Degraded(s1,s2)`
* `RelevantToActorCapability(a,k,s)` or a more general relevance family
* `AtLeastAsActionable(a,s,δ1,δ2)`

Then axiomatize them cleanly.

That would recover:

* governance dependence,
* actor-relative views,
* fallback,
* and actionability ordering,

without breaking closure.

---

# TPTP

## /theory/coordinated_transformation_core.p

```tptp

%--------------------------------------------------------------------------
% Coordinated Transformation in Federated Systems
% Closed many-sorted first-order core theory
% TPTP TFF version
%--------------------------------------------------------------------------

%--------------------------------------------------------------------------
% Sort declarations
%--------------------------------------------------------------------------

tff(actor_type, type, actor: $tType).
tff(objective_type, type, objective: $tType).
tff(capability_type, type, capability: $tType).
tff(dependency_type, type, dependency: $tType).
tff(constraint_type, type, constraint: $tType).
tff(boundary_type, type, boundary: $tType).
tff(state_type, type, state: $tType).
tff(transition_type, type, transition: $tType).
tff(decision_type, type, decision: $tType).
tff(time_type, type, time: $tType).

%--------------------------------------------------------------------------
% Primitive predicate declarations
%--------------------------------------------------------------------------

% Actor predicates
tff(pursues_type, type, pursues: (actor * objective) > $o).
tff(controls_type, type, controls: (actor * capability) > $o).
tff(benefits_from_type, type, benefits_from: (actor * capability) > $o).
tff(bears_cost_type, type, bears_cost: (actor * capability) > $o).
tff(bears_risk_type, type, bears_risk: (actor * capability) > $o).
tff(can_decide_type, type, can_decide: (actor * decision) > $o).

% Capability predicates
tff(advances_type, type, advances: (capability * objective) > $o).
tff(requires_type, type, requires: (capability * dependency) > $o).
tff(limited_by_type, type, limited_by: (capability * constraint) > $o).
tff(crosses_type, type, crosses: (capability * boundary) > $o).
tff(available_type, type, available: (capability * state) > $o).
tff(operational_type, type, operational: (capability * state) > $o).

% Dependency predicate
tff(satisfied_type, type, satisfied: (dependency * state) > $o).

% Constraint predicates
tff(active_type, type, active: (constraint * state) > $o).
tff(admissible_under_type, type, admissible_under: (capability * constraint * state) > $o).

% Boundary predicates
tff(separates_actor_type, type, separates_actor: (boundary * actor * actor) > $o).
tff(separates_capability_type, type, separates_capability: (boundary * capability * capability) > $o).
tff(separates_state_type, type, separates_state: (boundary * state * state) > $o).
tff(friction_at_type, type, friction_at: (boundary * state) > $o).

% State predicates
tff(current_type, type, current: (state) > $o).
tff(target_state_type, type, target_state: (state) > $o).
tff(reachable_type, type, reachable: (state * state) > $o).

% Transition predicates
tff(changes_type, type, changes: (transition * capability) > $o).
tff(requires_for_transition_type, type, requires_for_transition: (transition * dependency) > $o).
tff(constrained_by_transition_type, type, constrained_by_transition: (transition * constraint) > $o).
tff(crosses_transition_type, type, crosses_transition: (transition * boundary) > $o).
tff(transition_admissible_under_type, type,
    transition_admissible_under: (transition * constraint * state) > $o).

% Decision predicates
tff(selects_type, type, selects: (decision * transition) > $o).
tff(assigns_type, type, assigns: (decision * actor * capability) > $o).
tff(at_time_type, type, at_time: (decision * time) > $o).
tff(valid_type, type, valid: (decision * state) > $o).
tff(executable_type, type, executable: (decision * state) > $o).

%--------------------------------------------------------------------------
% Primitive function declarations
%--------------------------------------------------------------------------

tff(source_type, type, source: transition > state).
tff(target_type, type, target: transition > state).

%--------------------------------------------------------------------------
% Defined predicate declarations
%--------------------------------------------------------------------------

tff(admissible_type, type, admissible: (capability * state) > $o).
tff(admissible_transition_type, type, admissible_transition: (transition * state) > $o).
tff(ready_capability_type, type, ready_capability: (capability * state) > $o).
tff(ready_transition_type, type, ready_transition: (transition * state) > $o).
tff(risk_capability_type, type, risk_capability: (capability * state) > $o).
tff(risk_transition_type, type, risk_transition: (transition * state) > $o).
tff(requires_coordination_capability_type, type,
    requires_coordination_capability: (capability) > $o).
tff(requires_coordination_transition_type, type,
    requires_coordination_transition: (transition) > $o).
tff(coexists_type, type, coexists: (capability * capability * state) > $o).
tff(mixed_mode_type, type, mixed_mode: (state) > $o).
tff(boundary_friction_type, type, boundary_friction: (boundary * state) > $o).

%--------------------------------------------------------------------------
% Core axioms
%--------------------------------------------------------------------------

% A1. Decision single-selection
tff(a1_decision_single_selection, axiom,
    ![D: decision, T1: transition, T2: transition]:
      ((selects(D,T1) & selects(D,T2)) => (T1 = T2))).

% A2. Operational implies available
tff(a2_operational_implies_available, axiom,
    ![K: capability, S: state]:
      (operational(K,S) => available(K,S))).

% A3. Executable implies valid
tff(a3_executable_implies_valid, axiom,
    ![D: decision, S: state]:
      (executable(D,S) => valid(D,S))).

% A4. Valid decisions originate in the evaluated state
tff(a4_valid_originates_in_state, axiom,
    ![D: decision, S: state]:
      (valid(D,S) =>
        ?[T: transition]:
          (selects(D,T) & (source(T) = S)))).

% A5. Assigned actors are decision-capable
tff(a5_assigned_actor_decision_capable, axiom,
    ![D: decision, A: actor, K: capability]:
      (assigns(D,A,K) => can_decide(A,D))).

% A6. Assignments refer only to changed capabilities of the selected transition
tff(a6_assignments_only_for_changed_capabilities, axiom,
    ![D: decision, A: actor, K: capability]:
      (assigns(D,A,K) =>
        ?[T: transition]:
          (selects(D,T) & changes(T,K)))).

%--------------------------------------------------------------------------
% Definitional extensions
%--------------------------------------------------------------------------

% D1. Capability admissibility
tff(d1_capability_admissibility, axiom,
    ![K: capability, S: state]:
      (admissible(K,S) <=>
        ((![Dep: dependency]:
            (requires(K,Dep) => satisfied(Dep,S)))
         &
         (![Q: constraint]:
            ((limited_by(K,Q) & active(Q,S)) => admissible_under(K,Q,S)))))).

% D2. Transition admissibility
tff(d2_transition_admissibility, axiom,
    ![T: transition, S: state]:
      (admissible_transition(T,S) <=>
        (((source(T) = S)
          &
          (![Dep: dependency]:
             (requires_for_transition(T,Dep) => satisfied(Dep,S)))
          &
          (![Q: constraint]:
             ((constrained_by_transition(T,Q) & active(Q,S))
               => transition_admissible_under(T,Q,S))))))).

% D3. Capability readiness
tff(d3_capability_readiness, axiom,
    ![K: capability, S: state]:
      (ready_capability(K,S) <=> admissible(K,S))).

% D4. Transition readiness
tff(d4_transition_readiness, axiom,
    ![T: transition, S: state]:
      (ready_transition(T,S) <=> admissible_transition(T,S))).

% D5. Capability risk
tff(d5_capability_risk, axiom,
    ![K: capability, S: state]:
      (risk_capability(K,S) <=>
        ((?[Dep: dependency]:
            (requires(K,Dep) & ~satisfied(Dep,S)))
         |
         (?[Q: constraint]:
            (limited_by(K,Q) & active(Q,S) & ~admissible_under(K,Q,S)))
         |
         (?[B: boundary]:
            (crosses(K,B) & friction_at(B,S)))))).

% D6. Transition risk
tff(d6_transition_risk, axiom,
    ![T: transition, S: state]:
      (risk_transition(T,S) <=>
        ((?[Dep: dependency]:
            (requires_for_transition(T,Dep) & ~satisfied(Dep,S)))
         |
         (?[Q: constraint]:
            (constrained_by_transition(T,Q) & active(Q,S)
             & ~transition_admissible_under(T,Q,S)))
         |
         (?[B: boundary]:
            (crosses_transition(T,B) & friction_at(B,S)))))).

% D7. Capability coordination requirement
tff(d7_capability_coordination_requirement, axiom,
    ![K: capability]:
      (requires_coordination_capability(K) <=>
        ?[A1: actor, A2: actor]:
          ((A1 != A2) & controls(A1,K) & controls(A2,K)))).

% D8. Transition coordination requirement
tff(d8_transition_coordination_requirement, axiom,
    ![T: transition]:
      (requires_coordination_transition(T) <=>
        ?[A1: actor, A2: actor, K: capability]:
          ((A1 != A2) & changes(T,K) & controls(A1,K) & controls(A2,K)))).

% D9. Capability coexistence
tff(d9_capability_coexistence, axiom,
    ![K1: capability, K2: capability, S: state]:
      (coexists(K1,K2,S) <=> (available(K1,S) & available(K2,S)))).

% D10. Mixed-mode state
tff(d10_mixed_mode_state, axiom,
    ![S: state]:
      (mixed_mode(S) <=>
        ?[K1: capability, K2: capability]:
          ((K1 != K2) & coexists(K1,K2,S)))).

% D11. Boundary friction
tff(d11_boundary_friction, axiom,
    ![B: boundary, S: state]:
      (boundary_friction(B,S) <=> friction_at(B,S))).

%--------------------------------------------------------------------------
% Semantic axioms relating validity and executability to admissibility
%--------------------------------------------------------------------------

% A7. Validity requires selection of an admissible transition from the given state
tff(a7_validity_requires_admissible_transition, axiom,
    ![D: decision, S: state]:
      (valid(D,S) =>
        ?[T: transition]:
          (selects(D,T) & admissible_transition(T,S)))).

% A8. Executability preserves transition admissibility
tff(a8_executability_preserves_transition_admissibility, axiom,
    ![D: decision, S: state, T: transition]:
      ((executable(D,S) & selects(D,T)) => admissible_transition(T,S))).

% A9. Validity requires at least one assignment for each changed capability
tff(a9_validity_requires_assignments_for_changed_capabilities, axiom,
    ![D: decision, S: state, T: transition, K: capability]:
      ((valid(D,S) & selects(D,T) & changes(T,K)) =>
        ?[A: actor]:
          assigns(D,A,K))).

% A10. Executability requires validity plus assigned decision capability
tff(a10_executability_requires_validity_and_decision_capability, axiom,
    ![D: decision, S: state]:
      (executable(D,S) =>
        (valid(D,S)
         &
         (![A: actor, K: capability]:
            (assigns(D,A,K) => can_decide(A,D)))))).

%--------------------------------------------------------------------------
% Reachability axioms
%--------------------------------------------------------------------------

% A11. Reflexivity
tff(a11_reachability_reflexive, axiom,
    ![S: state]:
      reachable(S,S)).

% A12. One-step admissible transitions imply reachability
tff(a12_one_step_admissible_implies_reachable, axiom,
    ![T: transition, S: state]:
      (admissible_transition(T,S) => reachable(S,target(T)))).

% A13. Transitivity
tff(a13_reachability_transitive, axiom,
    ![S1: state, S2: state, S3: state]:
      ((reachable(S1,S2) & reachable(S2,S3)) => reachable(S1,S3))).

%--------------------------------------------------------------------------
% End of theory
%--------------------------------------------------------------------------

```

## /theory/coordinated_transformation_notes.md

```
# Notes

- This is a closed TFF theory.
- `target_state` is the unary predicate for target states.
- `target` is reserved for the function `transition -> state`.
- Derived notions are encoded as ordinary biconditional axioms.
- `Reachable` is axiomatized as reflexive and transitive and as containing
  one-step admissible transitions, but not as the least such relation.
- `FallbackFor`, governance dependence, actor-relative views, and actionability
  ordering are intentionally omitted from the closed core because they require
  additional primitives or stronger logic.


```

## /theory/coordinated_transformation_core_with_queries.p

```tptp
%--------------------------------------------------------------------------
% Optional query skeletons for theorem provers/model finders
% These are not part of the core theory itself.
%--------------------------------------------------------------------------

% Example conjecture:
% Every executable decision selects a transition whose source is the evaluated state.

tff(exec_selects_source_state_conj, conjecture,
    ![D: decision, S: state]:
      ((executable(D,S)) =>
        ?[T: transition]:
          (selects(D,T) & (source(T) = S)))).
          
```
---

# Python


```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Iterator, Generic, TypeVar


# ============================================================================
# Sort atoms
# ============================================================================

@dataclass(frozen=True, slots=True)
class Actor:
    name: str


@dataclass(frozen=True, slots=True)
class Objective:
    name: str


@dataclass(frozen=True, slots=True)
class Capability:
    name: str


@dataclass(frozen=True, slots=True)
class Dependency:
    name: str


@dataclass(frozen=True, slots=True)
class Constraint:
    name: str


@dataclass(frozen=True, slots=True)
class Boundary:
    name: str


@dataclass(frozen=True, slots=True)
class State:
    name: str


@dataclass(frozen=True, slots=True)
class Transition:
    name: str


@dataclass(frozen=True, slots=True)
class Decision:
    name: str


@dataclass(frozen=True, slots=True)
class TimePoint:
    value: str


# ============================================================================
# Relation aliases
# ============================================================================

A2 = tuple[Actor, Actor]
AK = tuple[Actor, Capability]
AO = tuple[Actor, Objective]
ADec = tuple[Actor, Decision]

CO = tuple[Capability, Objective]
CD = tuple[Capability, Dependency]
CQ = tuple[Capability, Constraint]
CB = tuple[Capability, Boundary]
CS = tuple[Capability, State]

DS = tuple[Dependency, State]
QS = tuple[Constraint, State]
CQS = tuple[Capability, Constraint, State]

BAA = tuple[Boundary, Actor, Actor]
BKK = tuple[Boundary, Capability, Capability]
BSS = tuple[Boundary, State, State]
BS = tuple[Boundary, State]

SS = tuple[State, State]

TK = tuple[Transition, Capability]
TD = tuple[Transition, Dependency]
TQ = tuple[Transition, Constraint]
TB = tuple[Transition, Boundary]
TQS = tuple[Transition, Constraint, State]

DT = tuple[Decision, Transition]
DAK = tuple[Decision, Actor, Capability]
DTime = tuple[Decision, TimePoint]
DS_validity = tuple[Decision, State]


# ============================================================================
# Core model
# ============================================================================

@dataclass(slots=True)
class Model:
    # Carriers
    actors: FrozenSet[Actor] = frozenset()
    objectives: FrozenSet[Objective] = frozenset()
    capabilities: FrozenSet[Capability] = frozenset()
    dependencies: FrozenSet[Dependency] = frozenset()
    constraints: FrozenSet[Constraint] = frozenset()
    boundaries: FrozenSet[Boundary] = frozenset()
    states: FrozenSet[State] = frozenset()
    transitions: FrozenSet[Transition] = frozenset()
    decisions: FrozenSet[Decision] = frozenset()
    times: FrozenSet[TimePoint] = frozenset()

    # Primitive relations
    pursues: FrozenSet[AO] = frozenset()
    controls: FrozenSet[AK] = frozenset()
    benefits_from: FrozenSet[AK] = frozenset()
    bears_cost: FrozenSet[AK] = frozenset()
    bears_risk: FrozenSet[AK] = frozenset()
    can_decide: FrozenSet[ADec] = frozenset()

    advances: FrozenSet[CO] = frozenset()
    requires: FrozenSet[CD] = frozenset()
    limited_by: FrozenSet[CQ] = frozenset()
    crosses: FrozenSet[CB] = frozenset()
    available: FrozenSet[CS] = frozenset()
    operational: FrozenSet[CS] = frozenset()

    satisfied: FrozenSet[DS] = frozenset()

    active: FrozenSet[QS] = frozenset()
    admissible_under: FrozenSet[CQS] = frozenset()

    separates_actor: FrozenSet[BAA] = frozenset()
    separates_capability: FrozenSet[BKK] = frozenset()
    separates_state: FrozenSet[BSS] = frozenset()
    friction_at: FrozenSet[BS] = frozenset()

    current: FrozenSet[State] = frozenset()
    target_state: FrozenSet[State] = frozenset()
    reachable: FrozenSet[SS] = frozenset()

    changes: FrozenSet[TK] = frozenset()
    requires_for_transition: FrozenSet[TD] = frozenset()
    constrained_by_transition: FrozenSet[TQ] = frozenset()
    crosses_transition: FrozenSet[TB] = frozenset()
    transition_admissible_under: FrozenSet[TQS] = frozenset()

    selects: FrozenSet[DT] = frozenset()
    assigns: FrozenSet[DAK] = frozenset()
    at_time: FrozenSet[DTime] = frozenset()
    valid: FrozenSet[DS_validity] = frozenset()
    executable: FrozenSet[DS_validity] = frozenset()

    # Primitive functions
    source: dict[Transition, State] = field(default_factory=dict)
    target: dict[Transition, State] = field(default_factory=dict)

    # --- structural helpers -------------------------------------------------

    def selected_transition(self, d: Decision) -> Transition | None:
        ts = [t for t in self.transitions if (d, t) in self.selects]
        if len(ts) == 1:
            return ts[0]
        return None

    def changed_capabilities(self, t: Transition) -> Iterator[Capability]:
        for k in self.capabilities:
            if (t, k) in self.changes:
                yield k

    def assigned_actors(self, d: Decision, k: Capability) -> Iterator[Actor]:
        for a in self.actors:
            if (d, a, k) in self.assigns:
                yield a

    def transitions_from(self, s: State) -> Iterator[Transition]:
        for t in self.transitions:
            if self.source.get(t) == s:
                yield t

    def decisions_selecting(self, t: Transition) -> Iterator[Decision]:
        for d in self.decisions:
            if (d, t) in self.selects:
                yield d


# ============================================================================
# Derived predicates
# ============================================================================

def admissible(m: Model, k: Capability, s: State) -> bool:
    return (
        all(
            (d, s) in m.satisfied
            for d in m.dependencies
            if (k, d) in m.requires
        )
        and
        all(
            (k, q, s) in m.admissible_under
            for q in m.constraints
            if (k, q) in m.limited_by and (q, s) in m.active
        )
    )


def admissible_transition(m: Model, t: Transition, s: State) -> bool:
    return (
        m.source.get(t) == s
        and
        all(
            (d, s) in m.satisfied
            for d in m.dependencies
            if (t, d) in m.requires_for_transition
        )
        and
        all(
            (t, q, s) in m.transition_admissible_under
            for q in m.constraints
            if (t, q) in m.constrained_by_transition and (q, s) in m.active
        )
    )


def ready_capability(m: Model, k: Capability, s: State) -> bool:
    return admissible(m, k, s)


def ready_transition(m: Model, t: Transition, s: State) -> bool:
    return admissible_transition(m, t, s)


def risk_capability(m: Model, k: Capability, s: State) -> bool:
    return (
        any(
            (k, d) in m.requires and (d, s) not in m.satisfied
            for d in m.dependencies
        )
        or
        any(
            (k, q) in m.limited_by and (q, s) in m.active and (k, q, s) not in m.admissible_under
            for q in m.constraints
        )
        or
        any(
            (k, b) in m.crosses and (b, s) in m.friction_at
            for b in m.boundaries
        )
    )


def risk_transition(m: Model, t: Transition, s: State) -> bool:
    return (
        any(
            (t, d) in m.requires_for_transition and (d, s) not in m.satisfied
            for d in m.dependencies
        )
        or
        any(
            (t, q) in m.constrained_by_transition
            and (q, s) in m.active
            and (t, q, s) not in m.transition_admissible_under
            for q in m.constraints
        )
        or
        any(
            (t, b) in m.crosses_transition and (b, s) in m.friction_at
            for b in m.boundaries
        )
    )


def requires_coordination_capability(m: Model, k: Capability) -> bool:
    controllers = [a for a in m.actors if (a, k) in m.controls]
    return len(controllers) >= 2


def requires_coordination_transition(m: Model, t: Transition) -> bool:
    for k in m.changed_capabilities(t):
        controllers = [a for a in m.actors if (a, k) in m.controls]
        if len(controllers) >= 2:
            return True
    return False


def coexists(m: Model, k1: Capability, k2: Capability, s: State) -> bool:
    return (k1, s) in m.available and (k2, s) in m.available


def mixed_mode(m: Model, s: State) -> bool:
    return any(
        k1 != k2 and coexists(m, k1, k2, s)
        for k1 in m.capabilities
        for k2 in m.capabilities
    )


def boundary_friction(m: Model, b: Boundary, s: State) -> bool:
    return (b, s) in m.friction_at


# ============================================================================
# Semantic predicates from the theory
# ============================================================================

def valid_decision(m: Model, d: Decision, s: State) -> bool:
    """
    Theory-close computation of validity, aligned with the repaired core:
    - exactly one selected transition,
    - that transition is admissible from s,
    - every changed capability has at least one assigned actor.
    """
    t = m.selected_transition(d)
    if t is None:
        return False

    if not admissible_transition(m, t, s):
        return False

    for k in m.changed_capabilities(t):
        if not any(True for _ in m.assigned_actors(d, k)):
            return False

    return True


def executable_decision(m: Model, d: Decision, s: State) -> bool:
    """
    In the closed core, executability is stricter than validity but does not
    introduce extra undeclared machinery. We therefore require:
    - validity,
    - every assigned actor can decide the decision.
    """
    if not valid_decision(m, d, s):
        return False

    for a in m.actors:
        for k in m.capabilities:
            if (d, a, k) in m.assigns and (a, d) not in m.can_decide:
                return False

    return True


# ============================================================================
# Axiom checking
# ============================================================================

@dataclass(frozen=True, slots=True)
class Violation:
    axiom: str
    message: str
    witness: tuple[object, ...] = ()


def check_a1(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for d in m.decisions:
        selected = [t for t in m.transitions if (d, t) in m.selects]
        if len(selected) > 1:
            out.append(Violation("A1", "decision selects more than one transition", (d, *selected)))
    return out


def check_a2(m: Model) -> list[Violation]:
    return [
        Violation("A2", "operational capability is not available", (k, s))
        for (k, s) in m.operational
        if (k, s) not in m.available
    ]


def check_a3(m: Model) -> list[Violation]:
    return [
        Violation("A3", "executable decision is not marked valid", (d, s))
        for (d, s) in m.executable
        if (d, s) not in m.valid
    ]


def check_a4(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for (d, s) in m.valid:
        ok = any((d, t) in m.selects and m.source.get(t) == s for t in m.transitions)
        if not ok:
            out.append(Violation("A4", "valid decision has no selected transition sourced at evaluated state", (d, s)))
    return out


def check_a5(m: Model) -> list[Violation]:
    return [
        Violation("A5", "assigned actor cannot decide decision", (d, a, k))
        for (d, a, k) in m.assigns
        if (a, d) not in m.can_decide
    ]


def check_a6(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for (d, a, k) in m.assigns:
        ok = any((d, t) in m.selects and (t, k) in m.changes for t in m.transitions)
        if not ok:
            out.append(Violation("A6", "assignment is not to a changed capability of selected transition", (d, a, k)))
    return out


def check_a7(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for (d, s) in m.valid:
        ok = any((d, t) in m.selects and admissible_transition(m, t, s) for t in m.transitions)
        if not ok:
            out.append(Violation("A7", "valid decision selects no admissible transition from state", (d, s)))
    return out


def check_a8(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for (d, s) in m.executable:
        for t in m.transitions:
            if (d, t) in m.selects and not admissible_transition(m, t, s):
                out.append(Violation("A8", "executable decision selects non-admissible transition", (d, s, t)))
    return out


def check_a9(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for (d, s) in m.valid:
        for t in m.transitions:
            if (d, t) not in m.selects:
                continue
            for k in m.changed_capabilities(t):
                if not any((d, a, k) in m.assigns for a in m.actors):
                    out.append(Violation("A9", "changed capability has no assigned actor", (d, s, t, k)))
    return out


def check_a10(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for (d, s) in m.executable:
        if (d, s) not in m.valid:
            out.append(Violation("A10", "executable decision is not marked valid", (d, s)))
        for a in m.actors:
            for k in m.capabilities:
                if (d, a, k) in m.assigns and (a, d) not in m.can_decide:
                    out.append(Violation("A10", "assigned actor lacks decision capability", (d, s, a, k)))
    return out


def check_a11(m: Model) -> list[Violation]:
    return [
        Violation("A11", "reachability is not reflexive on state", (s,))
        for s in m.states
        if (s, s) not in m.reachable
    ]


def check_a12(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for t in m.transitions:
        for s in m.states:
            if admissible_transition(m, t, s):
                tgt = m.target.get(t)
                if tgt is None or (s, tgt) not in m.reachable:
                    out.append(Violation("A12", "one-step admissible transition missing from reachability", (t, s, tgt)))
    return out


def check_a13(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for s1 in m.states:
        for s2 in m.states:
            for s3 in m.states:
                if (s1, s2) in m.reachable and (s2, s3) in m.reachable and (s1, s3) not in m.reachable:
                    out.append(Violation("A13", "reachability is not transitive", (s1, s2, s3)))
    return out


AXIOM_CHECKS = (
    check_a1,
    check_a2,
    check_a3,
    check_a4,
    check_a5,
    check_a6,
    check_a7,
    check_a8,
    check_a9,
    check_a10,
    check_a11,
    check_a12,
    check_a13,
)


def check_axioms(m: Model) -> list[Violation]:
    out: list[Violation] = []
    for check in AXIOM_CHECKS:
        out.extend(check(m))
    return out


# ============================================================================
# Useful queries
# ============================================================================

def admissible_capabilities(m: Model, s: State) -> list[Capability]:
    return [k for k in m.capabilities if admissible(m, k, s)]


def admissible_transitions(m: Model, s: State) -> list[Transition]:
    return [t for t in m.transitions if admissible_transition(m, t, s)]


def valid_decisions(m: Model, s: State) -> list[Decision]:
    return [d for d in m.decisions if valid_decision(m, d, s)]


def executable_decisions(m: Model, s: State) -> list[Decision]:
    return [d for d in m.decisions if executable_decision(m, d, s)]


# ============================================================================
# Reachability closure utility
# ============================================================================

def least_reachable_closure(m: Model) -> FrozenSet[SS]:
    """
    Computes the least reflexive-transitive relation containing all
    one-step admissible transitions under the current model.
    This is operationally useful, even though the core theory axiomatizes
    reachable rather than defining it as least closure.
    """
    rel: set[SS] = {(s, s) for s in m.states}

    for t in m.transitions:
        for s in m.states:
            if admissible_transition(m, t, s):
                tgt = m.target.get(t)
                if tgt is not None:
                    rel.add((s, tgt))

    changed = True
    while changed:
        changed = False
        new_pairs: set[SS] = set()
        for (s1, s2) in rel:
            for (u1, u2) in rel:
                if s2 == u1 and (s1, u2) not in rel:
                    new_pairs.add((s1, u2))
        if new_pairs:
            rel |= new_pairs
            changed = True

    return frozenset(rel)


# ============================================================================
# Tiny example
# ============================================================================

if __name__ == "__main__":
    a1 = Actor("operator")
    a2 = Actor("regulator")

    o1 = Objective("continuity")

    k_old = Capability("legacy")
    k_new = Capability("unified")

    d1 = Dependency("certified")
    q1 = Constraint("no_mixed_mode")
    b1 = Boundary("regulatory")

    s0 = State("legacy_state")
    s1 = State("target_state")

    t1 = Transition("migrate")
    dec1 = Decision("select_migrate")
    tm1 = TimePoint("2026-04-14T10:00:00Z")

    m = Model(
        actors=frozenset({a1, a2}),
        objectives=frozenset({o1}),
        capabilities=frozenset({k_old, k_new}),
        dependencies=frozenset({d1}),
        constraints=frozenset({q1}),
        boundaries=frozenset({b1}),
        states=frozenset({s0, s1}),
        transitions=frozenset({t1}),
        decisions=frozenset({dec1}),
        times=frozenset({tm1}),

        controls=frozenset({(a1, k_new)}),
        can_decide=frozenset({(a1, dec1)}),

        advances=frozenset({(k_new, o1)}),
        requires=frozenset({(k_new, d1)}),
        limited_by=frozenset({(k_new, q1)}),
        available=frozenset({(k_old, s0), (k_new, s1)}),
        operational=frozenset({(k_old, s0)}),

        satisfied=frozenset({(d1, s0)}),

        active=frozenset({(q1, s0)}),
        admissible_under=frozenset({(k_new, q1, s0)}),

        current=frozenset({s0}),
        target_state=frozenset({s1}),

        changes=frozenset({(t1, k_new)}),
        requires_for_transition=frozenset({(t1, d1)}),
        constrained_by_transition=frozenset({(t1, q1)}),
        transition_admissible_under=frozenset({(t1, q1, s0)}),

        selects=frozenset({(dec1, t1)}),
        assigns=frozenset({(dec1, a1, k_new)}),
        at_time=frozenset({(dec1, tm1)}),
        valid=frozenset({(dec1, s0)}),
        executable=frozenset({(dec1, s0)}),

        source={t1: s0},
        target={t1: s1},
    )

    # Operational closure for convenience
    m.reachable = least_reachable_closure(m)

    print("Admissible capabilities at s0:", [k.name for k in admissible_capabilities(m, s0)])
    print("Admissible transitions at s0:", [t.name for t in admissible_transitions(m, s0)])
    print("Valid decisions at s0:", [d.name for d in valid_decisions(m, s0)])
    print("Executable decisions at s0:", [d.name for d in executable_decisions(m, s0)])

    violations = check_axioms(m)
    print("Axiom violations:", len(violations))
    for v in violations:
        print(v.axiom, "-", v.message, v.witness)

```
