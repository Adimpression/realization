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
- [Module Ownership Map](MODULES.md)
- [Architecture Boundary Controls](architecture/README.md)

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

This design also covers four distinct events at the inter-reduction boundary:

- interruption, which stops active execution without itself changing semantic
  state;
- augmentation, which proposes additive semantic material;
- redirection, which establishes a changed intended direction;
- and realignment, which reconciles current state and non-achievedness with an
  established redirection.

These are not aliases for resumption. They constrain what a later resumption is
allowed to resume.

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
19. Interruption changes execution status, not achieved state,
    non-achievedness, direction, or branch identity.
20. Unfinished or merely proposed work at an interruption boundary is not
    promoted into current state.
21. Augmentation is additive and cannot silently withdraw, replace, invalidate,
    or redirect existing material.
22. Once redirection is established, unchanged continuation under the prior
    direction is prohibited until realignment has been admitted.
23. Realignment explicitly classifies affected material as retained,
    superseded, introduced, or unresolved in applicability.
24. Uncertain applicability remains non-achievedness; it is not resolved by
    retrieval rank, transcript proximity, or model confidence.
25. Execution-attempt status and semantic-revision status remain separately
    representable.

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

A redirection does not silently mutate this identity. Realignment determines
whether the redirected work:

- remains the same objective under a revised direction;
- becomes a causally derived objective with a new identity;
- or branches as an alternative direction from the prior revision.

If the constitutive meaning of the objective or scope changes, a new objective
or scope identity is required. The prior identity remains a causal ancestor.
This determination is governed and explicit; semantic similarity cannot make
it on its own.

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
- the currently governing direction, including applicable objective, scope,
  constraints, and required outcome;
- supersession and contradiction relationships;
- admitted redirection and realignment records that affect the current state;
- unresolved applicability created by realignment;
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

Interruption alone never creates a semantic revision. The current branch head
remains the latest admitted revision, including any independently admitted
transition committed before the interruption. Work that was generated but not
admitted remains attempt provenance, not current state.

A redirection and its realignment commit as one governed semantic transition.
The resulting revision may contain unresolved applicability as explicit
non-achievedness, but it cannot leave the old frontier active as though the
redirection had not occurred.

## Execution Attempt Model

An execution attempt is the operational episode during which a prepared
reduction is advanced. It is not the semantic object being resumed.

```text
ExecutionAttempt =
  <attempt identity,
   causal anchor,
   operation,
   execution policy,
   lifecycle status,
   externalized proposal and receipt references,
   latest admitted revision reference>
```

Attempt identity is provenance, not causal identity. It cannot replace scope,
objective, branch, or revision identity.

An attempt lifecycle distinguishes at least:

- prepared;
- running;
- interrupted;
- terminated after a semantic outcome;
- and operationally failed.

An interruption record identifies the attempt, the causal anchor, the latest
admitted revision known at the boundary, the stopping cause when known, and
references to any externalized unfinished proposals. It does not serialize
private reasoning or infer state from a partially emitted answer.

Attempt artifacts remain addressable from history and path inspection as
non-state operational episodes. They are never projected as accepted semantic
steps merely because they occurred.

If a process disappears before recording an interruption, correctness is still
preserved: the immutable revision repository and branch head remain
authoritative, and any uncommitted work remains non-state.

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
- the currently governing direction;
- any admitted redirection and realignment dispositions affecting the current
  objective;
- unresolved applicability that must remain non-achievedness;
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

Uncommitted work from an interrupted attempt is never included as achieved
state. It may be retrieved as clearly typed proposal provenance when a later
operation explicitly elects to reconsider it.

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

The inlet relationship is explicit. At minimum, the resumption contract
distinguishes:

- `continuation`, which proceeds under the current governing direction;
- `augmentation`, which adds semantic material without implied withdrawal;
- `redirection`, which proposes a changed objective, scope, constraint set, or
  required outcome;
- `correction`, which proposes explicit supersession;
- and `hold_satisfaction`, which addresses a specific `HoldOn` predicate.

These relationships cannot be inferred solely from where a message appears in
a transcript. If the relationship is materially ambiguous, that ambiguity is
resolved before state mutation or remains non-achievedness.

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

### Resume After Interruption

This operation starts a new execution attempt from the latest admitted revision
of an interrupted attempt. It does not require or satisfy a `HoldOn` predicate,
because interruption alone did not create a semantic suspension.

By default, unfinished proposals from the interrupted attempt are not active
context. A caller may explicitly select them for governed reconsideration as
proposal provenance. If the causal branch head has moved, ordinary stale-anchor
and branch rules apply.

### Continue Objective

This operation begins a new reduction from the current state of the same
objective. It may preserve state, add non-achievedness, or refine existing
non-achievedness.

### Augment Objective

This operation submits an explicitly additive inlet. Reconciliation may admit
new evidence, achieved material, or non-achievedness, and may expose a conflict
that requires later work. It cannot remove or supersede existing current
material unless a separate correction or redirection relationship is proposed
and admitted.

### Redirect And Realign

This operation proposes a new governing direction and computes the governed
realignment required before further reduction. It produces an explicit
identity disposition and classifies affected state and non-achievedness as:

- retained;
- superseded from active state;
- introduced;
- or unresolved in applicability.

The operation commits the redirection and realignment atomically. A result with
unresolved applicability is valid only when that uncertainty is represented as
non-achievedness and the old frontier is not allowed to continue unchanged.

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

### Interruption Is Not HoldOn

`HoldOn` is a governed semantic state that preserves unfinishedness under an
explicit resume predicate. Interruption is an operational event that stops an
attempt. Therefore:

- interruption does not synthesize a `HoldOn`;
- a `HoldOn` can remain active across one or more interruptions;
- resuming an interrupted attempt does not satisfy a `HoldOn`;
- and converting interrupted work into a semantic suspension requires a
  separate admitted transition.

This distinction prevents process control, cancellation, or host loss from
silently changing the semantic state of the objective.

A request to abandon, terminate, or replace the objective is therefore not
modeled as interruption alone. It is a separate governed semantic operation,
potentially a redirection or terminal transition, with its own admission and
provenance.

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

Augmentation reconciliation is monotonic with respect to existing current
material: it can add candidates, evidence, conflicts, and non-achievedness, but
cannot classify existing material as withdrawn or superseded merely because the
new material differs from it.

Redirection reconciliation is not complete until realignment has accounted for
the affected semantic basis.

## Realignment Contract

Realignment is a governed reconciliation result, not a text rewrite and not a
fresh prompt assembled without causal state.

```text
Realignment =
  <source revision,
   redirection inlet,
   affected scope,
   identity disposition,
   retained set,
   superseded set,
   introduced set,
   unresolved-applicability set,
   resulting non-achievedness,
   evidence and governance references,
   completeness statement>
```

For every item in the affected current achieved state and current
non-achievedness, the realignment records exactly one carry-forward
disposition:

- **retained** means evidence establishes continued applicability;
- **superseded** means evidence establishes that the item no longer governs
  active state under the new direction;
- **unresolved** means available evidence does not establish applicability.

The **introduced** set separately records semantic material that did not exist
in the source revision and is proposed by the redirection or its
reconciliation.

The carry-forward disposition sets are mutually exclusive and exhaustive over
the affected source material. Introduced identities cannot simultaneously be
classified as source material. The completeness statement proves that all
affected material was considered directly or through a stable bounded
reference. Material outside the affected scope remains current only when that
non-impact is explicit in the realignment basis.

Superseded material remains in provenance and path history. Unresolved material
becomes non-achievedness and cannot participate as an assumed current fact.
Introduced material in a realignment candidate remains proposed until
independently verified and admitted under its proper semantic kind. Once the
transition commits, admitted introduced material becomes current according to
that kind.

Identity disposition is part of realignment. It explicitly records whether the
result continues the same objective, derives a new objective or scope identity,
or creates a branch. A change to constitutive identity cannot be hidden inside
ordinary revision metadata.

The controller may use deterministic rules, explicit relationships, and
advisory model proposals to construct a realignment candidate. Governance and
verification admit the result. Retrieval similarity can nominate evidence but
cannot decide a disposition.

### Redirection Is Not Correction

Correction asserts that identified current material should be replaced or
invalidated. Redirection changes what the reduction is directed toward even
when prior material was valid under the former direction.

Accordingly, a realignment supersession means that material no longer governs
active state under the redirected objective. It does not, by itself, assert
that the material was false. If both truth correction and directional change
are required, the transition records both relationships explicitly.

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

Interruption does not advance the branch head. A late result from an interrupted
attempt may not commit merely because it eventually finishes. It must still
pass attempt-lifecycle checks and compare-and-swap against the exact expected
head.

Augmentation and redirection are anchored to exact revisions. If a redirection
realigns a branch while an older continuation is in flight, the older
continuation becomes stale for that branch. It may be abandoned, reconciled
against the new head, or preserved as an explicit branch; it cannot overwrite
the realigned state.

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

For augmentation, admission also verifies that no existing state is silently
withdrawn or superseded.

For redirection, admission also verifies:

- that the new direction is explicit;
- that identity impact is resolved or represented as non-achievedness;
- that every affected item has a realignment disposition;
- that retained and superseded classifications have evidence;
- that unresolved applicability remains non-achievedness;
- and that unchanged continuation under the prior direction is disabled.

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

The runtime may observe a stop signal or loss of execution capacity and return
an interrupted attempt outcome. It does not reinterpret that outcome as
`HoldOn`, incompletion, failure of the objective, redirection, or state change.
The controller and repository preserve the latest admitted revision and record
the attempt boundary separately.

After an admitted redirection, the runtime receives only the realigned frontier.
It must not continue an already prepared frontier derived from the prior
direction.

## Artifact-Mediated Attempt And Transition Verification

Every execution attempt emits an inspectable attempt artifact containing:

- attempt identity and lifecycle status;
- exact causal anchor and initial branch-head digest;
- operation and execution policy;
- externalized proposal and receipt references;
- interruption cause and boundary, when known;
- latest admitted revision observed by the attempt;
- and any semantic transition-artifact references produced by the attempt.

Every proposed semantic transition emits an inspectable transition artifact
containing:

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

An interrupted attempt with no admitted semantic transition has an attempt
artifact but no resulting semantic revision. Externalized unfinished proposals
remain visibly typed as proposals. Private or partially emitted model reasoning
is neither reconstructed nor promoted into the artifact.

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
- decide that an interruption changed semantic state;
- silently reinterpret augmentation as correction or redirection;
- authoritatively classify realignment dispositions;
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
- whether existing material remains applicable after redirection;
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
- admitted redirection and realignment traversal;
- realignment disposition and completeness verification;
- transition-artifact append;
- provenance and supersession traversal;
- deterministic state and projection digest verification;
- and reconstruction without model-provider state.

The persistence boundary must also support an attempt journal that is distinct
from semantic revisions. It records attempt lifecycle, interruption, and links
to externalized proposals, transition artifacts, and the latest admitted
revision. Recording an attempt does not update a semantic branch head.

The prepared attempt record is durable before runtime execution begins.
Terminal lifecycle updates are conditional on the current attempt status. If a
worker disappears, recovery can observe and close the abandoned operational
episode without inferring a semantic outcome or changing the branch head.

The repository commits the new revision, transition artifact, and branch-head
change atomically. A partial commit is not visible as a valid continuation.

For redirection, that atomic unit also contains the admitted realignment and its
identity disposition. For interruption, the durable unit is only the attempt
record and related receipts unless an independent semantic transition had
already committed.

Derived indexes, caches, search vectors, and materialized views are rebuildable.
They are not canonical state.

## Event Delivery

Semantic-state events are emitted only after authoritative revision commit. An
event identifies the committed revision and allows subscribers to reread their
projections.

Attempt-lifecycle notifications, including interruption, may be emitted only
after the corresponding attempt record is durable. They identify an attempt and
its observed branch head, but never claim that semantic state changed.

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
- the admitted governing direction and any realignment disposition;
- retrieved candidate artifacts kept distinct from admitted state;
- currently available capabilities;
- and the execution policy for the reduction.

Conversation history can be consulted as provenance or evidence only when
explicitly selected and admitted. It is not automatically re-fed.

The path taken so far is included only when required by the operation. Ordinary
continuation does not require replay of the path once its admitted result is
represented in current state.

Resume-after-interruption begins from the latest admitted revision. Unfinished
proposal artifacts from the interrupted attempt are excluded unless the caller
explicitly selects them for governed reconsideration. After redirection, no
cached or previously assembled context from the prior direction is reusable
without reconstruction against the realigned revision.

## Cache Semantics

Caching is optional and cannot affect correctness.

A reusable proposal cache key includes at least:

- exact projection digest;
- inlet digest;
- operation kind;
- governing-direction and realignment digest;
- proposal schema and prompt version;
- model and provider identity;
- and relevant governance posture.

A cache hit yields a prior proposal for reevaluation. It never yields an
already admitted transition merely because the proposal was admitted under a
different revision.

## Layer Responsibilities

### Runtime And Skill Execution

- Advance an already prepared active reduction.
- Own the dependency-inverted execution-attempt lifecycle and observe stop
  signals without assigning them semantic meaning.
- Return an explicit interrupted-attempt outcome when execution stops before a
  semantic disposition.
- Execute mechanically bound host realizers under current authority.
- Return effect results and receipts.
- Own no transcript, causal routing, revision selection, or state admission.

### Controller

- Own resumption identity semantics.
- Construct projections.
- Reconcile inlets with current state.
- Govern active non-achievedness and reduction flow.
- Represent correction, supersession, branching, merge, augmentation,
  redirection, and realignment semantics.
- Construct only a realigned frontier after an admitted redirection.
- Prepare the frontier supplied to the runtime.

### Governance

- Evaluate admission, policy, lifecycle, approval, revocation, freshness, and
  current-use authority.
- Evaluate realignment evidence, completeness, identity impact, and authority.
- Return inspectable decisions for inclusion in applicable transition
  artifacts; interruption without semantic change requires no fabricated
  admission decision.

### LLM

- Produce advisory interpretations and proposals.
- Own no state, authority, admission, or causal identity.

### Workstation Or Other Conversation Host

- Own sessions, transcripts, user interaction, and presentation.
- Let the user select or confirm a causal objective when necessary.
- Submit explicit identities and inlets through the application contract.
- Submit interruption requests against attempt identity rather than pretending
  that cancellation is a semantic inlet.
- Render structured outcomes without converting rendered prose back into state.

### Entry And Exchange

- Compose repository, governance, controller, runtime, model, and host
  implementations.
- Expose ingress, export, inspection, and administrative surfaces.
- Route conversation turns, interruption controls, and typed continuation
  operations without making transcript order a causal-state contract.

### Shared Host Interaction Substrate

- Resolve current host realizers, attachments, capabilities, delegated rights,
  and effect receipts.
- Remain below both controller and workstation without absorbing either one's
  responsibilities.

### Package Boundary Placement

- `realized-core-runtime` owns only the dependency-inverted attempt lifecycle
  and protocols for prepared state, interruption observation, closure,
  finalization, and persistence adapters.
- `realized-core-engine` owns the canonical semantic implementation: identity,
  projection, reconciliation, realignment, governance integration, state model,
  and plain-SQLite adapters exposed through its public typed ABI.
- `realized-core` owns CLI and conversation-host composition, including mapping
  user controls and turns to typed engine operations.
- workstation shells and transports consume supported application contracts;
  they do not import controller internals or infer state from rendered panes.

This placement preserves the allowed dependency direction. The runtime package
does not depend on engine, entry, workstation, model-provider, or storage
implementations. The engine does not acquire transcript ownership. Entry and
workstation layers remain replaceable hosts over the same semantic contract.

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

The operation kind distinguishes ordinary continuation, resume after
interruption, suspended-objective resumption, augmentation, correction,
redirection with realignment, branching, and merge. An inlet is optional only
where the operation is semantically valid without one, such as restarting
execution from an unchanged admitted revision after interruption.

### Interruption Request

- exact execution-attempt identity;
- requesting principal and authority context when user initiated;
- reason or cause when known;
- and correlation metadata.

An interruption request targets execution, not a semantic revision. Its result
reports whether the attempt was stopped or had already terminated; it does not
claim semantic mutation.

### Interruption Result

- exact execution-attempt identity;
- observed prior and resulting attempt lifecycle status;
- whether stop was accepted, already complete, or not applicable;
- latest admitted revision and branch head observed;
- attempt-artifact reference;
- and explicit confirmation that no semantic revision was created by the
  interruption itself.

### Resumption Result

- source revision identity;
- execution-attempt outcome;
- semantic outcome when one was established;
- resulting revision identity when committed;
- transition-artifact reference when a transition was proposed;
- attempt-artifact reference;
- realignment summary and identity disposition when applicable;
- current achieved-state summary;
- current non-achievedness summary;
- active `HoldOn` summary;
- conflict, rejection, or stale-anchor information;
- presentation-ready view kept separate from state.

### Inspection Request

- exact revision, branch-head, or execution-attempt identity;
- requested view: current state, non-achievedness, governing direction,
  realignment, path, provenance, attempt, transition, branch graph, or
  reconstruction data.

The transport may be an in-process interface, command line, RPC, or another
mechanism. Transport does not alter semantics.

## Outcome Model

Execution-attempt outcome and semantic outcome are separate.

An execution attempt concludes as one of:

- `terminated`: it reached a governed semantic disposition;
- `interrupted`: execution stopped without interruption itself changing state;
- `operationally_failed`: infrastructure or execution failed before a semantic
  disposition could be established.

When an attempt reaches a semantic disposition, that disposition is one of:

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

`interrupted` is intentionally absent from the semantic list. It reports what
happened to execution, not what is achieved or non-achieved. An interrupted
attempt can cite the latest admitted revision but cannot create one solely to
record interruption.

`operationally_failed` means no semantic failure disposition was established.
The semantic `failed` outcome is used only when failure itself was externally
represented, verified, and governed as the disposition of the reduction.

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
- attempt lifecycle and interruption records;
- governance and admission decisions;
- redirection and realignment dispositions;
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
- attempt preparation and interruption latency;
- realignment construction and verification latency;
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
21. Interruption without a committed transition leaves achieved state,
    non-achievedness, direction, and branch head unchanged.
22. Unfinished proposals from an interrupted attempt do not enter ordinary
    current-state projection.
23. Resume after interruption reconstructs from the latest admitted revision,
    not from hidden process or provider state.
24. Interruption does not create or satisfy a `HoldOn`.
25. Augmentation can add material and expose conflict but cannot silently
    supersede existing state.
26. Redirection prevents execution of a frontier prepared under the prior
    direction.
27. Realignment accounts for every affected item as retained, superseded,
    introduced, or unresolved.
28. Retained and superseded dispositions require inspectable support.
29. Unresolved applicability becomes non-achievedness.
30. A constitutive objective or scope change receives a new causally linked
    identity rather than mutating the old identity silently.
31. A late result from an interrupted or pre-redirection attempt cannot commit
    over the current branch head.
32. Attempt records, transition artifacts, and semantic revisions remain
    distinguishable under inspection and replay.
33. LLM-off execution can perform identity, augmentation, interruption, and
    mechanically decidable realignment flows without semantic degradation.

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
- turn interruption into an implicit pause, failure, or state transition;
- treat augmentation as implicit withdrawal;
- continue an old frontier after established redirection;
- resolve uncertain applicability by similarity or model confidence;
- or impose a single linear continuation model.

## Completion Standard

An implementation conforms when every continuation can be reconstructed from
its explicit causal anchor, admitted state, current non-achievedness,
governing direction, provenance, attempt artifact, transition artifact, and
resulting revision without relying on a transcript, hidden model state,
provider session, cache, process lifetime, or ambient host authority. It must
also be possible to prove that interruption alone changed no semantic state and
that every admitted redirection was followed by an inspectable realignment.
