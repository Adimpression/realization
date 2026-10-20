# API Client Commands 11 — Post Form Urlencoded Data

This document teaches the bounded Python capability of posting form-urlencoded
data to an API endpoint.

## 1. Core capability

When a user wants form fields sent to an API token or login endpoint, the
reusable capability is HTTP POST form submission by URL and field mapping.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    form_fields: dict[str, str],
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    request = Request(
        url,
        data=urlencode(form_fields).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request) as response:
        body = response.read().decode("utf-8")
        status_code = response.status
    try:
        payload = json.loads(body)
    except Exception:
        payload = body
    return {"status": "ok", "url": url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the endpoint that accepts form-urlencoded data
* `form_fields`: the fields to encode and send

Output:

* status, status code, the URL, and the response payload or text

## 4. Natural-language paraphrases

* post the form fields `grant_type=client_credentials&scope=read` to `https://api.example.com/token`
* send a form-urlencoded POST request
* call a token endpoint with form data

## 5. One-sentence summary

Posting form-urlencoded data is a reusable Python API authentication and form
submission capability.
