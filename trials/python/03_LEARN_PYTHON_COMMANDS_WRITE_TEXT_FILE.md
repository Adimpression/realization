# Python Commands 03 — Write Text File

This document teaches the bounded Python capability of writing text into a
file through a governed virtual mount.

## 1. Core capability

When a user wants a specific text payload saved to a file, the reusable
capability is text-file writing by mount, relative path, and text.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_tmp",
    relative_path: str = "python-suite.txt",
    text: str = "",
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from python_skill_host import broker_request

    result = broker_request("fs.write_mount", mount=mount, relative_path=relative_path, text=text)
    if result.get("status") != "ok":
        return result
    return {
        "status": "written",
        "mount": mount,
        "relative_path": relative_path,
        "text": text,
    }
```

## 3. Inputs and outputs

Inputs:

* `mount`: the governed virtual mount to write into
* `relative_path`: the file path inside that mount
* `text`: the exact text to write

Output:

* status, the mount-relative target, and the text that was written

## 4. Natural-language paraphrases

* write `hello world` to mount `skill_tmp` at `python-suite.txt`
* save `ready` into mount `skill_output` at `status.txt`
* write text into a file with Python through a governed mount

## 5. One-sentence summary

Writing text into a file through a mount is a reusable governed Python
persistence capability.
