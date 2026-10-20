# Device User Capabilities 01 — Launch Browser At Specific URL

This document teaches a bounded device capability for opening a browser at a
specific URL on macOS.

## 1. Core capability

When a user wants a browser to open at a known destination, the reusable
capability is browser launch with URL targeting.

The concrete macOS command is:

`open -a "Google Chrome" "https://example.com"`

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function is:

```python
def main(
    url: str,
    *,
    browser: str = "Google Chrome",
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    import subprocess

    subprocess.run(["open", "-a", browser, url], check=True)
    return {"status": "opened", "browser": browser, "url": url}
```

The function name is `main`.

The signature is
`main(url: str, *, browser: str = "Google Chrome", __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `subprocess`
* run `subprocess.run(["open", "-a", browser, url], check=True)`
* return `{"status": "opened", "browser": browser, "url": url}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Inputs:

* `url`: the target web address
* `browser`: the browser application name

Output:

* launch result confirming which browser opened which URL
* the result dictionary contains `status`, `browser`, and `url`

## 4. Natural-language paraphrases

These all ask for the same capability:

* open Google Chrome to `https://example.com`
* launch Safari at `https://news.ycombinator.com`
* start a browser on a specific web page
* open a browser at a specified URL

## 5. One-sentence summary

Launching a browser at a specific URL is a reusable device capability that
binds an application name and a destination URL into one open command.
