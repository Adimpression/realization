# Python Commands 01 — List Directory Entries

This document teaches the bounded Python capability of listing entries in a
directory exposed through a governed virtual mount.

## 1. Core capability

When a user wants to inspect what names exist directly inside a directory, the
reusable capability is directory listing by mount plus relative path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_input",
    *,
    relative_path: str = "",
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    from python_skill_host import broker_request

    result = broker_request("fs.list_mount", mount=mount, relative_path=relative_path)
    if result.get("status") != "ok":
        return result
    return {
        "status": "listed",
        "mount": mount,
        "relative_path": relative_path,
        "entries": result.get("entries", []),
    }
```

## 3. Inputs and outputs

Input:

* `mount`: the governed virtual mount to inspect
* `relative_path`: the directory path inside that mount

Output:

* status, the mount-relative target, and a sorted list of entry names

## 4. Natural-language paraphrases

* list the entries in mount `skill_input` at `trials`
* show what is inside mount `skill_input` at `tests`
* list directory contents through a governed mount with Python

## 5. One-sentence summary

Listing directory entries by mount and relative path is a reusable governed
Python inspection capability.
