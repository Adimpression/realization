# Realized Core Semantics

`realized-core-semantics` owns the dependency-light formal theory values and
read-only semantic contracts shared by Realized domains. Its theory models are
structural values; they do not admit artifacts, choose abilities, grant
authority, execute effects, call model providers, or persist application state.

The public surface is intentionally split into three explicit modules:

- `realized_core_semantics.theory` contains the Pydantic formal-system model.
- `realized_core_semantics.artifacts` contains narrow read protocols for
  artifact consumers.
- `realized_core_semantics.values` contains dependency-light timestamp and
  JSON-compatible value projection helpers.

Historical root imports remain one-way compatibility facades while consumers
migrate. New code should import the canonical modules above.
