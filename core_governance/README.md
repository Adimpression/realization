# Realized Core Governance

`realized-core-governance` is the dependency-light owner of Realized governance
vocabulary, lifecycle-only rules, approval-record matching, supplied
revocation/incident safety overlays, stored governance-record projections,
governed declaration and admission-policy normalization, read-only governance
inventory loading and classification, policy-and-approval admission evaluation,
and data-class access rules.

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
- `realized_core_governance.safety`: revocation and incident normalization,
  readable projection, temporal validity, matching against supplied skills,
  and lifecycle overlays derived from supplied safety artifacts.
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
- `realized_core_governance.records`: read-only defensive projection of stored
  skill declaration, policy, and admission records, plus structural policy-
  record classification.

This package does not parse YAML, synthesize declarations from artifacts or
host code, inspect broker availability or executable source, complete
current-use authorization, issue authority, persist governance records,
execute skills, invoke models, or own controller and workstation behavior. Its
admission evaluator decides only the supplied policy and approval portion after
the caller's host preflight. Its inventory port can request the complete
artifact collection from an injected reader, but it does not connect to SQLite,
manage schemas or cache lifetime, or compose a concrete store. It also does not
open virtual mounts, discover query registries, execute queries, or invoke host
brokers. Those concerns remain in their existing owners and combine this
package's values and rules with their own inputs.
