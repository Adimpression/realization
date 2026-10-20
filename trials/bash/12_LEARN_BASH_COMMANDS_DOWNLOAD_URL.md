# Bash Commands 12 — Download Url To File

This document teaches the bounded shell capability of downloading content from a
URL into a local file.

## 1. Core capability

When a user wants to fetch remote content and save it locally, the reusable
capability is URL download by source URL and destination path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
mkdir -p "$(dirname "$destination")"
curl -L "$url" -o "$destination"
```

The named shell parameters are `$url` and `$destination`.

## 3. Inputs and outputs

Inputs:

* `url`: the remote resource to download
* `destination`: the local output file path

Output:

* downloaded file at the destination path

## 4. Natural-language paraphrases

* download `https://example.com` to `/tmp/example.html`
* fetch `https://example.org/data.json` into `/tmp/data.json`
* save a URL response into a file

## 5. One-sentence summary

Downloading a URL into a file is a reusable shell fetch capability.
