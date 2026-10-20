# Device User Capabilities 05 — Open Terminal At Directory

This document teaches a bounded device capability for opening Terminal at a
specific directory on macOS.

## 1. Core capability

When a user wants shell work to begin from a chosen location, the reusable
capability is terminal launch with directory targeting from a governed mount.

The concrete macOS command is:

```bash
open -a "Terminal" "/Users/example/projects"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(mount: str, relative_path: str = "", *, terminal_app: str = "Terminal", __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `broker_request` from `python_skill_host`
* call `broker_request("fs.list_mount", mount=mount, relative_path=relative_path)` to resolve the governed folder target
* then call `broker_request("macos.open_file", path=result["path"], application=terminal_app)`
* return `{"status": "opened", "terminal_app": terminal_app, "mount": mount, "relative_path": relative_path}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Inputs:

* `mount`: the governed mount that contains the directory
* `relative_path`: the directory path inside that mount
* `terminal_app`: the terminal application name

Output:

* confirmation that the terminal app opened at the requested folder
* the result dictionary contains `status`, `terminal_app`, `mount`, and `relative_path`

## 4. Natural-language paraphrases

* open Terminal in mount `skill_input` at `.`
* launch a shell window at `trials` from mount `skill_input`
* start Terminal at a mounted directory
* open a terminal app at a chosen mounted folder

## 5. One-sentence summary

Opening Terminal at a directory is a reusable capability for starting command
work in the right filesystem context.
