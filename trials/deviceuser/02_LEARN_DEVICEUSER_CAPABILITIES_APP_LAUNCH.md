# Device User Capabilities 02 — Launch Application By Name

This document teaches a bounded device capability for launching an application
by its visible app name on macOS.

## 1. Core capability

When a user wants a specific app to start, the reusable capability is
application launch by name.

The concrete macOS command is:

```bash
open -a "TextEdit"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(app: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `subprocess`
* run `subprocess.run(["open", "-a", app], check=True)`
* return `{"status": "launched", "app": app}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Input:

* `app`: the app name, such as `Notes`, `TextEdit`, or `Calculator`

Output:

* launch result naming the app that was started
* the result dictionary contains `status` and `app`

## 4. Natural-language paraphrases

* launch Notes
* open Calculator
* start TextEdit
* launch an application by visible name

## 5. One-sentence summary

Launching an application by name is the reusable substrate behind many simple
device actions.
