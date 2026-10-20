# Python Commands 16 — Find Files By Suffix

This document teaches the bounded Python capability of finding files beneath a
governed virtual mount that end with a given suffix.

## 1. Core capability

When a user wants matching files discovered recursively inside a governed data
surface, the reusable capability is recursive file search by mount, root
relative path, and suffix.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    suffix: str = ".md",
    mount: str = "skill_input",
    relative_path: str = "",
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    from python_skill_host import broker_request

    result = broker_request(
        "fs.find_mount",
        mount=mount,
        relative_path=relative_path,
        suffix=suffix,
    )
    if result.get("status") != "ok":
        return result
    return {
        "status": "found",
        "mount": mount,
        "relative_path": relative_path,
        "suffix": suffix,
        "matches": result.get("matches", []),
    }
```

## 3. Inputs and outputs

Inputs:

* `mount`: the governed mount to search
* `relative_path`: the directory path inside that mount
* `suffix`: the file suffix to match, such as `.md` or `.json`

Output:

* status, the governed search root, the suffix, and matching mount-relative file paths

## 4. Natural-language paraphrases

* find files ending in `.md` under mount `skill_input` at `trials`
* search mount `skill_output` at `exports` for files with suffix `.json`
* recursively find files by suffix through a governed mount with Python

## 5. One-sentence summary

Finding files recursively by suffix in a governed mount is a reusable Python discovery capability.
