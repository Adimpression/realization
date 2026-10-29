# Realized Core Semantics

`realized-core-semantics` owns the dependency-light formal theory values and
read-only semantic contracts shared by Realized domains. Its theory models are
structural values; they do not admit artifacts, choose abilities, grant
authority, execute effects, call model providers, or persist application state.

The public surface is intentionally split into twelve explicit modules:

- `realized_core_semantics.theory` contains the Pydantic formal-system model.
- `realized_core_semantics.artifacts` contains narrow read protocols for
  artifact consumers.
- `realized_core_semantics.decision_review` contains dependency-light decision
  frame and review-item values, normalization, and stable identifiers.
- `realized_core_semantics.identifiers` contains dependency-free slug,
  subject-identity, and identifier construction helpers.
- `realized_core_semantics.itemization` contains dependency-light itemization
  session and item values plus their normalization rules.
- `realized_core_semantics.markdown` contains dependency-free Markdown IR
  values, parsing, bounded semantic views, symbolic mappings, and normalization.
- `realized_core_semantics.prolog` contains dependency-free parsing,
  normalization, unification, and scoring for Prolog-shaped semantic titles.
- `realized_core_semantics.proposals` contains the stable proposal,
  proposal-governance, and supplement-depth vocabulary shared across domains.
- `realized_core_semantics.semantic_text` contains deterministic semantic-text
  normalization and decomposition helpers.
- `realized_core_semantics.title_semantics` contains deterministic title-depth,
  namespace, and identity derivation over semantic and Prolog-shaped titles.
- `realized_core_semantics.transformation_constructs` contains transformation-
  construct candidate values and deterministic projection from itemized values.
- `realized_core_semantics.values` contains dependency-light timestamp and
  JSON-compatible value projection helpers.

Historical root imports remain exact, one-way module aliases while external
consumers migrate. Canonical repository code imports the package modules above.
