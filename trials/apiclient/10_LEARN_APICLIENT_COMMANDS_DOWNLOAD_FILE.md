# API Client Commands 10 — Download File From Url

This document teaches the bounded Python capability of downloading a file from a
URL to a destination path.

## 1. Core capability

When a user wants remote content saved locally, the reusable capability is file
download by URL and destination path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    destination: str,
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from pathlib import Path
    from urllib.request import urlopen

    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as response:
        Path(destination).write_bytes(response.read())
    return {"status": "downloaded", "url": url, "destination": destination}
```

## 3. Inputs and outputs

Inputs:

* `url`: the source file URL
* `destination`: the output path

Output:

* status, the URL, and the destination path

## 4. Natural-language paraphrases

* download `https://example.com/report.pdf` to `/tmp/report.pdf`
* fetch a remote file to local storage
* save an API file response to disk

## 5. One-sentence summary

Downloading a file from a URL is a reusable Python API transfer capability.
