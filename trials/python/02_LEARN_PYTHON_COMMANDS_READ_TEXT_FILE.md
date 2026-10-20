# Python Commands 02 — Read Text File

This document teaches the bounded Python capability of reading a text file
through a governed virtual mount.

## 1. Core capability

When a user wants the full contents of a text file, the reusable capability is
text-file reading by mount plus relative path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_input",
    *,
    relative_path: str,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from python_skill_host import broker_request

    result = broker_request("fs.read_mount", mount=mount, relative_path=relative_path)
    if result.get("status") != "ok":
        return result
    return {
        "status": "read",
        "mount": mount,
        "relative_path": relative_path,
        "text": result.get("text", ""),
    }
```

## 3. Inputs and outputs

Input:

* `mount`: the governed virtual mount to read from
* `relative_path`: the text file path inside that mount

Output:

* status, the mount-relative target, and the decoded text

## 4. Natural-language paraphrases

* read the text file `README.md` from mount `skill_input`
* show the contents of `docs/example.txt` from a governed mount
* load a text file with Python through a governed mount

## 5. One-sentence summary

Reading a text file by mount and relative path is a reusable governed Python
text-access capability.
