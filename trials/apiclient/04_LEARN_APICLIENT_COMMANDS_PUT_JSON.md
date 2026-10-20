# API Client Commands 04 — Put Json Body

This document teaches the bounded Python capability of replacing a resource with
a JSON body.

## 1. Core capability

When a user wants a full update sent to an API resource, the reusable
capability is HTTP PUT JSON submission by URL and JSON text.

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
        method="PUT",
    )
    with urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the resource URL to replace
* `json_text`: the JSON text to send

Output:

* status, status code, the URL, and the parsed JSON response

## 4. Natural-language paraphrases

* put the JSON text `{"status":"active"}` to `https://api.example.com/users/42`
* send a PUT request with JSON
* replace one resource through an API

## 5. One-sentence summary

Putting a JSON body by URL and JSON text is a reusable Python API replacement
capability.
