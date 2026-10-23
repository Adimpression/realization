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

## Current Implementation Baseline

This section is a conformance inventory recorded after the theory-derived
design was established. It describes the implementation present on 23 October
2026; it does not make that implementation authoritative over the design.

The dependency-inverted attempt layer in `realized-core-runtime` currently
provides:

- prepared, running, interrupted, terminated, and operationally failed attempt
  lifecycles;
- typed interruption requests and results;
- optional observation of an attempt only after it is durably running, so an
  outer application can expose interruption without treating attempt identity
  as semantic identity;
- conditional attempt-state transitions; and
- an attempt-journal protocol that does not own semantic revisions.

The canonical engine in `realized-core-engine` currently provides:

- typed identities, immutable semantic revisions, projections, inlets,
  semantic deltas, realignments, reversals, transition artifacts, and
  inspection results;
- the complete declared operation set: start, continue, derive,
  resume-after-interruption, resume-suspended, augment, correct,
  redirect-and-realign, branch, merge, explain, verify, reverse, and
  reconstruct;
- exact-anchor and compare-and-swap branch-head validation;
- a plain-SQLite revision, attempt, transition-artifact, event, and derived-index
  repository;
- interruption separated from semantic mutation;
- correction, supersession, `HoldOn`, branching, merge, realignment, path,
  replay, and inspection behavior; and
- an adapter that projects admitted semantic state into the canonical reduction
  controller and projects controller output back into typed semantic state.

The engine test suites exercise these contracts directly, including restart
and provider replacement, transcript and presentation independence,
non-achievedness preservation, correction, ambiguity, augmentation,
interruption, realignment, stale anchors, branching, merge, replay, event loss,
and LLM-off mechanically decidable paths. Those tests establish engine-level
behavior only. They do not establish that an ordinary conversation host can
express or route every operation correctly.

The transport-neutral `realized-core-conversation` component provides the
explicit application boundary needed for conversational resumption. The
`realized-core` Entry/Exchange package retains compatibility imports and
composes that component for the narrow CLI, but does not own its behavior:

- `ConversationTurnPlan` separates advisory application planning from engine
  requests and records the original message, plan, request, and resulting
  binding independently;
- typed plans route start, continuation, derivation, hold satisfaction,
  augmentation, correction, redirection and realignment, interruption resume,
  branch, merge, explanation, verification, reversal, and reconstruction;
- exact causal bindings are resolved mechanically before a request reaches the
  engine, and absent bindings cannot be inferred from similar wording;
- correction and selection accept uniquely resolvable semantic selectors as
  well as exact item identifiers, while zero or multiple matches are rejected;
- a structured start or continuation delta works with LLM operation disabled;
- live execution may expose its durably running attempt identifier through an
  optional callback, while interruption remains a separate operational call;
- provider-neutral planning and rendering protocols plus a natural-language
  host entry point can produce an advisory proposal, normalize it into a typed
  turn plan, submit it through the engine, and render the structured result;
- planning and rendering interactions are recorded separately from semantic
  revisions;
- contribution, proposal, normalized request, engine submission, structured
  result, rendering, and delivery stages have stable identities in a durable
  SQLite activity journal;
- normalized requests reconcile against authoritative engine records after a
  restart, so retrying a submitted turn cannot silently create a second
  semantic transition;
- the original four-treatment API remains as a compatibility adapter; and
- unknown terminal slash commands are rejected rather than started as
  independent objectives.

The reusable `realized-core-llm` adapter owns provider prompt construction,
schema-constrained planning and rendering calls, provider-response parsing,
and interaction receipts. It returns advisory structures only. The
conversation component retains mechanical ownership of proposal validation,
causal binding, selector resolution, admission, engine submission, recovery,
and result identity.

Both ordinary hosts now compose this same product path:

- the core CLI sends ordinary provider-backed input through
  `realized-core-conversation` and `realized-core-llm`; and
- the workstation shell exposes an additive `governed_conversation` mode that
  consumes those same public packages without depending on the CLI entry
  package.

The following surface constraints remain deliberate rather than missing
semantic behavior:

- the terminal loop exposes only the four compatibility routing commands and
  binding selection as dedicated slash commands; the complete operation set is
  available through typed plans and the ordinary-language planning path rather
  than a separate command for every operation;
- `follow_up` in the compatibility adapter still means derivation, whereas a
  provider-backed turn uses the complete operation vocabulary to distinguish
  continuation, hold satisfaction, derivation, explanation, and independent
  work; and
- concurrency remains owned by the embedding application. The host exposes the
  running-attempt notification and interruption method but does not create an
  application thread or task itself.

The obsolete five-turn provider-backed characterization has been replaced by a
full Cedar scenario that covers all 21 resumption principles. The runner
imports only the public conversation and LLM product surfaces, admits only
declared scenario operations, and observes product-owned receipts for timing
and provenance. It does not own a planner, prompt, normalizer, selector
resolver, journal, or recovery path. Its deterministic structural validation
passes. Its configured live-provider qualification also passes the complete
24-turn journey with 94 structural, 20 interpretation, and 22 rendering checks.

The deterministic cross-layer journey maps every principle in `RESUMPTION.md`
to a concrete probe and exercises the real conversation host, engine, runtime
lifecycle, and SQLite repository with model operation disabled. It covers the
mechanically decidable operation and continuity contracts. This establishes
the explicit-control path and protects the semantic engine independently of a
provider, but it is not the complete conversational qualification.

The provider-backed product path now interprets ordinary user contributions as
advisory proposals, mechanically retains causal identity, resolves public
selectors, rejects unresolved interpretation, submits only a validated typed
request, and renders only the structured outcome. Its provider adapter,
schemas, prompt policy, receipt capture, and retry behavior live in product
packages below Entry/Exchange and UI adapters. A configured live Cedar run now
provides evidence that the real provider traverses that path across the complete
bounded scenario. That evidence complements rather than substitutes for the
deterministic engine and typed-host tests.

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
- `realized-core` owns the narrow CLI and Entry/Exchange composition. It adapts
  terminal input and output to the transport-neutral conversation application
  contract; reusable turn planning, normalization, and recovery behavior does
  not remain private to that entry package.
- workstation shells and transports consume supported application contracts;
  they do not import controller internals or infer state from rendered panes.

This placement preserves the allowed dependency direction. The runtime package
does not depend on engine, entry, workstation, model-provider, or storage
implementations. The engine does not acquire transcript ownership. Entry and
workstation layers remain replaceable hosts over the same semantic contract.

## Application Contract

The application boundary exposes semantic operations rather than transcript
continuation commands.

### Conversation Planning Boundary

A conversation host needs one additional application-layer boundary between a
user contribution and the semantic engine request. That boundary is a planner,
not a second controller and not an admission authority.

```text
ConversationTurnPlan =
  <selected causal binding,
   proposed operation,
   proposed inlet relationship,
   proposed semantic target selectors,
   proposed semantic delta or realignment,
   unresolved interpretation,
   provenance>
```

The host establishes the causal binding mechanically before semantic
interpretation. It comes from one of:

- an explicitly selected scope, objective, branch, and revision;
- the session's explicitly selected active binding;
- an exact branch-head lookup requested by the user; or
- no prior binding, in which case the request is a candidate start operation.

Neither an LLM nor similarity retrieval may invent, replace, or silently change
that binding. If more than one causal binding could apply and the user has not
selected one, the plan remains ambiguous and asks for selection before any
state mutation.

The planner then proposes how the contribution relates to the selected state.
It may use deterministic syntax, structured UI controls, exact semantic
selectors, or an LLM-assisted interpretation. Its output remains a proposal.
The application resolves public selectors against the anchored projection and
constructs an exact typed request. The engine validates the resolved targets
and operation/relationship pair, verifies the proposed delta, applies
governance, and alone decides whether a transition commits.

Semantic targets exposed to a person or transport should be stable public
selectors where possible, such as an item key, kind, field, or exact inspected
identity. The application resolves a unique selector to the corresponding
current item identity. Zero or multiple matches produce explicit unresolved
interpretation; they do not authorize a guess. Raw internal item identifiers
remain accepted for exact automation and inspection workflows, but are not the
only usable correction journey.

The planner distinguishes at least:

- independent start;
- continuation of the same objective;
- satisfaction of a selected `HoldOn`;
- additive augmentation;
- explicit correction and supersession;
- redirection with an explicit realignment proposal;
- resume after interruption;
- derivation of a new objective from selected admitted material;
- branch and merge;
- and explain, verify, reverse, or reconstruct path operations.

The word "follow-up" is not itself an operation. Depending on user intent, a
later turn may continue the same objective, satisfy a hold, derive a new
objective, explain the current one, or start unrelated work. The host must not
map every follow-up to derivation.

Explicit commands and structured controls are mechanically interpreted and
must work with LLM operation disabled. Unknown commands are rejected as unknown
commands; they are never stripped of their control meaning and submitted as a
new objective. Natural-language interpretation may be model-assisted, but the
resulting plan remains advisory and must expose uncertainty rather than hiding
it in a confidence score.

An initial start plan may carry a structured semantic delta containing facts
already explicit in the inlet and non-achievedness explicitly stated or
mechanically derivable from it. This permits deterministic, LLM-off chat flows
without treating raw prose as admitted state. When a model proposes the
structure, the proposal still passes the same verification and admission
boundary.

A clarification after redirection does not rewrite the prior realignment. It
creates another anchored transition that explicitly resolves, retains, or
supersedes the applicability items left non-achieved by that realignment.

Interruption remains a separate control path. The host targets the exact
execution-attempt identity with an interruption request; it does not encode
"stop" as a semantic inlet. Resume-after-interruption targets the latest
admitted revision recorded by that attempt and does not promote unfinished
proposal material.

A host that permits interruption must be able to observe the attempt identity
while execution is still active. The runtime therefore exposes an optional
lifecycle observation only after the attempt has been durably recorded as
running. The engine narrows that observation to the opaque attempt identity,
and the application decides whether to run the request concurrently and expose
an interruption control. This observation is operational coordination: it does
not enter the semantic inlet, alter causal identity, or make the attempt a
state revision. If execution wins the race and terminates first, the ordinary
already-complete interruption disposition applies.

The host records the original message, the typed plan, the exact engine
request, and the resulting binding separately. Presentation is rendered from
the structured result and is never reparsed to manufacture the next plan.

Turn-level response completion is also kept separate from the engine's
objective-level semantic outcome. A host may render a complete response to a
turn whose objective remains `incomplete`, `paused`, `ambiguous`, or
`conflicted`; it must not relabel that objective as completed merely because a
message was emitted.

### Natural-Language Conversation Pipeline

An ordinary user contribution is an inlet at the inter-reduction boundary, but
it is not yet a normalized semantic inlet and is not an engine request. Its
original envelope is retained even when interpretation fails. The
conversational path interprets that envelope into a bounded candidate, then
crosses the same typed engine boundary used by explicit controls. The order is
strict:

1. The host durably records the original contribution envelope, provenance,
   correlation identity, and idempotency identity without treating its prose as
   admitted semantic state.
2. The host resolves the selected causal binding mechanically, or records that
   no binding exists for a possible start.
3. The host inspects the exact anchored projection and constructs a bounded
   planning context.
4. A planner proposes a structured interpretation of the inlet: an operation,
   inlet relationship, public semantic selectors, candidate delta or
   realignment, and any unresolved interpretation.
5. The host records the planning interaction and validates and normalizes its
   proposal without granting it authority.
6. The host resolves selectors only against the anchored projection and builds
   the typed engine request.
7. The engine performs reconciliation, verification, governance, execution,
   and admission.
8. The host durably records the engine result and resulting causal binding
   before presentation begins.
9. A renderer produces conversational presentation only from the original
   contribution, the admitted structured result, and explicitly permitted
   inspection views.
10. The host records the rendering receipt and presentation as records distinct
    from semantic state.

For an existing objective, the planner receives the binding selected by the
host and cannot replace it. For an unbound contribution, the planner may
propose `start` or report unresolved intent, but the host allocates all new
scope, objective, branch, and revision identities. A model-produced identity
is never accepted as causal identity.

The bounded planning context contains only what is needed to interpret the
current contribution:

- the original contribution and its provenance;
- whether an exact causal binding is selected;
- the selected binding and deterministic projection when one exists;
- the available operation and inlet-relationship vocabulary;
- active `HoldOn` summaries and current non-achievedness;
- stable public selectors for eligible current material;
- explicit branch or source aliases already resolved by the host; and
- schema, policy, and prompt versions needed to interpret the proposal.

Transcript history is not included by default. If a prior contribution is
needed as evidence, it is supplied as explicitly selected provenance and
remains distinguishable from admitted state. Internal item identifiers,
unselected objectives, ambient branch heads, native capability handles, and
hidden provider memory are not exposed as choices for the planner.

The advisory planning result contains at least:

- a proposed operation and inlet relationship;
- proposed public selectors and source references;
- proposed facts, non-achievedness, corrections, or realignment material;
- an explicit unresolved interpretation and clarification request when needed;
- planner schema and prompt versions;
- provider and model receipt references when a model is used; and
- timing and failure information kept separate from semantic outcome.

The host accepts a proposal for engine submission only after deterministic
checks establish that:

- the proposal conforms to the planning schema;
- the operation is available for the current binding state;
- the proposal did not choose or alter causal identity;
- every selector resolves uniquely within the anchored projection;
- the inlet relationship is compatible with the operation;
- a correction names explicit material to supersede;
- augmentation does not imply withdrawal;
- redirection carries a complete realignment candidate or explicit unresolved
  applicability;
- interruption targets an observed running attempt through the separate
  operational path; and
- ambiguity is represented rather than converted into a guessed transition.

Malformed output, provider failure, timeout, zero selector matches, multiple
selector matches, or materially ambiguous intent creates no semantic mutation.
The host may ask for clarification or report an operational planning failure,
but it must not silently fall back to `continue`, `derive`, or `start`.

Interpretation ambiguity before a valid structured semantic interpretation has
been constructed is not silently inserted into the objective as semantic
non-achievedness. The original contribution remains a durable inlet and
provenance record, while its unresolved interpretation remains an
application-level condition that may produce a clarification turn. Ambiguity
discovered by engine reconciliation after a normalized inlet crosses the typed
boundary may become governed semantic non-achievedness. This keeps a
provider's inability to parse a message distinct from uncertainty in the
realized subject state without discarding the contribution itself.

Planning and rendering are separate ports. The planner consumes a bounded
projection and proposes structure before admission. The renderer consumes the
structured outcome after admission and produces presentation. A provider may
implement both ports, but the calls, schemas, receipts, and failure handling
remain independent. Rendered prose is never reparsed to recover a plan or
state.

### Conversational Transaction And Retry Boundaries

A conversation turn spans multiple durable activities but is not one database
transaction and not one model session:

```text
received contribution
  -> planning activity
  -> normalized typed request
  -> semantic execution attempt and optional revision commit
  -> rendering activity
  -> delivered presentation
```

Each arrow is recoverable from explicit identities and receipts. The
contribution identity deduplicates receipt of the same user contribution. The
normalized request identity deduplicates semantic submission. A rendering
identity allows presentation to be retried without resubmitting the semantic
transition.

The stage identities are distinct:

- `contribution_id` identifies the received user contribution and is stable
  across delivery retries;
- `planning_attempt_id` identifies one advisory interpretation attempt and
  links its complete or partial receipt to the contribution;
- `normalized_request_id` identifies the canonical typed request together with
  its exact causal anchor and remains stable across semantic-submission retries;
- `execution_attempt_id` identifies the runtime episode created or recovered
  for that request;
- `result_id` identifies the durable structured engine result, including a
  no-commit semantic disposition; and
- `rendering_attempt_id` identifies one presentation attempt over that result.

These identifiers are correlation, provenance, and idempotency identities.
None substitutes for scope, objective, branch, or revision identity.

Failure or interruption has stage-specific meaning:

- before a valid plan exists, no semantic execution attempt has started and no
  semantic state changes;
- after a plan is recorded but before engine submission, retry may reuse the
  recorded proposal only through the same deterministic validation boundary;
- after engine submission, the exact attempt and request identities determine
  whether execution is still running, terminated, interrupted, or failed;
- after semantic commit but before successful rendering, the committed revision
  remains authoritative and presentation can be regenerated from its
  structured result; and
- interruption or partial output from planning or rendering is application
  activity provenance, not a semantic interruption and not resumable hidden
  model state.

Retries never infer success from a provider response alone. They inspect the
request, attempt, transition artifact, revision, and rendering records to
determine the last durable boundary. Repeating a delivery, planning call,
engine submission, or rendering call cannot create a duplicate semantic
transition for the same normalized request.

Idempotency must survive process restart. An in-memory set, the currently
selected conversation binding, or a provider session is insufficient. When a
caller repeats a normalized request after losing the response, the engine
either returns the already recorded attempt/result or proves that no attempt
was durably created before beginning one. A committed revision is never
recreated merely because its presentation receipt is absent.

### Conversational Architecture Placement

The reusable capability is a transport-neutral conversation application
component at the Workstation/application-service boundary, independent of any
concrete shell or UI. It owns:

- contribution, binding, plan, normalized-request, structured-result, and
  rendering contracts;
- deterministic operation and relationship validation;
- selector and alias resolution against an exact projection;
- orchestration of the conversational transaction stages; and
- recovery decisions based on durable stage records.

That component is below CLI and UI entry adapters. It consumes a narrow public
semantic-resumption port rather than controller internals, and it contains no
provider client, terminal loop, Flutter/Textual widget, or trial assertion. It
may be extracted as a cohesive UV project or placed in an existing package only
if that package has the same responsibility and allowed dependency direction.
Its contracts must not remain owned solely by `realized-core`, because
`realized-core` is an Entry/Exchange package and workstation code must not
depend upward on it.

The logical LLM layer owns prompt construction, concrete model/provider calls,
provider-response parsing, provider receipts, and the provider-neutral model
interaction ABI consumed by planner and renderer application adapters. The
conversation component depends toward that LLM ABI; the LLM implementation
does not import Workstation or Entry contracts. If boundary DTOs need a shared
home, they reside in a dependency-free contract package declared in the
architecture manifest rather than creating an LLM-to-Workstation edge. The
conversation component owns normalization and mechanical validation of the
returned proposal; the LLM adapter cannot admit state or choose causal
identity. A dedicated LLM package or correctly classified LLM module may house
the adapter, but trial code may not be its sole owner.

The Controller, exposed by `realized-core-engine`, owns semantic identity,
projection, reconciliation, governance integration, execution, admission, and
revision persistence. It receives a validated typed request, not a transcript,
provider session, prompt cache, or rendered answer. The runtime continues to
own only execution-attempt lifecycle and dependency-inverted execution.

The conversation host owns session selection, transcript display, user-input
delivery, presentation delivery, and a durable conversation-activity journal
implementation. For the narrow CLI this host is composed by `realized-core`.
For Flutter or Textual it is composed by the workstation entry surface. Both
consume the same transport-neutral conversation application contract; neither
duplicates planning normalization or reparses presentation into state.

Entry/Exchange composes the host, conversation component, LLM adapters,
semantic-resumption adapter, repository, governance, and runtime. This allows a
small model, a recorded-proposal adapter, a deterministic explicit-control
planner, or no model at all to occupy the same advisory boundary without
reversing dependencies.

Any new physical package is first declared in the workspace and architecture
manifest with a narrow public API and only the dependencies required by this
logical placement. Compatibility imports may preserve callers during
migration. Entry/Exchange may compose a Workstation/application service as the
six-layer direction permits; Workstation-to-Entry and provider-to-controller
dependency reversals are prohibited.

Planning and rendering receipts are application provenance. They are linked to
the contribution, normalized request, and execution attempt but are not
semantic revisions. Recorded provider responses may support replay of an
LLM-enabled attempt; replaying such a receipt does not constitute a fresh
live-provider qualification.

### Conversation Activity Journal

The host supplies a conversation-activity journal through a narrow persistence
port. The reference CLI and workstation may use different adapters, but the
observable contract is the same. The journal records, by stable identity:

- the original contribution envelope and selected binding;
- each planning request, complete or partial provider receipt, and normalized
  proposal;
- the canonical typed engine request and its submission disposition;
- the execution-attempt identity and durable structured result;
- each rendering request, complete or partial receipt, presentation, and
  delivery disposition; and
- recovery decisions linking a retry to the prior durable stage.

The activity journal is not the semantic revision repository and does not
acquire authority to admit state. The two may share one SQLite database and an
outer transaction where useful, but their records, keys, ownership, and
recovery meanings remain distinguishable. Conversation-record loss may degrade
presentation history, but it must not corrupt or redefine an admitted semantic
revision. Conversely, a contribution or planning receipt that has not produced
an admitted engine result cannot be projected as achieved state.

Recovery reads the journal and the engine's authoritative attempt, transition,
and revision records together. If the activity journal says `submitted` but
lacks a result, recovery queries the engine by normalized request identity. If
the engine reports a durable result, the host records that result and proceeds
to rendering. If no execution attempt exists, the exact normalized request may
be submitted once. The host never resolves this uncertainty by submitting a
different request or by asking the model whether the previous request
succeeded.

### Required Product Surface

The reusable application boundary exposes operations equivalent to:

- accept or recover a contribution by idempotency identity;
- inspect or select an exact causal binding;
- plan and normalize a contribution without semantic mutation;
- submit or recover an exact normalized semantic request;
- render or rerender a durable structured result without resubmission;
- inspect conversational stage receipts and their semantic links; and
- interrupt an observed execution attempt through the separate operational
  control.

These are semantic/application operations, not transport endpoints. A CLI,
in-process API, workstation client, or future RPC may expose them without
altering their identities or stage semantics.

### Product Boundary Versus Qualification Harness

The conversational implementation is a shipped application capability, not a
feature of the Cedar trial. Product code owns:

- the transport-neutral conversation application contract and orchestration;
- semantic-resumption and activity-journal ports at the conversation boundary;
- the provider-neutral planning and rendering ABI in the LLM layer, consumed
  in the allowed Workstation-to-LLM direction;
- versioned planning and rendering schemas;
- LLM-layer prompt policy and concrete provider adapters selected by
  composition;
- bounded context assembly and proposal normalization;
- selector and alias resolution;
- contribution, planning, engine, binding, and rendering receipts;
- idempotency and recovery across conversational transaction boundaries; and
- the public entry point used by the core chatbot and any workstation host.

The qualification harness may select configuration, supply ordinary user
messages, invoke supported operational controls, observe public receipts, and
assert outcomes. It may not own a private planner adapter, duplicate prompt or
schema logic, normalize proposals differently from product code, manufacture a
typed plan for a semantic turn, or repair product state directly. If deleting
the trial runner would remove the only working natural-language conversation
path, the product implementation is incomplete.

### Cedar Conversational Qualification

The Cedar trial is the full conversational qualification for this
implementation. It is one coherent provider-backed chat journey whose probes
collectively cover every governing principle in `RESUMPTION.md`. It complements
rather than replaces deterministic engine and typed-host conformance.

Every semantic user turn that claims to test natural-language interpretation
must enter as ordinary language through the planner port. The harness may not
preconstruct a `ConversationTurnPlan` for that turn and then claim the model
understood it. It must use the same public conversational entry point and
product-owned provider adapter available to an ordinary core-chat or
workstation composition. The harness may perform operational actions that are
not semantic language interpretation, including:

- selecting an exact initial or active binding;
- restarting the host or replacing the provider instance;
- interrupting an observed running attempt;
- arranging concurrent branches or a stale-anchor race;
- deleting transcript availability or changing presentation wording;
- rebuilding a derived index; and
- inspecting revisions, path, attempts, transition artifacts, and receipts.

Those actions must use supported public host or engine contracts. They cannot
write repository state directly, invent admission results, or substitute fake
semantic transitions for the conversation being qualified.

The trial records and evaluates four result classes separately:

1. **Harness validity:** the real packaged host, engine, runtime lifecycle, and
   SQLite repository were used through public contracts.
2. **Structural conformance:** causal bindings, normalized operations,
   selectors, revisions, non-achievedness, realignments, attempts, and path
   artifacts satisfy deterministic assertions.
3. **Interpretation and presentation:** the live provider proposed the intended
   operation and semantic material from ordinary language, and the renderer
   communicated the admitted outcome without inventing state.
4. **Provider performance:** planning latency, rendering latency, token or
   request measurements when available, and failures are reported without
   being conflated with engine latency.

A live-provider failure is a failed conversational qualification, not grounds
to weaken a structural assertion or bypass the planner with a typed fixture.
Recorded proposals and fake adapters remain appropriate for deterministic CI
tests of orchestration and replay, but they are not evidence that the configured
model can conduct the Cedar conversation.

The model-off journey remains mandatory because semantic correctness cannot
depend on provider availability. The live Cedar journey is also mandatory
before claiming this repository's natural-language conversational resumption
scope complete. Passing either one alone is insufficient for that claim.

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

### Compatibility Migration

The existing `independent`, `human_contribution`, `follow_up`, and `correction`
arguments remain temporary compatibility inputs while callers move to typed
turn plans. Their mapping is explicit and testable:

- `independent` maps to start;
- `human_contribution` maps to continue or resume-suspended according to an
  exact selected hold;
- `follow_up` maps only to derive and therefore requires explicit selected
  source material; and
- `correction` maps to correct and requires a uniquely resolved current target.

Compatibility mapping must not claim support for operations it cannot express.
New structured controls use the typed plan directly. Compatibility inputs can
be removed only after repository-wide callers and qualification trials no
longer depend on them.

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
34. The real conversation host, not a fake engine or evaluator-only harness,
    can execute a neutral multi-turn journey that establishes explicit state,
    preserves non-achievedness, corrects two fields, and survives host restart.
35. Every governing principle in `RESUMPTION.md` is mapped to at least one
    executable neutral scenario probe, and the mapping fails when a principle
    is added without a probe.
36. Explicit chat controls cover every application operation family without
    requiring model interpretation, and an unknown control is rejected rather
    than started as an independent objective.
37. Natural-language interpretation cannot choose causal identity; an absent
    or ambiguous binding prevents mutation even when retrieval finds a similar
    objective.
38. A uniquely resolved semantic selector can drive correction without asking
    a person for an opaque item identifier, while an ambiguous selector cannot
    commit.
39. A complete turn response does not erase objective non-achievedness or force
    the objective outcome to `completed`.
40. Conversation-level augmentation preserves all current material unless a
    separately represented conflict is exposed.
41. Conversation-level redirection commits only with exhaustive realignment,
    prevents execution of the old frontier, and carries uncertain
    applicability as non-achievedness.
42. A later clarification resolves realignment uncertainty through a new
    anchored transition rather than mutating the prior realignment artifact.
43. Conversation interruption targets an attempt, creates no semantic revision,
    and resume-after-interruption excludes unfinished candidate work.
44. Explanation and reversal use admitted path artifacts; presentation prose
    alone cannot reconstruct or reverse state.
45. Two conversation branches from one revision remain distinct, and a stale
    continuation cannot overwrite either branch head.
46. Replacing the provider, changing presentation wording, deleting transcript
    availability, or rebuilding derived indexes leaves continuation semantics
    unchanged.
47. The executable governed-chat trial validates current result fields and
    supplies every selector required by the application contract; it contains
    no obsolete checkpoint assertion.
48. The host resolves or withholds causal binding before natural-language
    planning, and the planner cannot choose a similar objective as the target.
49. Every Cedar semantic turn used as interpretation evidence enters as
    ordinary language through the provider-backed planner rather than as a
    preconstructed typed plan.
50. Provider timeout, malformed output, and unresolved interpretation cause no
    semantic mutation and do not silently fall back to another operation.
51. Planner-proposed public selectors are resolved uniquely against the exact
    anchored projection before an engine request is constructed.
52. Planning, engine admission, and rendering produce separate receipts, and a
    rendering change cannot alter the admitted revision or the next planning
    projection.
53. The Cedar journey maps all 21 resumption principles to observable probes
    while distinguishing semantic user turns from explicit operational harness
    actions.
54. A recorded provider proposal can replay the same advisory input, but only a
    live provider run counts as provider-backed conversational qualification.
55. Deleting the Cedar runner leaves a reusable product entry point capable of
    planning, validating, executing, and rendering an ordinary conversation.
56. The trial and ordinary chatbot use the same provider adapter, schemas,
    prompt policy, normalization, and selector-resolution implementation.
57. A duplicate contribution or normalized request cannot create a duplicate
    semantic transition.
58. A crash after contribution receipt but before planning leaves the
    contribution recoverable and semantic state unchanged.
59. A crash after planning but before engine submission permits deterministic
    revalidation without treating the proposal as admitted state.
60. A crash after semantic commit but before rendering preserves the committed
    revision and retries only presentation.
61. Partial or interrupted planner and renderer output never enters semantic
    state and is not treated as an interrupted reduction attempt.
62. Planning ambiguity remains application-level unresolved interpretation,
    while ambiguity admitted through engine reconciliation remains durable
    semantic non-achievedness.
63. A contribution whose planning fails remains inspectable as inlet
    provenance, but creates no normalized engine request or semantic revision.
64. Conversation-activity records remain distinguishable from semantic
    revisions even when both use the same SQLite database.
65. The CLI and workstation hosts consume the same transport-neutral
    conversation application contract without either importing the other's
    entry or UI package.
66. Prompt construction, provider calls, and provider-response parsing remain
    in the LLM layer, while selector resolution and admission remain outside
    the provider adapter.
67. After process restart, a repeated normalized request recovers its existing
    engine attempt/result or proves that none exists before executing; an
    in-memory deduplication result is insufficient.
68. Recovery from a `submitted` conversation stage with no local result
    reconciles against authoritative engine records and cannot create a second
    semantic transition.
69. The Cedar harness contains no product planner, renderer, normalization,
    selector-resolution, journal, or recovery implementation; removing it
    leaves ordinary natural-language conversation operational.

The deterministic cross-layer scenario derives its operations and assertions
directly from the resumption principles rather than from model behavior. The
Cedar scenario applies the same principles to a real provider-backed
conversation. Provider interpretation, prose quality, and latency are reported
separately from deterministic engine correctness, but interpretation is not an
optional concern when qualifying the natural-language conversation product
path.

## Implementation Sequence

The safe correction order is:

1. [x] Retain the direct engine conformance suite and deterministic cross-layer
   scenario as the model-independent semantic baseline.
2. [x] Retain the typed conversation-plan contract, exact semantic-selector
   resolver, complete operation routing, separate interruption control, and
   compatibility adapter.
3. [x] Establish the transport-neutral conversation application component and its
   allowed dependency edges in the architecture manifest before moving code.
   It must be consumable by both Entry/Exchange and Workstation without one
   depending on the other's package.
4. [x] Define its semantic-resumption and activity-journal ports plus versioned,
   serializable contribution, proposal, request, result, and receipt schemas.
   Define the generic planning and rendering ABI on the LLM side of the
   boundary, or in a dependency-free contracts package, so dependency direction
   remains Workstation-to-LLM. Preserve existing imports through compatibility
   shims while callers migrate.
5. [x] Add the durable conversation-activity journal and stable contribution,
   planning, normalized-request, result, and rendering identities. Keep these
   records logically distinct from semantic revisions.
6. [x] Implement the product pipeline in strict contribution receipt, binding,
   projection, planning, normalization, selector resolution, engine submission,
   durable result capture, rendering, and delivery order.
7. [x] Add restart-safe engine lookup and idempotency for normalized request
   identity, then implement recovery at every conversational transaction
   boundary. Do not rely on an in-memory host map to prevent duplicate commits.
8. [x] Implement the reusable planner and renderer provider adapter in the LLM
   layer. Prompt construction and provider calls remain there; proposal
   normalization and selector resolution remain in the conversation component.
   Do not place the only adapter in a trial module.
9. [x] Compose the same product path into the narrow core chatbot and workstation
   entry surfaces. Keep terminal, Flutter, Textual, and other transport details
   outside the transport-neutral component.
10. [x] Add deterministic fake-provider and failure-injection tests for schema
   handling, ambiguity, partial provider output, orchestration, idempotency,
   crash recovery, recorded-proposal replay, and package-boundary direction.
11. [x] Replace the stale five-turn runner with the full Cedar conversational
   scenario, current bindings and selectors, supported operational harness
   actions, and separate structural, interpretation, rendering, and
   performance evidence.
12. [x] Verify that the Cedar harness imports the product surface and owns no
   private planner, prompt, normalizer, journal, or recovery behavior.
13. [x] Run Cedar against the configured live provider and require its natural
   language turns to pass through the real planner and host path.
14. [x] Run core-runtime, core-engine, conversation-component, LLM-adapter,
   core-app, workstation, architecture-ratchet, replay,
   distribution, deterministic journey, governed-chat runner, and live Cedar
   qualification gates before declaring the scope complete or removing any
   compatibility path.

As of 23 October 2026, sequence items 1 through 14 are implemented: the direct
engine baseline, typed operation path, transport-neutral conversation package,
versioned ports and records, durable activity journal, strict conversation
pipeline, restart-safe normalized-request recovery, and reusable live-provider
planner and renderer adapter are present and covered by focused tests. The
narrow core chatbot and workstation shell now compose that same product path
without either importing the other's entry surface. Deterministic tests cover
schema rejection, ambiguity, partial provider output, orchestration ordering,
idempotency, crash recovery, recorded-proposal replay, and package direction.
The default Cedar journey covers all 21 resumption principles, admits only
declared semantic and operational harness actions, consumes the public product
surfaces, and reports structural, interpretation, rendering, and performance
evidence separately. The deterministic architecture/core gate passes 318
tests, the deterministic BDD gate passes 76 tests, the replay gate passes 9
tests, the complete workstation gate passes 602 tests with 1 intentional skip,
and fresh builds of all five core wheels pass isolated-import and SQLite smoke
verification. The live Cedar qualification passes all 24 turns through the
configured OpenAI planner and renderer with engine-internal model use disabled:
94 of 94 structural checks, 20 of 20 interpretation checks, and 22 of 22
rendering checks pass with no operational failure. Draft proposal types,
recorded replays, or runner fixtures remain supporting tests rather than
substitutes for that live end-to-end evidence.

No step changes persisted schema or an existing public import path without a
separate compatibility and migration decision.

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
- make a qualification trial the owner of conversational product behavior;
- require workstation code to depend on a CLI or other Entry/Exchange package;
- or impose a single linear continuation model.

## Completion Standard

An implementation conforms when every continuation can be reconstructed from
its explicit causal anchor, admitted state, current non-achievedness,
governing direction, provenance, attempt artifact, transition artifact, and
resulting revision without relying on a transcript, hidden model state,
provider session, cache, process lifetime, or ambient host authority. It must
also be possible to prove that interruption alone changed no semantic state and
that every admitted redirection was followed by an inspectable realignment.

The natural-language conversational implementation in this repository is
complete only when ordinary user contributions can traverse the provider-
neutral planning boundary, deterministic application validation, canonical
engine, and separate rendering boundary without the model choosing identity or
admission. That path must be reusable by Entry/Exchange and Workstation hosts
through a transport-neutral product contract independent of the trial harness,
with provider behavior owned by the LLM layer and semantic admission owned by
the Controller. Its contribution, planning, normalized-request, semantic
result, rendering, and delivery boundaries must be durably distinguishable,
idempotent, and recoverable without transcript or provider-session state.
Completion additionally requires both the deterministic model-off journey and
a successful live Cedar qualification covering all 21 resumption principles.
A typed fixture, fake provider, recorded replay, trial-local adapter, or
prose-only evaluation cannot substitute for that live end-to-end evidence.
