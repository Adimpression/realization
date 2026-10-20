# API Client Commands 07 — Get Json With Bearer Token

This document teaches the bounded Python capability of fetching JSON from an API
that requires a bearer token.

## 1. Core capability

When a user wants authenticated JSON retrieval, the reusable capability is GET
JSON by URL and bearer token.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    token: str,
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    from urllib.request import Request, urlopen

    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    with urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the authenticated endpoint URL
* `token`: the bearer token

Output:

* status, status code, the URL, and the parsed JSON payload

## 4. Natural-language paraphrases

* fetch JSON from `https://api.example.com/profile` using the bearer token `secret-token`
* make an authenticated GET request with a bearer token
* retrieve protected JSON API data

## 5. One-sentence summary

Fetching JSON with a bearer token is a reusable Python authenticated API
retrieval capability.
