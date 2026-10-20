# Device User Capabilities 06 — Search The Web In Browser

This document teaches a bounded device capability for launching a browser with
a search query on macOS.

## 1. Core capability

When a user wants a browser to perform a search rather than open a fixed URL,
the reusable capability is browser launch with query encoding.

The concrete macOS command is conceptually:

```bash
open -a "Safari" "https://www.google.com/search?q=right+triangle+hypotenuse"
```

## 2. Executable Python relation

This capability is a parameterized executable template and should be learned as
an ability artifact.

The reusable function name is `main`.

The reusable function signature is
`main(query: str, *, browser: str = "Safari", __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `subprocess`
* import `urllib.parse`
* compute `encoded = urllib.parse.quote_plus(query)`
* compute `url = f"https://www.google.com/search?q={encoded}"`
* run `subprocess.run(["open", "-a", browser, url], check=True)`
* return `{"status": "opened", "browser": browser, "query": query, "url": url}`
* keep dependency metadata inline as `__dependencies__ = ()`

## 3. Inputs and outputs

Input:

* `query`: the search text

Outputs:

* the browser that was used
* the generated search URL
* the result dictionary also contains `status` and the original `query`

## 4. Natural-language paraphrases

* search the web for `best code editor for markdown`
* open Safari and search for `how to zip a folder on mac`
* launch a browser search for a given query
* perform a browser search from plain query text

## 5. One-sentence summary

Browser search is a reusable capability that transforms a natural query into a
search URL and opens it in a browser.
