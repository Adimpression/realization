# Architecture Boundary Controls

This directory contains only the live controls and current snapshots used to
measure the repository's architectural boundaries. Historical migration logs,
screenshots, cloud responses, and one-off completion narratives do not belong
here.

## Contents

- `boundaries.toml` declares every UV workspace component, its owner layer, its
  public module prefix, and its permitted project dependencies. It also assigns
  every repository-root Python module and top-level Python package family to one
  responsibility, records orthogonal entrypoint/validation/compatibility
  status, and declares the acyclic target direction between those
  responsibilities.
- `dependency-baseline.json` is the current machine-readable import-graph
  snapshot used by the architecture ratchet.
- `compatibility-facades.json` is the deterministic ledger of every retained
  repository-root compatibility facade, its canonical targets, and every
  static repository consumer. It also records public README/example references
  and the qualification hold that applies before retirement.
- `compatibility-facade-contracts.json` is the executable retirement-card
  ledger. It freezes module identity, exports, callable signatures, constants,
  command replacements, and every protocol-zero pickle global exercised by the
  compatibility contract suite.
- `compatibility-facade-policy.json` contains human retirement decisions and
  tombstones separately from generated observations and contracts.
- `remaining-architecture-obligations.toml` records every unresolved forbidden
  root-owner edge and every supported package compatibility ABI, including its
  canonical owner, evidence, review condition, and rollback boundary.
- `DEPENDENCY_REPORT.md` is the deterministic human-readable rendering of that
  snapshot. Tests require it to match the measured graph.
- `qualification-gates.toml` declares the behavioral, packaging, UI, and
  provider-backed gates used to qualify boundary changes.
- `qualification-baseline.json` is the current comparison baseline produced by
  those gates.

The product architecture itself is documented in `6-LAYER_ARCHITECTURE.md` and
the component ownership map in `MODULES.md`. This directory is the enforcement
surface, not a migration diary.

## Enforced Invariants

- Every member of `[tool.uv.workspace].members` is registered in
  `boundaries.toml`.
- Every repository-root Python module and top-level Python package family has
  exactly one explicit owner; missing, duplicate, stale, or silently changed
  ownership fails the ratchet.
- Root compatibility facades remain attributable to their behavioral owner,
  and package code may not import those facades even through a refreshed
  baseline.
- The responsibility-level target graph is acyclic, while current violations
  are retained only as a shrinking baseline.
- Canonical package dependencies are declared and acyclic.
- The combined root-module, top-level package-family, and UV workspace graph has
  no cyclic strongly connected components.
- Existing dependency exceptions can only shrink; a removed exception cannot
  be reintroduced without failing the ratchet.
- Compatibility aliases are explicit, measured separately, and cannot expand
  silently. Supported package aliases live in the dedicated compatibility
  distribution and are counted as declared edges of that distribution rather
  than dependencies between canonical components.
- Canonical package code, public README examples, and repository examples may
  not import a root compatibility facade.
- A compatibility facade is treated as a supported historical import until it
  is explicitly classified otherwise. Removal requires a separate change,
  documented notice where externally supported, and at least one complete
  stable qualification cycle after the final consumer migration.
- Contract packages remain dependency-light, the shared `workstation`
  namespace remains inert, and UI adapters depend on supported contracts rather
  than runtime implementation details.
- Every supported compatibility module is imported from the assembled wheels
  by the distribution-isolation gate in addition to the component's primary
  public module.

## Architecture Check

Run the read-only check with:

```sh
python3 scripts/check_architecture_boundaries.py
python3 scripts/check_compatibility_facades.py
python3 scripts/capture_compatibility_facade_contracts.py
python3 scripts/verify_workspace_distributions.py
```

After an intentional, reviewed architecture change, refresh both current graph
artifacts explicitly:

```sh
python3 scripts/check_architecture_boundaries.py --update-baseline --write-report
python3 scripts/check_compatibility_facades.py --update
python3 scripts/capture_compatibility_facade_contracts.py --update
```

A normal check never rewrites either baseline. All generated files must be
reviewed with the code change. Updating the compatibility inventory records
observed consumers; it does not authorize a facade removal.

## Behavioral Qualification

Run the default qualification ladder with:

```sh
python3 scripts/capture_qualification_baseline.py
```

Provider-backed and browser gates are opt-in because they require credentials,
external capacity, or local desktop services. Run the full declared ladder with
`--include-manual`. Use `--compare-to architecture/qualification-baseline.json`
when qualifying a candidate without replacing the accepted baseline, and use
`--repeat 3` before changing a performance-sensitive boundary.
