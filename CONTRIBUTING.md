# Contributing to Realized

Realized is a pre-1.0 research system with behaviorally significant persisted
artifacts, architecture boundaries, and deterministic qualification paths.
Changes must preserve those contracts unless a change explicitly migrates and
tests them.

## Development Setup

Python 3.14 and `uv` are required.

```bash
uv sync --frozen
```

Use the checked-in workspace and lock file. Do not add undeclared import paths
or install dependencies directly into a workspace package.

## Change Discipline

- Keep each change within one cohesive architectural responsibility.
- Preserve public package APIs, persisted schemas, receipts, event ordering,
  report artifacts, and user-visible workflow behavior unless the change is an
  explicit migration.
- Add or update focused tests for every behavioral change.
- Do not combine boundary movement with behavior changes.
- Keep compatibility paths until repository-wide searches and qualification
  prove that consumers have moved.
- Treat theory documents as claims that must remain distinguishable from
  implemented and verified behavior.

The intended dependency directions are defined by
`architecture/boundaries.toml` and explained in `6-LAYER_ARCHITECTURE.md`.

## Verification

Run the narrowest relevant tests first, then the architecture ratchet:

```bash
uv run --frozen python scripts/check_architecture_boundaries.py
uv run --frozen python -m unittest tests.test_architecture_boundaries
```

For changes that affect the governed runtime, workstation, or publication
flow, run the corresponding unit and BDD modules listed in `cloudbuild.yaml`.
Provider-backed and desktop/browser qualification must be reported separately;
they are not substitutes for deterministic tests.

## Workspace Cleanup

Preview generated caches and build products that can be removed safely:

```bash
python3 scripts/clean_workspace.py
```

Apply that cleanup with `--apply`. Dependency environments are preserved unless
`--include-environments` is also supplied. The command never traverses
`reports/`, `corpus/`, `ram/`, `state/`, or `tmp/`, and it refuses to remove
tracked content.

## Sensitive and Generated Material

- Never commit credentials, tokens, passwords, private keys, personal paths,
  local databases, or captured private source material.
- Start local configuration from `local.env.example` or
  `offline.env.example`.
- Keep local runtime state under ignored `state/`, `ram/`, or `tmp/` paths.
- Do not commit generated validation output unless it is an intentional,
  reviewed baseline with documented provenance.

## Submitting a Change

Describe the responsibility being changed, the preserved invariants, the tests
run, and any qualification that could not be run. Security reports must follow
`SECURITY.md` rather than a public issue.
