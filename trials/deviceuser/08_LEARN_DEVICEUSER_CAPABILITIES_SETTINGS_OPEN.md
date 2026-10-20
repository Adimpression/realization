# Device User Capabilities 08 — Open System Settings Pane

This document teaches a bounded device capability for opening a specific System
Settings pane on macOS.

## 1. Core capability

When a user wants to jump directly to a settings area, the reusable capability
is settings launch with pane targeting.

One concrete macOS command is:

```bash
open "x-apple.systempreferences:com.apple.Network-Settings.extension"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(settings_url: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `subprocess`
* run `subprocess.run(["open", settings_url], check=True)`
* return `{"status": "opened", "settings_url": settings_url}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Input:

* `settings_url`: the deep-link URL for the target settings pane

Output:

* confirmation that the settings pane was opened
* the result dictionary contains `status` and `settings_url`

## 4. Natural-language paraphrases

* open Wi-Fi settings
* launch the Network settings pane
* jump to a specific System Settings section
* open a specific System Settings pane from a deep-link URL

## 5. One-sentence summary

Opening a specific settings pane is a reusable device capability for targeted
system configuration.
