# API Client Commands 02 — Get Json With Query Parameters

This document teaches the bounded Python capability of fetching JSON from an
endpoint with query parameters.

## 1. Core capability

When a user wants JSON data constrained by query values, the reusable
capability is GET JSON retrieval by base URL and query mapping.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    query: dict[str, str],
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    from urllib.parse import urlencode
    from urllib.request import urlopen

    full_url = f"{url}?{urlencode(query)}"
    with urlopen(full_url) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": full_url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the base endpoint URL
* `query`: the query parameters to encode

Output:

* status, the full URL, status code, and the parsed JSON payload

## 4. Natural-language paraphrases

* fetch JSON from `https://api.example.com/search` with query `q=widgets` and `limit=10`
* make a GET request with query parameters
* retrieve filtered JSON results from an API

## 5. One-sentence summary

Fetching JSON with query parameters is a reusable Python API filtering
capability.
