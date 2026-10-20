# Python Commands 13 — Create Zip Archive

This document teaches the bounded Python capability of archiving a mount-relative
directory into a mount-relative zip file.

## 1. Core capability

When a user wants a governed directory packaged into one governed zip archive,
the reusable capability is zip creation by source mount plus destination mount.

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
        "fs.create_zip_mount",
        source_mount=source_mount,
        source_relative_path=source_relative_path,
        destination_mount=destination_mount,
        destination_relative_path=destination_relative_path,
    )
    if result.get("status") != "ok":
        return result
    return {
        "status": "archived",
        "source_mount": source_mount,
        "source_relative_path": source_relative_path,
        "destination_mount": destination_mount,
        "destination_relative_path": destination_relative_path,
    }
```

## 3. Inputs and outputs

Inputs:

* `source_mount`: the governed mount holding the source directory
* `source_relative_path`: the directory path inside the source mount
* `destination_mount`: the governed mount that should receive the zip archive
* `destination_relative_path`: the archive path inside the destination mount

Output:

* status plus the source and destination mount-relative targets

## 4. Natural-language paraphrases

* create `realized-tests.zip` in mount `skill_tmp` from mount `skill_input` at `tests`
* zip `reports/current` from mount `skill_input` into mount `skill_output` at `reports-current.zip`
* create a zip archive with Python through governed mounts

## 5. One-sentence summary

Creating a zip archive from a governed directory is a reusable governed Python packaging
capability.
