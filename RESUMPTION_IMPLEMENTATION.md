# Resumption Implementation Design

## Status And Source Of Authority

This is a normative implementation design derived from:

- [Resumption](RESUMPTION.md)
- [Resumption Expanded](RESUMPTION_EXPANDED.md)
- [Theory](THEORY.md)
- [Intelligence](INTELLIGENCE.md)
- [Artifact-Mediated Verification](ARTIFACT_MEDIATED_VERIFICATION.md)
- [Event Bus](EVENT_BUS.md)
- [Open Governance](OPEN_GOVERNANCE.md)
- [Six-Layer Architecture](6-LAYER_ARCHITECTURE.md)

It is not a description of the implementation present when this document was
written. In particular, implementation changes made on 22 October 2026 are
deliberately excluded as design input. Same-day run, resume, governed-turn, or
performance experiments must not become a circular compatibility baseline.

Established implementation can be examined only after the theory-derived
design is complete, to identify conformance and migration gaps. It cannot
override the theory or redefine the architectural boundaries.

The theory remains authoritative over this document. Architectural placement
must preserve the theory rather than reinterpret it around convenient
implementation details.

## Design Objective

Resumption initiates a new governed reduction from an exact, persisted account
of:

```text
current achieved state
+ current non-achievedness
+ supporting provenance
+ causal identity
```

The object resumed is a governed realization state relative to an objective. It
is not:

- a transcript;
- a previous natural-language answer;
- hidden model state;
- a provider session;
- a prompt cache;
- a stack frame;
- or an unqualified request to retry prior work.

The implementation must make a resumed reduction correct even when every model
session, process, cache, and presentation surface from the earlier reduction has
disappeared.

## Governing Invariants

1. History records what occurred.
2. Path records how state changed.
3. State records what currently holds.
4. Non-achievedness records what remains unresolved.
5. Ordinary resumption is governed directly by current state and current
   non-achievedness.
6. History and path remain available for explanation, verification, reversal,
   merge, and reconstruction.
7. Presentation is never authoritative continuation state.
8. A generated result is not state until it is verified and admitted.
9. A correction changes active state only through explicit supersession.
10. Ambiguity and contradiction remain non-achievedness until resolved.
11. Retrieval nominates candidates but does not establish identity, validity,
    authority, or applicability.
12. Every continuation is anchored to an exact causal revision.
13. Concurrent continuations branch rather than silently overwrite one another.
14. A completed conversational turn does not imply an achieved objective.
15. Every accepted transition has provenance and an inspectable receipt.
16. A notification mechanism cannot be the source of truth.
17. Authority and host capabilities are reevaluated at continuation time.
18. Guarantees within one reduction cross into another only through an explicit
    inter-reduction contract.

## Semantic Identity

A resumable state is identified by:

```text
ResumptionIdentity =
    ScopeIdentity
  x ObjectiveIdentity
  x BranchIdentity
  x RevisionIdentity
```

### Scope Identity

The scope identifies the semantic world within which the objective is valid. A
scope may correspond to a subject, bounded workspace, imported semantic domain,
or another governed context. The controller consumes a stable scope reference;
it does not infer scope from conversational similarity.

### Objective Identity

The objective identifies the continuing governed realization, independently of
how many reductions, user turns, pauses, or model invocations have occurred.

### Branch Identity

The branch identifies one explicit line of state development. Branch identity
prevents two valid continuations from one revision from being collapsed into an
accidental linear history.

### Revision Identity

The revision identifies the exact immutable state from which the new reduction
continues. It is bound to a canonical state digest. A locator, filename, run ID,
or message ID is not a revision identity unless it resolves to and verifies this
record.

### Non-Causal Identities

Session, turn, message, process, provider, and execution-attempt identifiers are
provenance. They can explain how an inlet arrived but cannot establish which
state it continues.

## Durable Semantic State

A durable state revision contains the semantic material that can affect later
realization:

- objective and scope identity;
- current achieved assertions and artifacts;
- current non-achievedness;
- the governed refinement graph;
- active duties and obligations;
- certainty and closure state;
- blockers, conflicts, and unknowns;
- admitted evidence and support relationships;
- current commitments;
- supersession and contradiction relationships;
- active `HoldOn` conditions;
- relevant capability and ability declarations;
- subject or scope imports and version pins;
- provenance references;
- governance references needed to interpret the state;
- and the parent revision relationship.

Transient deliberation, native handles, provider sessions, and presentation text
are not part of durable semantic state.

## Revision Model

A revision is an immutable admitted state:

```text
Revision = <identity, parents, state, provenance, governance, digest>
```

Every revision has zero, one, or multiple parents:

- zero parents for an initial objective;
- one parent for ordinary continuation, correction, or branch development;
- multiple parents for an explicit governed merge.

Mutable branch heads point to immutable revisions. Updating a branch head does
not mutate the revision it previously referenced.

A revision is created only after the proposed state transition has been
verified and admitted. Failed, rejected, expired, or ambiguous attempts produce
receipts but do not masquerade as committed revisions.

## Resumption Projection

The next reduction does not consume all durable material indiscriminately. It
consumes a deterministic and inspectable projection of the anchored revision.

```text
Projection = Project(Revision, Objective, ProjectionPolicy)
```

The projection contains:

- all currently valid achieved state relevant to the objective;
- every live non-achievedness relevant to the objective;
- active refinement relationships needed to interpret that non-achievedness;
- blockers, conflicts, certainty, and commitments;
- active `HoldOn` records;
- supersession status;
- supporting provenance references;
- applicable governance and scope references;
- and explicit references to relevant material held outside the inline
  projection.

The projection must satisfy:

- deterministic construction;
- canonical serialization;
- schema and policy versioning;
- content digesting;
- inspectability;
- live-obligation completeness;
- and bounded representation without silent semantic loss.

Boundedness is achieved through stable references, not by silently dropping
live obligations. If a projection cannot represent all material inline, its
completeness record declares what is referenced and why.

The full reduction path is added only when the operation requires explanation,
verification, reversal, correction, merge, or reconstruction.

## Continuation Inlet

Every new contribution crosses the inter-reduction boundary as an explicit
inlet:

```text
ContinuationInlet =
  <identity,
   kind,
   payload,
   target,
   relationship,
   source,
   provenance,
   correlation,
   authority context>
```

The original representation of the contribution is retained for provenance.
Structured interpretation is recorded separately.

An inlet can propose:

- a new fact;
- new evidence;
- refinement of an objective;
- new non-achievedness;
- satisfaction of a waiting condition;
- contradiction of current state;
- supersession of current state;
- branch creation;
- or merge reconciliation.

An inlet does not become current state by arrival alone.

## Resumption Operations

### Start

Start creates a new objective and initial branch with no causal parent revision.
It is not resumption.

### Resume Suspended Objective

This operation continues the same objective and branch from a suspended
revision. It requires an inlet that addresses an active `HoldOn` and satisfies
its governed resume predicate.

The new invocation is operationally distinct, while the semantic thread remains
continuous.

### Continue Objective

This operation begins a new reduction from the current state of the same
objective. It may preserve state, add non-achievedness, or refine existing
non-achievedness.

### Derive Objective

This operation creates a new objective whose inlet explicitly references
selected admitted state from another objective. The source objective is
provenance and support, not silently inherited ambient context.

### Correct State

This operation proposes replacement of explicitly identified current state. If
admitted, the replacement becomes current and the earlier state remains in the
path and provenance as superseded.

### Branch

This operation creates a new branch from an exact revision. It preserves the
parent state while allowing an independent continuation.

### Merge

This operation reconciles two or more explicit branch revisions. Conflicts
remain represented until resolved. A merge result is a new multi-parent
revision, not an overwrite of either input branch.

### Explain, Verify, Reverse, And Reconstruct

These operations consult path and history in addition to current state. A
reversal is represented as a new governed transition; it does not erase the
transition being reversed.

## HoldOn

`HoldOn` is represented as the complete durable continuation object:

```text
H = <n, c, r, f, tau, kappa, mu, sigma, pi>
```

where:

- `n` is the unresolved semantic object;
- `c` is the continuation carrier;
- `r` is the resume predicate;
- `f` is the failure or expiry predicate;
- `tau` is temporal policy;
- `kappa` is correlation structure;
- `mu` is multiplicity structure;
- `sigma` is scope;
- `pi` is provenance and governance.

The continuation carrier preserves enough information to resume the same
semantic thread without restoring a process stack or model session.

Supported condition families include:

- correlated message arrival;
- correlated signal arrival;
- timer or temporal boundary;
- external completion;
- state convergence;
- approval or authority decision.

Every evaluation yields one explicit disposition:

- remain held;
- resume;
- expire;
- fail;
- escalate;
- reframe.

Only the non-achievedness made eligible by the satisfied condition enters the
new active frontier. Unrelated suspended state remains suspended.

## Inlet Reconciliation

Reconciliation compares the inlet with the anchored projection and produces a
candidate transition. It does not mutate committed state.

Reconciliation determines whether the inlet:

- supports current state;
- adds compatible state;
- narrows non-achievedness;
- introduces new non-achievedness;
- contradicts current state;
- proposes supersession;
- satisfies a `HoldOn` condition;
- is irrelevant to the objective;
- is ambiguous;
- or refers to a stale or different causal identity.

If more than one interpretation remains materially plausible, reconciliation
emits ambiguity as non-achievedness or requests clarification. It does not
select an interpretation from transcript proximity.

## Correction And Supersession

A correction contains:

- one or more candidate target identities;
- the proposed replacement or invalidation;
- its intended scope;
- its source and provenance;
- and the evidence or authority supporting the change.

Admission creates an explicit supersession edge:

```text
new_state --supersedes--> prior_state
```

The prior state remains queryable in history and provenance but is excluded
from ordinary current-state projection. Restoring prior state requires another
explicit transition.

Contradiction alone does not imply supersession. Unresolved contradictory state
remains visible as conflict and non-achievedness.

## Concurrency And Staleness

Every mutating operation supplies an expected branch-head revision. Commit uses
an atomic compare-and-swap:

```text
commit(candidate) only if branch_head == expected_revision
```

If the branch head changed, the attempt produces a stale-anchor result. The
caller may then request:

- inspection of the new head;
- explicit reconciliation;
- creation of a branch from the original revision;
- or abandonment of the attempt.

The system never applies last-write-wins silently.

## Transition Admission

The reconciled candidate transition is admitted only after governance evaluates:

- causal identity and revision integrity;
- scope and lifecycle;
- evidence and provenance;
- supersession validity;
- contradiction and ambiguity;
- active `HoldOn` constraints;
- freshness requirements;
- policy and approval state;
- current capability availability;
- and requested authority.

Admission can accept, reject, narrow, hold, or require clarification. An LLM
assessment can be evidence for this evaluation but cannot perform admission.

## Reduction Execution

After admission of the inlet relationship, the controller constructs the active
reduction state from the projection and candidate transition.

The runtime receives an already prepared frontier. It advances the governed
reduction until one of the following occurs:

- achieved closure;
- governed suspension;
- explicit incompletion;
- failure;
- or resource-bound exhaustion.

The runtime does not decide which historical conversation is relevant, which
revision is causal, whether a correction supersedes state, or whether a waiting
condition has been satisfied.

## Artifact-Mediated Transition Verification

Every attempted transition emits an inspectable transition artifact containing:

- source identity and revision digest;
- projection policy, projection digest, and completeness statement;
- inlet identity and digest;
- reconciliation result;
- proposal references;
- governance and verification decisions;
- admitted, rejected, superseded, conflicting, and unresolved deltas;
- `HoldOn` evaluation and disposition;
- capability and effect receipt references;
- execution outcome;
- resulting revision identity and digest, when committed;
- and a decision-flow signature.

The transition artifact is verified independently of the generator that
proposed the transition. A successful verification does not imply that internal
model reasoning was faithfully reported; it establishes that the externalized
transition satisfies the governed checks.

## LLM Role

An LLM may:

- propose structured interpretations of an inlet;
- nominate possible correction targets;
- rank already eligible state or artifacts for attention;
- propose clarification questions;
- propose refinement, reflection, or contemplation artifacts;
- and render admitted results for presentation.

An LLM may not:

- choose causal identity by semantic resemblance;
- turn transcript text into state without admission;
- establish that a `HoldOn` predicate is satisfied merely by assertion;
- grant authority;
- select an undeclared host realizer;
- admit a transition;
- or make its hidden state part of the correctness boundary.

Resumption remains valid with LLM operation disabled. Where interpretation
cannot be completed mechanically, unresolved interpretation remains
non-achievedness.

## Retrieval And Attention

Retrieval operates over admitted artifacts and state references. Exact,
structural, full-text, vector, or model-assisted retrieval may nominate relevant
candidates.

Retrieval does not establish:

- which objective is being continued;
- whether an artifact is true;
- whether an artifact remains admissible;
- whether a correction is valid;
- whether authority exists;
- or whether a transition may commit.

Those relationships are mechanically established through identity, explicit
links, verification, and governance.

## Capability And Authority Rebinding

A persisted state may reference:

- required capability declarations;
- admitted abilities;
- exact executor or broker identities;
- previous invocation receipts;
- and historical authority decisions.

It does not persist live native handles or ambient authority. On each new
reduction:

1. the host advertises current realizers;
2. the runtime mechanically checks the declared realizer identity;
3. governance reevaluates lifecycle, policy, and approval;
4. invocation-scoped authority is issued when permitted;
5. effects execute through host mediation;
6. results and effect receipts return to the controller.

Historical grants remain provenance and are never treated as reusable live
authority.

## Persistence Contract

Persistence is defined by behavior rather than one storage technology.

The revision repository must support:

- immutable revision append;
- lookup by complete resumption identity;
- parent and child traversal;
- branch-head lookup;
- atomic compare-and-swap branch-head update;
- transition-artifact append;
- provenance and supersession traversal;
- deterministic state and projection digest verification;
- and reconstruction without model-provider state.

The repository commits the new revision, transition artifact, and branch-head
change atomically. A partial commit is not visible as a valid continuation.

Derived indexes, caches, search vectors, and materialized views are rebuildable.
They are not canonical state.

## Event Delivery

Events are emitted only after authoritative commit. An event identifies the
committed revision and allows subscribers to reread their projections.

Correctness must survive:

- delayed delivery;
- duplicate delivery;
- out-of-order delivery;
- subscriber failure;
- and complete event loss followed by state reread.

The event bus never carries the sole copy of state or establishes transition
ordering independently of committed revisions.

## Active Context Assembly

The active context for a reduction is assembled from:

- the resumption projection;
- the admitted inlet relationship;
- retrieved candidate artifacts kept distinct from admitted state;
- currently available capabilities;
- and the execution policy for the reduction.

Conversation history can be consulted as provenance or evidence only when
explicitly selected and admitted. It is not automatically re-fed.

The path taken so far is included only when required by the operation. Ordinary
continuation does not require replay of the path once its admitted result is
represented in current state.

## Cache Semantics

Caching is optional and cannot affect correctness.

A reusable proposal cache key includes at least:

- exact projection digest;
- inlet digest;
- operation kind;
- proposal schema and prompt version;
- model and provider identity;
- and relevant governance posture.

A cache hit yields a prior proposal for reevaluation. It never yields an
already admitted transition merely because the proposal was admitted under a
different revision.

## Layer Responsibilities

### Runtime And Skill Execution

- Advance an already prepared active reduction.
- Execute mechanically bound host realizers under current authority.
- Return effect results and receipts.
- Own no transcript, causal routing, revision selection, or state admission.

### Controller

- Own resumption identity semantics.
- Construct projections.
- Reconcile inlets with current state.
- Govern active non-achievedness and reduction flow.
- Represent correction, supersession, branching, and merge semantics.
- Prepare the frontier supplied to the runtime.

### Governance

- Evaluate admission, policy, lifecycle, approval, revocation, freshness, and
  current-use authority.
- Record decisions in transition artifacts.

### LLM

- Produce advisory interpretations and proposals.
- Own no state, authority, admission, or causal identity.

### Workstation Or Other Conversation Host

- Own sessions, transcripts, user interaction, and presentation.
- Let the user select or confirm a causal objective when necessary.
- Submit explicit identities and inlets through the application contract.
- Render structured outcomes without converting rendered prose back into state.

### Entry And Exchange

- Compose repository, governance, controller, runtime, model, and host
  implementations.
- Expose ingress, export, inspection, and administrative surfaces.

### Shared Host Interaction Substrate

- Resolve current host realizers, attachments, capabilities, delegated rights,
  and effect receipts.
- Remain below both controller and workstation without absorbing either one's
  responsibilities.

## Application Contract

The application boundary exposes semantic operations rather than transcript
continuation commands.

### Start Request

- new scope and objective identity;
- initial inlet;
- governance and execution policy.

### Resumption Request

- complete causal anchor;
- operation kind;
- continuation inlet;
- expected branch head;
- projection policy;
- governance and execution policy.

### Resumption Result

- source revision identity;
- outcome;
- resulting revision identity when committed;
- transition-artifact reference;
- current achieved-state summary;
- current non-achievedness summary;
- active `HoldOn` summary;
- conflict, rejection, or stale-anchor information;
- presentation-ready view kept separate from state.

### Inspection Request

- exact revision or branch-head identity;
- requested view: current state, non-achievedness, path, provenance, transition,
  branch graph, or reconstruction data.

The transport may be an in-process interface, command line, RPC, or another
mechanism. Transport does not alter semantics.

## Outcome Model

An invocation concludes with one explicit outcome:

- `completed`: the active objective is achieved under governance;
- `paused`: a durable `HoldOn` governs continuation;
- `incomplete`: unresolved state remains without a current continuation path;
- `rejected`: the proposed transition was inadmissible;
- `ambiguous`: clarification is required before state can change;
- `conflicted`: unresolved contradictory state blocks commitment;
- `stale`: the causal anchor is no longer the selected branch head;
- `expired`: the continuation condition expired;
- `failed`: execution or verification failed;
- `exhausted`: the bounded reduction ended without another semantic outcome.

A valid conversational response may accompany any outcome. The response does
not alter the outcome or imply objective closure.

## Determinism And Replay

Deterministic replay requires reconstruction of decision flow, not only the
final answer. The replay record includes:

- exact source revision;
- projection and inlet artifacts;
- frontier selections;
- retrieved candidate sets and ordering;
- proposal request and response receipts;
- governance and admission decisions;
- `HoldOn` decisions;
- capability and effect receipts;
- pause, failure, and commitment decisions;
- and the resulting revision digest.

LLM-off execution can be intrinsically deterministic when all other inputs are
fixed. LLM-enabled execution is replayable only through recorded proposal
interactions or an explicitly qualified deterministic provider contract.

## Security And Privacy

The projection includes only material permitted for the continuing scope and
principal. Provenance references do not bypass access control.

Sensitive material can remain behind governed references when inline projection
would violate policy. The completeness record declares the reference without
revealing unauthorized content.

Inspection, explanation, branch traversal, and replay each perform their own
authorization checks.

## Performance Model

Performance is improved by reducing irrelevant active context, not by weakening
state continuity.

The implementation measures independently:

- revision load latency;
- projection construction latency;
- projection size;
- candidate retrieval latency;
- proposal latency;
- verification and admission latency;
- reduction latency;
- effect latency;
- and atomic commit latency.

Optimization may introduce indexes, snapshots, references, memoization, and
proposal caches. It may not silently remove active non-achievedness, provenance,
supersession, conflict, or governance context.

## Conformance Tests

A conforming implementation demonstrates at least these behaviors:

1. Provider restart or replacement does not lose continuation state.
2. Transcript wording changes do not alter state when admitted artifacts are
   unchanged.
3. Presentation changes do not change the revision digest.
4. Unresolved non-achievedness survives a completed conversational turn.
5. Superseded state remains in provenance and is absent from ordinary current
   projection.
6. An ambiguous correction does not guess a target.
7. A wrong correlation cannot satisfy a `HoldOn`.
8. A valid correlation reopens only the addressed continuation.
9. Expiry, failure, escalation, and reframe dispositions are durable.
10. A stale branch head prevents silent commit.
11. Concurrent child revisions remain separate branches.
12. A merge preserves parent identities and explicit conflicts.
13. Similarity cannot bind an inlet to a causal objective.
14. Revoked or expired authority is not restored.
15. Imported scope material retains source identity and version pins.
16. Event loss does not lose state.
17. Derived indexes can be rebuilt without semantic loss.
18. Deterministic replay reproduces the decision-flow signature.
19. LLM-enabled replay uses recorded proposal interactions.
20. Every committed transition has an independently inspectable artifact and
    revision digest.

## Non-Goals

This design does not:

- define conversation as transcript replay;
- make every conversation turn a resumption;
- require an LLM;
- serialize private model reasoning;
- use similarity as causal identity;
- make presentation text authoritative state;
- make the event bus a state store;
- persist native handles or ambient authority;
- prescribe one database technology or transport;
- erase history during correction;
- or impose a single linear continuation model.

## Completion Standard

An implementation conforms when every continuation can be reconstructed from
its explicit causal anchor, admitted state, current non-achievedness,
provenance, transition artifact, and resulting revision without relying on a
transcript, hidden model state, provider session, cache, process lifetime, or
ambient host authority.
