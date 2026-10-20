# API Client Commands 09 — Get Paginated Json

This document teaches the bounded Python capability of fetching paginated JSON
results.

## 1. Core capability

When a user wants one page of paginated API results, the reusable capability is
GET JSON by URL, page number, and page size.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    page: int,
    per_page: int,
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    from urllib.parse import urlencode
    from urllib.request import urlopen

    full_url = f"{url}?{urlencode({'page': page, 'per_page': per_page})}"
    with urlopen(full_url) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status_code = response.status
    return {"status": "ok", "url": full_url, "status_code": status_code, "payload": payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the base endpoint URL
* `page`: the desired page number
* `per_page`: the page size

Output:

* status, the full URL, status code, and the parsed JSON payload

## 4. Natural-language paraphrases

* fetch page `2` with page size `50` from `https://api.example.com/items`
* make a paginated API request
* retrieve one page of JSON results

## 5. One-sentence summary

Fetching paginated JSON results is a reusable Python API paging capability.
