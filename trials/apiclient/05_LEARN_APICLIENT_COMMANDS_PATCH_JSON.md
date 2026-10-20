# API Client Commands 05 — Patch Json Body

This document teaches the bounded Python capability of partially updating a
resource with JSON.

## 1. Core capability

When a user wants a partial change sent to an API resource, the reusable
capability is HTTP PATCH JSON submission by URL and JSON text.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    json_text: str,
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    from urllib.request import Request, urlopen

    request = Request(
        url,
        data=json_text.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the resource URL to patch
* `json_text`: the partial JSON text to send

Output:

* status, status code, the URL, and the parsed JSON response

## 4. Natural-language paraphrases

* patch `https://api.example.com/users/42` with the JSON text `{"nickname":"ace"}`
* send a PATCH request with JSON
* partially update a resource through an API

## 5. One-sentence summary

Patching a JSON body by URL and JSON text is a reusable Python API partial
update capability.
