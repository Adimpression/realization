# Realized Skill Semantics

`realized-skill-semantics` owns the dependency-light semantic substrate shared
by portable Realized skills. It represents canonical skill IR values, portable
skill identity metadata, invocation request/result records, typed
region-preserving leaves, their reconstructible canonical paths, and
deterministic boundary-normalization documents over explicit values. It owns
supported portable declaration schema versions and deterministic projection of
explicit composition rights into target titles. It owns the portable executor
descriptor vocabulary and deterministic inference of a descriptor and its
executable body from already-declared ability content. A descriptor states
what an ability requires; it does not establish that a host provides that
executor. The package also owns immutable composition-plan and static-analysis
result values, but not the analysis or execution algorithms yet. It does not
parse or validate declaration payloads, admit or approve skills, grant
authority, bind host realizers, execute effects, persist state, or plan a
workstation interaction.

The public surface is intentionally split into eight explicit modules:

- `realized_skill_semantics.composition` contains immutable mapper, binding,
  condition, step, candidate, diagnostic, and plan-analysis records.
- `realized_skill_semantics.declaration` contains supported portable skill
  schema versions, schema-version normalization, and explicit
  composition-right target projection.
- `realized_skill_semantics.execution` contains the portable executor
  descriptor vocabulary, alias normalization, content-field mapping, and
  deterministic descriptor/body inference. It contains no host support,
  provider registration, prerequisite, dispatch, or effect behavior.
- `realized_skill_semantics.invocation` contains immutable invocation binding,
  request, and result records plus deterministic required-input and terminal
  result normalization.
- `realized_skill_semantics.ir` contains the immutable canonical IR value and
  deterministic alias/family identity normalization.
- `realized_skill_semantics.leaves` contains leaf values, region
  normalization, type normalization, and value/reference carrier derivation.
- `realized_skill_semantics.paths` contains canonical path escaping, rendering,
  and parsing.
- `realized_skill_semantics.normalization` contains deterministic flattening,
  reconstruction, payload validation, and synthesis from explicit boundary
  values.

Historical root imports remain compatibility aliases while consumers migrate.
The root governance adapter still parses and validates declaration and policy
payloads, synthesizes declarations from artifacts, and makes admission
decisions while re-exporting the portable declaration symbols by exact
identity.
The workstation invocation adapter still projects artifact, runtime
declaration, and executor information into the portable invocation records.
The root IR adapter still constructs the package value from artifact,
governance, lifecycle, compatibility, and runtime projections.
The root executor primitive retains host-advertised support normalization; the
root execution adapter retains learning, provider, prerequisite, dispatch, and
effect behavior while re-exporting portable descriptors by exact identity.
The root composition module still owns artifact projection, proposal and plan
analysis, mapper execution, iteration, runtime events, and invoker calls while
re-exporting the portable composition records by exact identity.
The root artifact adapter still combines artifact fields with a governance
declaration before calling this package; that extraction is deliberately not a
portable semantic responsibility. New code should import the canonical modules
above when it already has explicit values.
