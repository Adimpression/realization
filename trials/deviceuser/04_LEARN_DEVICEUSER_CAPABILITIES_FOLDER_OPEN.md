# Device User Capabilities 04 — Open Folder In Finder

This document teaches a bounded device capability for opening a folder in
Finder on macOS.

## 1. Core capability

When a user wants to browse a directory visually, the reusable capability is
folder-open in the file manager from a governed mount.

The concrete macOS command is:

```bash
open "/Users/example/Downloads"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(mount: str, relative_path: str = "", *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `broker_request` from `python_skill_host`
* call `broker_request("fs.list_mount", mount=mount, relative_path=relative_path)` to resolve the governed folder target
* then call `broker_request("macos.open_folder", folder=result["path"])`
* return `{"status": "opened", "mount": mount, "relative_path": relative_path, "app": "Finder"}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Input:

* `mount`: the governed mount that contains the folder
* `relative_path`: the directory path inside that mount

Output:

* confirmation that Finder opened the folder
* the result dictionary contains `status`, `mount`, `relative_path`, and `app`

## 4. Natural-language paraphrases

* open mount `skill_input` at `trials`
* show `tests` from mount `skill_input` in Finder
* open a mounted directory in the file manager
* show a specific mounted folder in Finder

## 5. One-sentence summary

Opening a folder in Finder is the reusable visual-browsing capability for local
directories.
