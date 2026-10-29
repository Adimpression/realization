# Realized Core Governance

`realized-core-governance` is the dependency-light owner of Realized governance
vocabulary, lifecycle-only rules, approval-record matching, supplied
revocation/incident safety overlays, stored governance-record projections,
governed declaration and admission-policy normalization, read-only governance
inventory loading and classification, policy-and-approval admission evaluation,
final current-use eligibility over supplied governance state, deterministic
authority coverage over supplied grants, canonical per-effect evidence
receipts, constitutional replay signatures over supplied effect traces, a
structural artifact-writer port, and data-class access rules.

The current public surface contains:

- `realized_core_governance.vocabulary`: skill kinds, risk tiers, approval
  classes, authorities, and their deterministic normalizers.
- `realized_core_governance.lifecycle`: lifecycle states, normalization,
  conservative synthesis, read-only artifact projection, and lifecycle-only
  current-use eligibility.
- `realized_core_governance.approval`: approval-record normalization, readable
  projection, temporal validity, and matching against supplied skill
  requirements and supplied approval artifacts.
- `realized_core_governance.admission`: deterministic admission evaluation over
  a supplied declaration, supplied policy and approval records, portable skill
  semantics, and an injected evaluation clock. Host compatibility preflight is
  deliberately outside this module.
- `realized_core_governance.current_use`: deterministic schema-compatibility,
  admission, and lifecycle eligibility over supplied admission and effective
  lifecycle values. It does not retrieve or recompute those values.
- `realized_core_governance.authority`: an immutable authority-evaluation value
  and a deterministic deny-by-default check over supplied current-use state,
  required authority, and invocation grants. Effect mapping, grant issuance,
  executor matching, and dispatch remain outside this module.
- `realized_core_governance.safety`: revocation and incident normalization,
  readable projection, temporal validity, matching against supplied skills,
  and lifecycle overlays derived from supplied safety artifacts.
- `realized_core_governance.trace`: canonicalization and versioned semantic
  receipts for already-supplied per-effect evidence, plus the stable
  replay-significant projection of an already-supplied effect trace. Its
  SHA-256 evidence receipts and constitutional replay signatures remain
  distinct contracts. Runtime still decides when to capture evidence,
  assembles traces and state snapshots, compares or replays runs, records
  results, and executes effects.
- `realized_core_governance.data`: data-class normalization, projection from a
  supplied governance context, access checks, named-query declaration
  normalization, and lexical read-only-query checks.
- `realized_core_governance.declarations`: deterministic validation and
  normalization of governed v2 skill declarations and admission policies, plus
  reviewable policy summaries. Portable schema and executor vocabulary comes
  from `realized-skill-semantics`; YAML parsing remains outside governance.
- `realized_core_governance.inventory`: a structural read-only inventory port
  plus deterministic policy, approval, revocation, and incident classification
  over the artifacts returned by that port.
- `realized_core_governance.persistence`: a structural batch-writer port and an
  exact forwarding seam for already-prepared governed artifacts. It does not
  define a database, schema, transaction, serialization, or indexing policy.
- `realized_core_governance.records`: read-only defensive projection of stored
  skill declaration, policy, and admission records, plus structural policy-
  record classification.

This package does not parse YAML, synthesize declarations from artifacts or
host code, inspect broker availability or executable source, retrieve or
recompute current-use governance state, issue authority, implement persistence,
execute skills, invoke models, or own controller and workstation behavior. Its
admission evaluator decides only the supplied policy and approval portion after
the caller's host preflight. Its authority evaluator checks only whether the
caller's supplied admission and grants cover a caller-supplied authority; it
does not map host effects, select or inspect a realizer, issue grants, or create
runtime trace records. Its inventory port can request the complete
artifact collection from an injected reader, and its writer port can forward an
already-prepared batch to an injected writer, but it does not connect to SQLite,
manage schemas, transactions, indexing, cache lifetime, or compose a concrete
store. It also does not
open virtual mounts, discover query registries, execute queries, or invoke host
brokers. Those concerns remain in their existing owners and combine this
package's values and rules with their own inputs. Final current-use eligibility
is not an authority grant and does not dispatch an invocation. Retrieval and
semantic ranking also remain outside governance, but a consumer must apply the
final current-use decision before promoting a retrieved governed artifact as
an answer or invocation candidate. Similarity can justify consideration; it
cannot override admission, lifecycle, safety, policy, or authority. Receipt
derivation does not observe effects, create trace identifiers or timestamps,
select evidence, mutate runtime state, persist records, or perform replay.
