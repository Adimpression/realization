# API Client Commands 08 — Get Json With Custom Headers

This document teaches the bounded Python capability of fetching JSON from an API
with custom headers.

## 1. Core capability

When a user wants request metadata sent as headers, the reusable capability is
GET JSON by URL and header mapping.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    headers: dict[str, str],
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    from urllib.request import Request, urlopen

    request = Request(url, headers=headers)
    with urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the endpoint URL
* `headers`: the headers to attach

Output:

* status, status code, the URL, and the parsed JSON payload

## 4. Natural-language paraphrases

* fetch JSON from `https://api.example.com/items` with the header `X-Trace-Id: abc-123`
* make a GET request with custom headers
* retrieve JSON from an API with explicit request metadata

## 5. One-sentence summary

Fetching JSON with custom headers is a reusable Python API request-shaping
capability.
