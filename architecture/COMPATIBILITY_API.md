# Compatibility API

`realized-compatibility` preserves historical top-level Python imports that
have positive serialized-identity, stored-source, provider-boundary, or command
compatibility obligations. It is an outer compatibility distribution, not a
canonical implementation layer.

## Contract

- Canonical packages remain the sole owners of product behavior.
- Historical imports preserve the object identities and adapter behavior
  captured by `architecture/compatibility-facade-contracts.json`.
- Protocol-zero pickle globals recorded by that ledger remain resolvable.
- `realized-compatibility` and `python -m main` preserve the historical
  aggregate command composition.
- `python -m fence_extraction_strategy` and `realized-fence-extraction`
  preserve the fence-strategy command surface.
- New product code, examples, and public onboarding must import canonical APIs,
  not compatibility modules.
- Compatibility support is reviewed at every compatibility package release.
  Removal requires an explicit deprecation window, migration guidance, a
  stable qualification cycle, and a tombstone.

The current ledger classifies every retained compatibility import as an
explicitly supported ABI. Supported status is a deliberate terminal contract,
not an unresolved retirement hold. Compatibility sources are isolated from the
repository root and canonical packages do not consume them.

## Evidence

The supported module list is declared in `architecture/boundaries.toml` and
`architecture/compatibility-facade-policy.json`. Identity, pickle, consumer,
distribution-isolation, and retirement-state checks are enforced by:

- `tests/test_architecture_compatibility_facades.py`
- `tests/test_compatibility_facade_contracts.py`
- `tests/test_compatibility_facade_inventory.py`
- `scripts/verify_workspace_distributions.py`
