# Device User Capabilities 09 — Copy Text To Clipboard

This document teaches a bounded device capability for copying text into the
system clipboard on macOS.

## 1. Core capability

When a user wants text to be available for a later paste action, the reusable
capability is clipboard write.

The concrete macOS command is conceptually:

```bash
printf "hello world" | pbcopy
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(text: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `subprocess`
* run `subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)`
* return `{"status": "copied", "text": text}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Input:

* `text`: the text to copy

Output:

* confirmation that the clipboard now holds the text
* the result dictionary contains `status` and `text`

## 4. Natural-language paraphrases

* copy `hello world` to the clipboard
* put this text in the clipboard
* write a string into the system clipboard
* copy supplied text into the macOS clipboard

## 5. One-sentence summary

Clipboard copy is a reusable capability for moving text into the device’s
pasteable temporary memory.
