# Resumption

*State, non-achievedness, and governed continuity across reductions*

## Abstract

Resumption is the initiation of a new reduction from an explicitly persisted
and governed account of what is currently achieved and what remains
non-achieved. It is not transcript replay, continuation of hidden model state,
or restoration of transient reasoning.

A reduction can be resumed correctly only when the boundary between reductions
preserves the semantic state required by the next reduction. That state must be
distinguished from the conversation history, the path by which the state was
reached, and the prose through which a result was presented.

This note extends the canonical treatment of non-achievedness and governed
reduction in [Theory](THEORY.md). It does not redefine artifact authority,
retention, forgetting, or execution. Those concerns remain related constraints,
but they are not additional principles of resumption.

The explanatory companion, [Resumption Expanded](RESUMPTION_EXPANDED.md),
develops these distinctions through a worked scenario.

## 1. The object of resumption

The object being resumed is not a transcript and not a model session. It is a
governed realization state relative to an objective:

```text
current achieved state
+ current non-achievedness
+ supporting provenance
+ causal identity
```

Resumption begins another reduction from that state. The new reduction may
preserve it, refine it, supersede part of it, create additional
non-achievedness, or branch from it.

The central distinction is:

```text
history records what occurred
path records how state changed
state records what currently holds
non-achievedness records what remains unresolved
```

Only the latter two directly govern the ordinary next reduction. History and
path remain available when explanation, verification, reversal, or
reconstruction requires them.

## 2. Interruption, augmentation, redirection, and realignment

These concepts distinguish a break in reduction activity, an addition to its
semantic basis, a change in its intended direction, and the reconciliation
required by that change.

### 2.1 Interruption

An interruption is an event that stops an active reduction before its current
non-achievedness has reached its intended disposition. It changes whether the
reduction is proceeding, but does not by itself change its direction, current
achieved state, or current non-achievedness.

Semantic continuity requires the state at the interruption boundary to remain
distinguishable from work that was unfinished or merely proposed when the
interruption occurred.

### 2.2 Augmentation

An augmentation is an inlet that adds semantic material to an existing
reduction without, by definition, withdrawing, replacing, or invalidating
existing material.

An augmentation may have consequences that require further reconciliation. It
may introduce new non-achievedness, expose contradiction, or affect what can be
justifiably achieved. Those consequences are distinct from the augmentation
itself.

### 2.3 Redirection

A redirection is an inlet or governed decision that changes the intended
direction of a reduction. It may change the objective, scope, constraints, or
required outcome governing what the reduction is now directed toward.

Redirection names the change in intended direction. It does not itself describe
how existing state is reconciled with that change.

### 2.4 Realignment

Realignment is the governed reconciliation of current achieved state and
current non-achievedness with a redirection. It determines:

- what remains applicable and is retained;
- what no longer applies and is superseded in active state;
- what new material is introduced;
- and what remains unresolved.

Material displaced by realignment is not erased. It remains available in the
reduction path, history, and provenance. If the required realignment is
ambiguous, that ambiguity remains non-achievedness rather than being resolved
implicitly.

The distinction is therefore:

```text
interruption changes whether reduction is proceeding
augmentation adds to the semantic basis
redirection changes the intended direction
realignment reconciles the semantic basis with that new direction
```

## 3. Governing principles

### 3.1 Conversation history is not non-achievedness

History records what occurred. Non-achievedness represents what remains
unresolved relative to the current objective. History may provide evidence for
determining non-achievedness, but it is not itself the unresolved state.

### 3.2 The reduction path is not the current state

The path records how facts were established, transformed, superseded, or
rejected. Resumption proceeds from the resulting current state and its remaining
non-achievedness. The path is consulted when that state must be explained,
verified, reversed, or reconstructed.

### 3.3 Resumption is a new reduction from a persisted state projection

The projection contains the currently valid achieved facts, unresolved
non-achievedness, and references to supporting provenance. Continuity comes
from this explicit state rather than transcript replay or hidden model memory.

### 3.4 Corrections require explicit supersession

A corrected artifact replaces the earlier artifact in active state. The
earlier artifact remains in provenance but does not participate as a current
fact unless it is explicitly restored.

### 3.5 Resumption context is deliberately projected and bounded

Only state relevant to the current objective and unresolved requirements should
be supplied. Retrieval or model judgment may help identify relevant candidates,
but artifact validity, admissibility, and supersession remain mechanically
governed. The projection must itself be inspectable rather than disappearing
inside prompt assembly.

### 3.6 Model state is not conversational state

Every reduction must be reconstructible from persisted artifacts and its
explicit projection. Provider sessions and caches may improve performance, but
correctness must remain unchanged if they disappear, restart, or are replaced
by another model.

### 3.7 A generated response is not automatically achieved state

A generated response is a proposal produced by a reduction step. Only a
validated and admitted result may update persisted current state or discharge
non-achievedness.

### 3.8 Presentation is not state

A chat answer is a rendered view of a reduction result. Future reductions
consume the admitted structured artifacts behind that answer, not reparsed
prose from the answer itself.

### 3.9 Each user turn is an inlet that may change problem state

A new inlet can add facts, create non-achievedness, refine an objective, or
supersede prior state. It must be reconciled with current state rather than
merely appended to a transcript.

### 3.10 Turn completion and objective achievement are different

The system may produce a valid reply while the larger objective remains
non-achieved. Resumption preserves unresolved obligations rather than treating
every answered turn as closure.

### 3.11 Every accepted state transition requires provenance

The system retains what caused the change, which artifacts supported it, what
it superseded, and the reduction receipt that admitted it. Resumption uses the
resulting state while preserving this trace for audit and reconstruction.

### 3.12 Ambiguity and unresolved contradiction remain non-achievedness

The system must not silently choose between competing valid interpretations. It
preserves the conflict and seeks evidence, verification, or clarification
before updating current state.

### 3.13 Retrieval is attention, not verification

Similarity search or model judgment may nominate artifacts for consideration,
but cannot establish their truth, validity, authority, or applicability. Those
remain governed by explicit artifact relationships and verification.

### 3.14 Reduction guarantees are not automatically compositional

Guarantees that hold within one reduction do not automatically survive loosely
chained reductions. Passing prose or partial context can lose governed state,
non-achievedness, supersession, provenance, and verification relationships.
Chained reductions preserve correctness only through an explicit
inter-reduction state contract.

### 3.15 Resumption is causally anchored

A new reduction identifies the exact state revision from which it continues. If
that state has changed meanwhile, the system reconciles or rejects the stale
continuation rather than silently overwriting newer state.

### 3.16 Resumption need not be linear

Multiple reductions may validly continue from the same state revision. They are
represented as explicit branches and later selected, merged, or abandoned
rather than collapsed into one assumed conversation history.

### 3.17 Resumption requires explicit identity

A continuation is bound to its subject, objective, state revision, and branch.
Semantic similarity alone must not decide which prior reduction a new inlet
continues.

### 3.18 Interruption is not a semantic state transition

An interruption stops an active reduction but does not itself augment,
redirect, realign, supersede, or discharge anything. Accepted state remains
current, while unfinished or proposed work remains distinguishable in the path
and provenance unless separately accepted through a later transition.

### 3.19 Augmentation is additive

An augmentation adds semantic material. It does not itself withdraw, replace,
invalidate, or redirect existing material. Any resulting conflict or need for
change must be represented separately.

### 3.20 Redirection prevents unchanged continuation

Once redirection is established, reduction cannot continue as though the
previous direction still governed it. Current achieved state and current
non-achievedness must first be reconciled with the new direction.

### 3.21 Realignment preserves uncertainty about applicability

The effect of a redirection on existing material must be established from
available relationships and evidence. Material whose applicability remains
uncertain is neither silently retained nor superseded; that uncertainty becomes
non-achievedness.

## 4. The inter-reduction boundary

The theory does not prescribe one storage schema or transport format. It does
require the boundary between reductions to preserve, in explicit form:

- the subject and objective being continued;
- the causal state revision and branch;
- currently admitted achieved state;
- current non-achievedness;
- supersession and contradiction status;
- references to supporting provenance;
- and enough governance metadata to interpret those artifacts correctly.

This is a semantic contract, not a requirement to serialize private reasoning.
Transient model deliberation is neither necessary nor sufficient for
resumption.

## 5. Consequences

A resumption design is unsound when it relies only on any of the following:

- replaying an entire transcript;
- passing the previous answer as prose;
- retaining a provider session;
- selecting a prior conversation by semantic similarity alone;
- treating every completed turn as an achieved objective;
- or chaining locally correct reductions without preserving their governed
  state relationships.

A sound design may still use transcripts, retrieval, models, and caches. Their
role is subordinate: they help reconstruct or attend to an explicit governed
state, but they do not constitute that state.
