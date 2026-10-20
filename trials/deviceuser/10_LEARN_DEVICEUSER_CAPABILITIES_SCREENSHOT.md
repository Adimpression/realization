# Device User Capabilities 10 — Capture Screenshot To File

This document teaches a bounded device capability for saving a screenshot to a
file on macOS.

## 1. Core capability

When a user wants a visual snapshot of the current screen state, the reusable
capability is screenshot capture with governed output targeting.

The concrete macOS command is:

```bash
screencapture "/Users/example/Desktop/screen.png"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(mount: str, relative_path: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `broker_request` from `python_skill_host`
* call `broker_request("fs.write_mount", mount=mount, relative_path=relative_path, text="")` to prepare the governed output target
* then call `broker_request("macos.capture_screenshot", path=result["path"])`
* return `{"status": "captured", "mount": mount, "relative_path": relative_path}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Input:

* `mount`: the governed mount that should receive the screenshot
* `relative_path`: the output file path inside that mount

Output:

* confirmation that the screenshot was written to the target
* the result dictionary contains `status`, `mount`, and `relative_path`

## 4. Natural-language paraphrases

* take a screenshot and save it to mount `skill_tmp` at `deviceuser-screen.png`
* capture the current screen to a governed output target
* save a screenshot at a chosen mounted path
* capture the current screen into a chosen mount-relative file path

## 5. One-sentence summary

Screenshot capture is a reusable capability for turning current visual device
state into a file artifact.
