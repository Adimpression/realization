# API Client Commands 03 — Post Json Body

This document teaches the bounded Python capability of posting a JSON body to an
endpoint.

## 1. Core capability

When a user wants structured data sent to an API for creation or processing, the
reusable capability is HTTP POST JSON submission by URL and JSON text.

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
        method="POST",
    )
    with urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the endpoint that accepts POST requests
* `json_text`: the JSON text to send

Output:

* status, status code, the URL, and the parsed JSON response

## 4. Natural-language paraphrases

* post the JSON text `{"name":"Ada","role":"admin"}` to `https://api.example.com/users`
* send a JSON POST request
* create an API resource using JSON

## 5. One-sentence summary

Posting a JSON body by URL and JSON text is a reusable Python API creation
capability.
