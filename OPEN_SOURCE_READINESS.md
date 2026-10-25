# Open Source Readiness

## Status

The project is not yet approved for public release. Content classification,
source staging, provenance verification, secret scanning, and public metadata
for the six standalone core distributions are in place. Final candidate
qualification, Cloud Build integration, and tagging remain. This preparation
does not change runtime behavior, package boundaries, persisted formats, or
current local operations.

Run the read-only audit with:

```bash
python3 scripts/check_open_source_readiness.py
```

The audit intentionally fails against an active development checkout when
local configuration or runtime state is present. Run it again against the exact
staged release directory before publication.

## Completed Quick Wins

- Contribution, security, and conduct expectations are documented.
- Credential-free `local.env.example` and `offline.env.example` templates are
  available without replacing the operational environment files.
- A dependency-free readiness audit detects missing release documents, local
  configuration, common runtime artifacts, synchronization-conflict files, and
  non-empty secret fields in environment examples.
- macOS metadata is ignored for future changes.
- `RELEASE_CONTENT.md` and `release/release-content.toml` classify maintained
  source, reviewed fixtures, generated code, tool scaffolding, dependency
  metadata, captured reports, generated corpora, and local state.
- `scripts/build_release_export.py` produces a deterministic staged tree and a
  per-file SHA-256, mode, license, category, and provenance manifest.
- `scripts/check_release_provenance.py` verifies the manifest, classifications,
  third-party notices, and public core-package metadata.
- The public Git history was scanned with pinned Gitleaks 8.30.1 on 2026-10-20.
  It scanned the imported commit and approximately 155 MB without findings.
- The `realized-core`, `realized-core-conversation`, `realized-core-engine`,
  `realized-core-llm`, `realized-core-runtime`, and `realized-host-interaction`
  projects declare authorship,
  maintenance contact, Apache-2.0 licensing, classifiers, keywords, and public
  project URLs, and package the license text.

## Release Blockers

- Regenerate the staged directory from the exact clean candidate commit and
  rerun provenance, readiness, and pinned Gitleaks scans against that stage.
- Build and inspect source distributions and wheels, then verify the local
  wheel and eventual index-backed `uvx` journeys from fresh environments.
- Run all deterministic Cloud Build gates from the exact candidate commit, then
  separately record provider-backed and UI qualification.
- Add the release readiness and provenance checks to Google Cloud Build before
  creating the alpha tag.

## Publication Invariants

- A public snapshot must not alter the behavior of the private operational
  checkout used to prepare it.
- The release must distinguish implemented behavior, verified behavior,
  experimental behavior, and theory.
- Host operations, authority, ability admission, semantic matching, and
  dispatch must remain separate in both documentation and code.
- The release must include enough deterministic fixtures to reproduce the
  claimed core behavior without private services or credentials.
- No generated artifact may be treated as source merely because it is already
  checked in.

## Completed Owner Decisions

- Source is licensed under Apache License 2.0 through the canonical
  `LICENSE` text.
- Private vulnerability and conduct reports use the address published in
  `SECURITY.md`.

## Initial Release Shape

The safest first tag is a pre-1.0 research release from a clean repository that
contains only reviewed content from this folder. It should expose one complete
offline path through the governed core and SQLite, explain the workspace
boundaries, and label workstation/provider surfaces according to their actual
qualification status.

The staged snapshot is intentionally narrower than the development checkout.
Captured `reports/`, generated corpora, local state, and the unresolved Gradle
wrapper binary are not release payload. Reviewed trial definitions and compiled
trial bundles remain because deterministic tests consume them directly.
