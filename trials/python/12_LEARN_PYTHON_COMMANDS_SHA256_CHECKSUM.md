# Python Commands 12 — Compute Sha256 Checksum

This document teaches the bounded Python capability of computing a sha256
checksum for a file exposed through a governed virtual mount.

## 1. Core capability

When a user wants a stable digest of file content, the reusable capability is
sha256 computation by mount plus relative path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_input",
    *,
    relative_path: str = "README.md",
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    import hashlib
    from python_skill_host import broker_request

    result = broker_request("fs.read_mount", mount=mount, relative_path=relative_path)
    if result.get("status") != "ok":
        return result
    digest = hashlib.sha256(result.get("text", "").encode("utf-8")).hexdigest()
    return {"status": "hashed", "mount": mount, "relative_path": relative_path, "sha256": digest}
```

## 3. Inputs and outputs

Input:

* `mount`: the governed virtual mount to read from
* `relative_path`: the file path inside that mount

Output:

* status, the mount-relative target, and the sha256 digest

## 4. Natural-language paraphrases

* compute the sha256 checksum of `README.md` from mount `skill_input`
* hash `docs/example.txt` from a governed mount
* get a sha256 digest with Python through a governed mount

## 5. One-sentence summary

Computing a sha256 checksum by mount and relative path is a reusable governed
Python verification capability.
