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

## 2. Governing principles

### 2.1 Conversation history is not non-achievedness

History records what occurred. Non-achievedness represents what remains
unresolved relative to the current objective. History may provide evidence for
determining non-achievedness, but it is not itself the unresolved state.

### 2.2 The reduction path is not the current state

The path records how facts were established, transformed, superseded, or
rejected. Resumption proceeds from the resulting current state and its remaining
non-achievedness. The path is consulted when that state must be explained,
verified, reversed, or reconstructed.

### 2.3 Resumption is a new reduction from a persisted state projection

The projection contains the currently valid achieved facts, unresolved
non-achievedness, and references to supporting provenance. Continuity comes
from this explicit state rather than transcript replay or hidden model memory.

### 2.4 Corrections require explicit supersession

A corrected artifact replaces the earlier artifact in active state. The
earlier artifact remains in provenance but does not participate as a current
fact unless it is explicitly restored.

### 2.5 Resumption context is deliberately projected and bounded

Only state relevant to the current objective and unresolved requirements should
be supplied. Retrieval or model judgment may help identify relevant candidates,
but artifact validity, admissibility, and supersession remain mechanically
governed. The projection must itself be inspectable rather than disappearing
inside prompt assembly.

### 2.6 Model state is not conversational state

Every reduction must be reconstructible from persisted artifacts and its
explicit projection. Provider sessions and caches may improve performance, but
correctness must remain unchanged if they disappear, restart, or are replaced
by another model.

### 2.7 A generated response is not automatically achieved state

A generated response is a proposal produced by a reduction step. Only a
validated and admitted result may update persisted current state or discharge
non-achievedness.

### 2.8 Presentation is not state

A chat answer is a rendered view of a reduction result. Future reductions
consume the admitted structured artifacts behind that answer, not reparsed
prose from the answer itself.

### 2.9 Each user turn is an inlet that may change problem state

A new inlet can add facts, create non-achievedness, refine an objective, or
supersede prior state. It must be reconciled with current state rather than
merely appended to a transcript.

### 2.10 Turn completion and objective achievement are different

The system may produce a valid reply while the larger objective remains
non-achieved. Resumption preserves unresolved obligations rather than treating
every answered turn as closure.

### 2.11 Every accepted state transition requires provenance

The system retains what caused the change, which artifacts supported it, what
it superseded, and the reduction receipt that admitted it. Resumption uses the
resulting state while preserving this trace for audit and reconstruction.

### 2.12 Ambiguity and unresolved contradiction remain non-achievedness

The system must not silently choose between competing valid interpretations. It
preserves the conflict and seeks evidence, verification, or clarification
before updating current state.

### 2.13 Retrieval is attention, not verification

Similarity search or model judgment may nominate artifacts for consideration,
but cannot establish their truth, validity, authority, or applicability. Those
remain governed by explicit artifact relationships and verification.

### 2.14 Reduction guarantees are not automatically compositional

Guarantees that hold within one reduction do not automatically survive loosely
chained reductions. Passing prose or partial context can lose governed state,
non-achievedness, supersession, provenance, and verification relationships.
Chained reductions preserve correctness only through an explicit
inter-reduction state contract.

### 2.15 Resumption is causally anchored

A new reduction identifies the exact state revision from which it continues. If
that state has changed meanwhile, the system reconciles or rejects the stale
continuation rather than silently overwriting newer state.

### 2.16 Resumption need not be linear

Multiple reductions may validly continue from the same state revision. They are
represented as explicit branches and later selected, merged, or abandoned
rather than collapsed into one assumed conversation history.

### 2.17 Resumption requires explicit identity

A continuation is bound to its subject, objective, state revision, and branch.
Semantic similarity alone must not decide which prior reduction a new inlet
continues.

## 3. The inter-reduction boundary

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

## 4. Consequences

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
