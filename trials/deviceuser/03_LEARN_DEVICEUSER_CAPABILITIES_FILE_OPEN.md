# Device User Capabilities 03 — Open File In Chosen App

This document teaches a bounded device capability for opening a file in a
chosen application on macOS.

## 1. Core capability

When a user wants a specific file to open in a specific app, the reusable
capability is file-open with application targeting from a governed mount.

The concrete macOS command is:

```bash
open -a "Preview" "/Users/example/Documents/report.pdf"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(mount: str, relative_path: str, *, app: str, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `broker_request` from `python_skill_host`
* call `broker_request("fs.read_mount", mount=mount, relative_path=relative_path)` to resolve the governed file target
* then call `broker_request("macos.open_file", path=result["path"], application=app)`
* return `{"status": "opened", "app": app, "mount": mount, "relative_path": relative_path}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Inputs:

* `mount`: the governed mount that contains the file
* `relative_path`: the file path inside that mount
* `app`: the app that should open the file

Output:

* launch result confirming the file target and chosen app
* the result dictionary contains `status`, `app`, `mount`, and `relative_path`

## 4. Natural-language paraphrases

* open `README.md` from mount `skill_input` in TextEdit
* launch Preview with `docs/report.pdf` from a governed mount
* open a mounted file in a chosen application
* open a chosen mounted file in a chosen app

## 5. One-sentence summary

Opening a file in a chosen app is a reusable capability that extends simple app
launch by adding a file target.
