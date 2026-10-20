# Device User Capabilities 07 — Reveal File In Finder

This document teaches a bounded device capability for revealing a specific file
in Finder on macOS.

## 1. Core capability

When a user wants to see where a file lives rather than open the file itself,
the reusable capability is file reveal in the file manager from a governed
mount.

The concrete macOS command is:

```bash
open -R "/Users/example/Downloads/archive.zip"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(mount: str, relative_path: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `broker_request` from `python_skill_host`
* call `broker_request("fs.read_mount", mount=mount, relative_path=relative_path)` to resolve the governed file target
* then call `broker_request("macos.reveal_in_finder", path=result["path"])`
* return `{"status": "revealed", "mount": mount, "relative_path": relative_path, "app": "Finder"}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Input:

* `mount`: the governed mount that contains the file
* `relative_path`: the file path inside that mount

Output:

* confirmation that Finder revealed the file
* the result dictionary contains `status`, `mount`, `relative_path`, and `app`

## 4. Natural-language paraphrases

* reveal `README.md` from mount `skill_input` in Finder
* show where `docs/report.csv` is located inside a governed mount
* highlight a mounted file in the file manager
* reveal a chosen mounted file in Finder

## 5. One-sentence summary

Revealing a file in Finder is a reusable capability for location-first file
navigation.
