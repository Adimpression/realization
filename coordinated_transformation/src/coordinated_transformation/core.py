from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Iterator, Generic, TypeVar


__all__ = [
    "A2",
    "ADec",
    "AK",
    "AO",
    "AXIOM_CHECKS",
    "Actor",
    "BAA",
    "BKK",
    "BS",
    "BSS",
    "Boundary",
    "CB",
    "CD",
    "CO",
    "CQ",
    "CQS",
    "CS",
    "Capability",
    "Constraint",
    "DAK",
    "DS",
    "DS_validity",
    "DT",
    "DTime",
    "Decision",
    "Dependency",
    "Model",
    "Objective",
    "QS",
    "SS",
    "State",
    "TB",
    "TD",
    "TK",
    "TQ",
    "TQS",
    "TimePoint",
    "Transition",
    "TransitionPath",
    "Violation",
    "admissible",
    "admissible_capabilities",
    "admissible_transition",
    "admissible_transition_paths",
    "admissible_transitions",
    "boundary_friction",
    "check_a1",
    "check_a10",
    "check_a11",
    "check_a12",
    "check_a13",
    "check_a2",
    "check_a3",
    "check_a4",
    "check_a5",
    "check_a6",
    "check_a7",
    "check_a8",
    "check_a9",
    "check_axioms",
    "coexists",
    "executable_decision",
    "executable_decisions",
    "least_reachable_closure",
    "mixed_mode",
    "ready_capability",
    "ready_transition",
    "requires_coordination_capability",
    "requires_coordination_transition",
    "risk_capability",
    "risk_transition",
    "valid_decision",
    "valid_decisions",
]


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


@dataclass(frozen=True, slots=True)
class TransitionPath:
    start: State
    transitions: tuple[Transition, ...]
    states: tuple[State, ...]


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

def admissible_transition_paths(
    m: Model,
    *,
    start_states: Iterable[State] | None = None,
    target_states: Iterable[State] | None = None,
    max_depth: int | None = None,
) -> tuple[TransitionPath, ...]:
    starts = tuple(
        sorted(
            set(start_states if start_states is not None else m.current),
            key=lambda item: item.name,
        )
    )
    targets = frozenset(target_states if target_states is not None else m.target_state)
    if not starts:
        return ()
    max_path_depth = max(1, int(max_depth or len(m.transitions) or 1))
    resolved_paths: list[TransitionPath] = []
    seen: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()

    def walk(
        current_state: State,
        *,
        start_state: State,
        transition_path: tuple[Transition, ...],
        state_path: tuple[State, ...],
    ) -> None:
        if transition_path and (not targets or current_state in targets):
            key = (
                start_state.name,
                tuple(item.name for item in transition_path),
                tuple(item.name for item in state_path),
            )
            if key not in seen:
                seen.add(key)
                resolved_paths.append(
                    TransitionPath(
                        start=start_state,
                        transitions=transition_path,
                        states=state_path,
                    )
                )
        if len(transition_path) >= max_path_depth:
            return
        for transition in sorted(admissible_transitions(m, current_state), key=lambda item: item.name):
            next_state = m.target.get(transition)
            if next_state is None or next_state in state_path:
                continue
            walk(
                next_state,
                start_state=start_state,
                transition_path=(*transition_path, transition),
                state_path=(*state_path, next_state),
            )

    for start_state in starts:
        walk(
            start_state,
            start_state=start_state,
            transition_path=(),
            state_path=(start_state,),
        )
    return tuple(
        sorted(
            resolved_paths,
            key=lambda item: (
                len(item.transitions),
                item.start.name,
                tuple(transition.name for transition in item.transitions),
                tuple(state.name for state in item.states),
            ),
        )
    )

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
