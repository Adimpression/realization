# Python Commands 05 — Copy File

This document teaches the bounded Python capability of copying a file from one
governed virtual mount to another.

## 1. Core capability

When a user wants one file duplicated at another governed location, the
reusable capability is file copy by source mount plus destination mount.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    source_mount: str = "skill_input",
    source_relative_path: str = "",
    destination_mount: str = "skill_tmp",
    destination_relative_path: str = "",
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from python_skill_host import broker_request

    result = broker_request(
        "fs.copy_mount",
        source_mount=source_mount,
        source_relative_path=source_relative_path,
        destination_mount=destination_mount,
        destination_relative_path=destination_relative_path,
    )
    if result.get("status") != "ok":
        return result
    return {
        "status": "copied",
        "source_mount": source_mount,
        "source_relative_path": source_relative_path,
        "destination_mount": destination_mount,
        "destination_relative_path": destination_relative_path,
    }
```

## 3. Inputs and outputs

Inputs:

* `source_mount`: the governed mount holding the existing file
* `source_relative_path`: the existing file path inside the source mount
* `destination_mount`: the governed mount that should receive the copy
* `destination_relative_path`: the new file path inside the destination mount

Output:

* status plus the source and destination mount-relative targets

## 4. Natural-language paraphrases

* copy `trials/python/README.md` from mount `skill_input` to mount `skill_tmp` at `python-readme.copy`
* duplicate `docs/input.txt` from mount `skill_input` into mount `skill_output` at `archive/input.txt`
* copy a file with Python through governed mounts

## 5. One-sentence summary

Copying a file by source mount and destination mount is a reusable governed Python transfer
capability.
