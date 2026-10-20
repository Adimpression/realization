# Python Commands 06 — Move File

This document teaches the bounded Python capability of moving or renaming a
file across governed virtual mounts.

## 1. Core capability

When a user wants a file relocated or renamed, the reusable capability is file
move by source mount plus destination mount.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    source_mount: str = "skill_tmp",
    source_relative_path: str = "",
    destination_mount: str = "skill_output",
    destination_relative_path: str = "",
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from python_skill_host import broker_request

    result = broker_request(
        "fs.move_mount",
        source_mount=source_mount,
        source_relative_path=source_relative_path,
        destination_mount=destination_mount,
        destination_relative_path=destination_relative_path,
    )
    if result.get("status") != "ok":
        return result
    return {
        "status": "moved",
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
* `destination_mount`: the governed mount that should receive the moved file
* `destination_relative_path`: the new file path inside the destination mount

Output:

* status plus the source and destination mount-relative targets

## 4. Natural-language paraphrases

* move `python-readme.copy` from mount `skill_tmp` to mount `skill_output` at `python-readme.moved`
* rename `reports/current.txt` from mount `skill_tmp` to mount `skill_output` at `reports/archive.txt`
* move a file with Python through governed mounts

## 5. One-sentence summary

Moving a file by source mount and destination mount is a reusable governed Python relocation
capability.
