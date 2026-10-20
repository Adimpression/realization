# Architecture Boundary Controls

This directory contains only the live controls and current snapshots used to
measure the repository's architectural boundaries. Historical migration logs,
screenshots, cloud responses, and one-off completion narratives do not belong
here.

## Contents

- `boundaries.toml` declares every UV workspace component, its owner layer, its
  public module prefix, and its permitted project dependencies.
- `dependency-baseline.json` is the current machine-readable import-graph
  snapshot used by the architecture ratchet.
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
- Canonical package dependencies are declared and acyclic.
- The combined root-module and package graph has no cyclic strongly connected
  components.
- Existing dependency exceptions can only shrink; a removed exception cannot
  be reintroduced without failing the ratchet.
- Compatibility aliases are explicit, measured separately, and cannot expand
  silently.
- Contract packages remain dependency-light, the shared `workstation`
  namespace remains inert, and UI adapters depend on supported contracts rather
  than runtime implementation details.

## Architecture Check

Run the read-only check with:

```sh
python3 scripts/check_architecture_boundaries.py
```

After an intentional, reviewed architecture change, refresh both current graph
artifacts explicitly:

```sh
python3 scripts/check_architecture_boundaries.py --update-baseline --write-report
```

A normal check never rewrites the baseline. Both generated files must be
reviewed with the code change.

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
