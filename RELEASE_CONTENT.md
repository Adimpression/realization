# Release Content And Redistribution

This document defines the source content eligible for the initial public
Realization release. It is a redistribution classification, not a claim that
every checked-in file is authored source or that every experimental result is
portable evidence.

The machine-readable policy is
[`release/release-content.toml`](release/release-content.toml). The staged
source tree and its `release-manifest.json` are produced by
[`scripts/build_release_export.py`](scripts/build_release_export.py).

## Included Classes

| Class | Included material | Treatment |
| --- | --- | --- |
| Project source | Maintained Python, Dart, platform, infrastructure, schemas, and documentation | Redistributed under Apache-2.0 to the extent the maintainer can license it |
| Deterministic fixtures | Test fixtures, BDD material, authored trial inputs, and reviewed trial ability bundles | Included for reproducibility; not represented as production data or independently validated knowledge |
| Generated project source | Protobuf/gRPC bindings derived from checked-in project `.proto` files | Included because the generated bindings are required to use the checked-in interface |
| Tool-generated scaffold | Flutter platform scaffold, registrants, launcher assets, and metadata tied to the revision recorded in `workstation/ui_flutter/.metadata` | Included with upstream origin disclosed in `THIRD_PARTY_NOTICES.md` |
| Dependency metadata | `uv.lock`, `pubspec.lock`, Terraform lock data, and build-wrapper configuration | Included to identify resolution inputs; lock entries are not relicensed as project source |
| Maintainer-reviewed derived specification | The product self-representation generated from, then reconciled against, this codebase | Included as documentation, not as an independent conformance certificate |

## Excluded Classes

| Class | Excluded material | Reason |
| --- | --- | --- |
| Captured runtime output | `reports/` | Contains timestamped runs, local paths, copied workspace listings, archives, and model or tool output; it is neither source nor a portable baseline |
| Generated runtime corpus | `corpus/`, `trials/corpus/`, and domain `trials/*/corpus/` trees | Contains machine-produced learning state and projections that can be regenerated from reviewed inputs |
| Generated trial reports | `trials/reports/` | Runtime evidence with environment-specific state |
| Historical trial evidence | Root `trials/*_TRIAL.md`, `trials/*_TRIAL.json`, and `trials/*_TRIAL_CONCLUSION.MD` results | One-off run narratives and payloads refer to excluded reports, stale source locations, and historical implementation line numbers; authored trial inputs, validators, and compiled ability bundles remain included |
| Historical architecture captures | `architecture/baselines/` | Superseded, dated qualification evidence rather than live architecture controls |
| Local editor state | `*.code-workspace` | Machine-specific convenience configuration |
| Unverified third-party binary | `workstation/ui_flutter/android/gradle/wrapper/gradle-wrapper.jar` | The checked-in binary does not carry enough provenance to reconcile its embedded version with the configured Gradle distribution; regenerate it from a verified Gradle distribution before binary release |
| Local or transient state | Credentials, non-example environment files, databases, caches, virtual environments, build products, and synchronization-conflict files | Must never enter a staged source release |

Exclusion from the staged snapshot does not erase a file from Git history or
revoke a credential. History is scanned separately before publication.

## Authorship And Model Assistance

The standalone public repository began as a maintainer-controlled import from
the project's private development checkout. Its initial public commit does not
preserve the private repository's granular authorship history. The maintainer
therefore attests to the redistribution classification at the repository level
rather than presenting the public Git history as complete provenance.

Some maintained material may have been produced with model assistance and then
reviewed or revised by the maintainer. It is classified by its maintained role,
not represented as an independently authored third-party work, and licensed
only to the extent legally available. Unreviewed captured model output remains
excluded with other runtime reports.

No external user corpus is intentionally included in the initial staged
release. Examples that resemble people, organizations, endpoints, or scenarios
are synthetic fixtures unless a file states otherwise.

## Dependency And Embedded Material

Python and Dart dependencies are resolved externally from their respective
lock files and retain their own licenses. The repository does not vendor those
installed distributions. Flutter template material and generated protocol
bindings are identified in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
Binary distributors must collect the license texts and notices for the exact
dependency set and platform artifacts they redistribute.

## Building The Stage

The default command requires a clean Git worktree and uses tracked files only:

```console
python3 scripts/build_release_export.py --output /tmp/realization-release
```

During release preparation only, a dirty preview can include untracked files:

```console
python3 scripts/build_release_export.py \
  --output /tmp/realization-release-preview \
  --allow-dirty \
  --include-untracked
```

Verify the resulting content and provenance:

```console
python3 scripts/check_release_provenance.py /tmp/realization-release
python3 scripts/check_open_source_readiness.py /tmp/realization-release
```

The manifest records the source commit, worktree state, policy digest, file
mode, size, SHA-256 digest, category, provenance identifier, and license for
every included payload file. A final release candidate must be regenerated
from a clean commit; a dirty preview is not publishable.

## Secret Scanning

The pinned scanner and commands are recorded in
[`release/tooling.toml`](release/tooling.toml). Scan both histories and the
exact staged tree. Findings must be investigated before release; excluding a
file from the stage is not sufficient if its secret appeared in published
history.
