# API Client Commands 06 — Delete Resource

This document teaches the bounded Python capability of deleting an API
resource.

## 1. Core capability

When a user wants one API resource removed, the reusable capability is HTTP
DELETE by URL.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(url: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:
    from urllib.request import Request, urlopen

    request = Request(url, method="DELETE")
    with urlopen(request) as response:
        status_code = response.status
        body = response.read().decode("utf-8")
    return {"status": "ok", "url": url, "status_code": status_code, "body": body}
```

## 3. Inputs and outputs

Input:

* `url`: the resource URL to delete

Output:

* status, status code, the URL, and any returned body text

## 4. Natural-language paraphrases

* delete the resource at `https://api.example.com/users/42`
* send a DELETE request to an endpoint
* remove one resource through an API

## 5. One-sentence summary

Deleting an API resource by URL is a reusable Python API removal capability.
