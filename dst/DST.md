# Decision Support Tool

High-level note for the Decision Support Tool (`DST`) layer.

`DST` exists to bridge a specific gap:

- real decision cases usually begin as prose, partial observations, rival intuitions, and unresolved distinctions
- [coordinated_transformation](../coordinated_transformation/COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md) is a closed formal theory that evaluates explicit states, transitions, decisions, constraints, boundaries, and assignments

So the problem is not only evaluation. The problem is how to move from weak, incomplete case material into explicit decision structure without pretending that the source was already formal.

Implementation-specific guidance lives in:

- [DST_IMPLEMENTATION.md](DST_IMPLEMENTATION.md)

## Why DST Exists

`DST` exists because decision support needs an intermediate logical layer between source material and formal evaluation.

Without that layer, there are only two bad options:

- treat source prose as if it were already a decision model
- force the formal theory to behave like a discovery engine

Both are wrong.

Source prose is usually mixed:

- some of it describes the current state
- some of it describes desired outcomes
- some of it names capabilities, constraints, dependencies, or boundaries
- some of it suggests rival paths implicitly
- some of it leaves important distinctions unresolved

That means decision support must first discover what kinds of candidate paths, blockers, and distinctions are even present before it can ask whether a concrete decision is valid, executable, or preferable.

## Relation to Coordinated Transformation

`DST` is upstream of coordinated transformation in federated systems.

The relation is:

- `DST` discovers and stabilizes the decision-bearing structure of the case
- `coordinated_transformation` evaluates explicit modeled candidates inside a closed theory

So their roles are different.

`DST` is responsible for:

- candidate-path discovery
- distinction preservation
- blocker and missingness capture
- typed case normalization

`coordinated_transformation` is responsible for:

- formal admissibility
- formal executability
- formal reachability
- formal coordination and risk reasoning over explicit modeled objects

`DST` should not replace coordinated transformation.
`coordinated_transformation` should not replace DST.

The first opens the case into explicit alternatives.
The second closes explicit alternatives under a formal discipline.

## Why Discovery Comes Before Evaluation

The repository theory already gives a governed discovery mechanism through `reduce_not`.

That matters because a decision case is usually not born as:

- one explicit transition
- one explicit decision
- one explicit actor assignment

It is born as a non-achievedness with rival routes, unclear dependencies, and incomplete boundaries.

So the logical order is:

1. discover candidate ways the non-achievedness might be reduced
2. preserve the important distinctions between those candidates
3. normalize those candidates into typed decision structure
4. evaluate them formally

If evaluation happens before discovery, the system either invents a false single-path case or silently drops alternatives that should have remained visible.

## Why Normalization Comes After Discovery

Discovery alone is not enough.

Raw discovery output is still too unstable to serve as durable decision structure. It may preserve useful distinctions, but it is not yet a case model.

So `DST` needs a typed normalization layer that turns governed discoveries into a stable case vocabulary.

Logically, that normalization must produce explicit decision-bearing structure such as:

- actors
- objectives
- capabilities
- dependencies
- constraints
- boundaries
- states
- transitions
- decisions

This is the point where a case stops being only discovered material and becomes an explicit object that can be reviewed, curated, projected, and evaluated.

## Logical Pipeline

The intended logical pipeline is:

`source case -> governed discovery -> typed normalization -> explicit decision objects -> coordinated transformation evaluation`

That pipeline exists for a reason.

Each step changes the logical status of the material:

1. `source case`
   - provenance-bearing material
   - not yet decision truth
2. `governed discovery`
   - candidate-path and blocker discovery under `reduce_not`
   - still provisional
3. `typed normalization`
   - stable typed case
   - explicit enough for review and projection
4. `explicit decision objects`
   - inspectable decision frame / review structure
   - directly curatable
5. `coordinated transformation evaluation`
   - closed formal judgment over explicit alternatives

The important point is that each stage narrows ambiguity without pretending ambiguity never existed.

## What DST Must Preserve

For `DST` to do its job correctly, it must preserve at least the following:

- distinct candidate paths rather than collapsing them too early
- the reasons paths differ
- blockers that prevent a candidate from being admissible or executable
- dependencies that must be satisfied before a path is viable
- constraints that limit what can be chosen
- boundaries that create friction or coordination overhead
- the difference between current state, intermediate states, and target state
- unresolved or missing facts that still matter to decision quality

If those are lost before formal evaluation, the formal layer may still produce a clean answer, but it will be answering the wrong case.

## Source Prose Is Not Decision Truth

`DST` also exists to enforce a discipline around source material.

Source prose is provenance.
It is not yet the decision model.
It is not yet the publication.

This matters because a decision-support system should remain able to:

- accept new source material
- preserve continuity across revisions
- regenerate structure from improved evidence
- keep explicit decision objects stable enough for review

That is only possible if raw source, discovered structure, normalized case structure, and formal evaluation are kept logically distinct.

## Why We Implemented DST This Way

The logical implementation choice is therefore:

- use governed discovery first, because decision cases begin in non-achievedness and ambiguity
- use typed normalization second, because durable decision support needs stable structure
- use explicit reviewable decision objects next, because decisions must be inspectable and curatable
- use coordinated transformation after that, because formal evaluation should operate on explicit objects, not on prose fragments

This is the repository's intended decision architecture:

`Not<X> discovery -> DST structure -> formal coordinated-transformation evaluation`

That is why `DST` is not merely a prompt, not merely a parser, and not merely a publication helper.

It is the logical bridge between governed discovery and formal decision evaluation.

## Why DST Also Needs Revision Semantics

`DST` cannot stop at one normalized case snapshot.

Real decision support is iterative:

- new prose arrives
- a later source may introduce a new actor, dependency, or constraint
- a previously blocked route may become admissible
- a previously recommended route may become unsafe
- a later import may show that the old frame was incomplete rather than wrong

So if `DST` is only a one-shot discovery and normalization layer, it loses continuity exactly where decision support becomes important.

The logical requirement is:

- preserve one decision-bearing snapshot cleanly enough for formal evaluation
- preserve enough continuity across snapshots to explain how the case changed

That means `DST` must eventually support not only:

- discovery
- normalization
- projection

but also:

- snapshot evolution
- revision-sensitive invalidation
- continuity-preserving refresh

## Relation To CTFS Revision Discipline

This is where `DST` and `coordinated_transformation` must remain cleanly separated.

`coordinated_transformation` defines:

- what is valid inside one explicit model snapshot
- what is admissible, executable, risky, or blocked in that snapshot

Its implementation guidance now also defines how model revision should be understood:

- state transition happens inside a snapshot
- model revision changes the snapshot itself

`DST` should follow that discipline rather than invent a second incompatible one.

So the logical split is:

- `DST` discovers and normalizes a case into a snapshot-ready explicit structure
- `coordinated_transformation` evaluates that explicit structure inside one snapshot
- the `DST` revision layer explains how one discovered/normalized case snapshot becomes the next

This matters because `DST` should not respond to changing source material by weakening formal judgment.

It should respond by:

1. recording that the source basis changed
2. refreshing discovery where needed
3. refreshing normalization where needed
4. producing a new explicit decision snapshot
5. re-running formal evaluation against the new snapshot

So the governing discipline becomes:

`source revision -> DST rediscovery/renormalization -> new explicit snapshot -> CTFS evaluation`

## Snapshot Products Versus Revision Products

`DST` already produces snapshot-local artifacts such as:

- discovery results
- normalized cases
- decision frames
- decision review items
- `coordinated_transformation.Model`

Those remain the right products for one case state at one time.

The revision layer should therefore be additive, not replacement-oriented.

Logically:

- a normalized case is a snapshot product
- a decision frame is a snapshot product
- a CTFS model is a snapshot product
- a revision record is a cross-snapshot product

This distinction is important because it lets existing consumers remain correct.

Current clients ask questions like:

- what are the current candidate paths
- what is the current decision frame
- what transitions are admissible now

Future revision-aware clients will additionally ask:

- what changed between the previous and current snapshots
- which prior admissibility judgments became stale
- which routes were newly blocked or newly unblocked
- whether a later source changed the model or only refined the wording

Those are new questions.
They should be added without changing the meaning of the existing snapshot questions.

## What The DST Revision Layer Must Preserve

If `DST` gains revision semantics, it must preserve the same high-level discipline it already applies to discovery:

- do not collapse materially distinct paths too early
- do not silently replace an old frame with a new one without traceability
- do not carry forward blocked/unblocked judgments when their prerequisites changed
- do not treat a new actor as “magically unblocking” a route unless an admissibility-relevant fact changed
- do not confuse source revision with state transition

So the revision layer should preserve:

- source continuity
- discovered-path continuity where valid
- explicit invalidation when path prerequisites changed
- explicit replacement when the later source materially changes the case structure

## Additive Implementation Principle

The correct implementation discipline is:

> do not rewrite the current DST snapshot pipeline to make revision possible;
> add a revision layer around it and keep the snapshot pipeline intact

That is the only safe way to extend `DST` while preserving existing workstation, test, and projection clients.

So the future shape is not:

`revision-aware DST instead of current DST`

It is:

`current DST snapshot pipeline + revision layer + continuity/invalidation rules`

The theory reason is simple:

- the snapshot pipeline already answers “what is the case now”
- the revision layer should answer “how did the case become this”

Those are different questions and should remain different layers.
