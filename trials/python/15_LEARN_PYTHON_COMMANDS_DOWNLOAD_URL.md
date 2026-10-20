# Python Commands 15 — Download Url To File

This document teaches the bounded Python capability of downloading content from
a URL into a governed virtual mount.

## 1. Core capability

When a user wants remote content saved through governed broker surfaces, the
reusable capability is URL download by source URL, destination mount, and
destination relative path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    mount: str = "skill_tmp",
    relative_path: str = "example-python.html",
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from python_skill_host import broker_request

    fetched = broker_request("net.http_get_text", url=url)
    if fetched.get("status") != "ok":
        return fetched
    written = broker_request(
        "fs.write_mount",
        mount=mount,
        relative_path=relative_path,
        text=fetched.get("text", ""),
    )
    if written.get("status") != "ok":
        return written
    return {
        "status": "downloaded",
        "url": url,
        "mount": mount,
        "relative_path": relative_path,
    }
```

## 3. Inputs and outputs

Inputs:

* `url`: the remote resource to fetch
* `mount`: the governed destination mount
* `relative_path`: the destination file path inside that mount

Output:

* status, the URL, and the governed destination surface

## 4. Natural-language paraphrases

* download `https://example.com` to mount `skill_tmp` at `example-python.html`
* fetch `https://example.org/data.json` into mount `skill_output` at `api/data.json`
* download a URL to a governed mount file with Python

## 5. One-sentence summary

Downloading a URL into a governed mount file is a reusable Python fetch capability.
