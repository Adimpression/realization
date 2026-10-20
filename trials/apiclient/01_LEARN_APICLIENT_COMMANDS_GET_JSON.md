# API Client Commands 01 — Get Json From Url

This document teaches the bounded Python capability of fetching JSON from a URL.

## 1. Core capability

When a user wants structured JSON data from one endpoint, the reusable
capability is HTTP GET JSON retrieval by URL.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(url: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:
    import json
    from urllib.request import urlopen

    with urlopen(url) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Input:

* `url`: the endpoint that returns JSON

Output:

* status, status code, the URL, and the parsed JSON payload

## 4. Natural-language paraphrases

* fetch JSON from `https://api.example.com/items/42`
* make a GET request and parse JSON
* retrieve one JSON API response

## 5. One-sentence summary

Fetching JSON from a URL is a reusable Python API retrieval capability.
