# Python Commands 14 — Extract Zip Archive

This document teaches the bounded Python capability of extracting a mount-relative
zip archive into a mount-relative directory.

## 1. Core capability

When a user wants a governed zip file unpacked into a governed destination
folder, the reusable capability is zip extraction by source mount plus
destination mount.

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
        "fs.extract_zip_mount",
        source_mount=source_mount,
        source_relative_path=source_relative_path,
        destination_mount=destination_mount,
        destination_relative_path=destination_relative_path,
    )
    if result.get("status") != "ok":
        return result
    return {
        "status": "extracted",
        "source_mount": source_mount,
        "source_relative_path": source_relative_path,
        "destination_mount": destination_mount,
        "destination_relative_path": destination_relative_path,
    }
```

## 3. Inputs and outputs

Inputs:

* `source_mount`: the governed mount holding the zip file
* `source_relative_path`: the zip file path inside the source mount
* `destination_mount`: the governed mount that should receive the extracted directory
* `destination_relative_path`: the directory path inside the destination mount

Output:

* status plus the source and destination mount-relative targets

## 4. Natural-language paraphrases

* extract `realized-tests.zip` from mount `skill_tmp` into mount `skill_output` at `extracted-tests`
* unzip `reports-current.zip` from mount `skill_tmp` into mount `skill_output` at `reports-current`
* extract a zip archive with Python through governed mounts

## 5. One-sentence summary

Extracting a zip archive into a governed directory is a reusable governed Python unpacking
capability.
