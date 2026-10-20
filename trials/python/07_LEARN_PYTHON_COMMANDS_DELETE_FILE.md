# Python Commands 07 — Delete File

This document teaches the bounded Python capability of deleting a file from a
governed virtual mount.

## 1. Core capability

When a user wants a specific governed file removed, the reusable capability is
file deletion by mount plus relative path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_output",
    *,
    relative_path: str,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from python_skill_host import broker_request

    result = broker_request("fs.delete_mount", mount=mount, relative_path=relative_path)
    if result.get("status") != "ok":
        return result
    return {"status": "deleted", "mount": mount, "relative_path": relative_path}
```

## 3. Inputs and outputs

Input:

* `mount`: the governed mount containing the file
* `relative_path`: the file path inside that mount

Output:

* status and the mount-relative target that was deleted

## 4. Natural-language paraphrases

* delete `python-readme.moved` from mount `skill_output`
* remove `logs/old.log` from mount `skill_tmp`
* delete a file with Python through a governed mount

## 5. One-sentence summary

Deleting a file by mount and relative path is a reusable governed Python cleanup capability.
