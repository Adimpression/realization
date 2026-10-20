# Python Commands 04 — Append Text File

This document teaches the bounded Python capability of appending text to an
existing file through a governed virtual mount.

## 1. Core capability

When a user wants to add text to the end of a file without replacing the
existing contents, the reusable capability is text append by mount,
relative path, and text.

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

    result = broker_request(
        "fs.write_mount",
        mount=mount,
        relative_path=relative_path,
        text=text,
        append=True,
    )
    if result.get("status") != "ok":
        return result
    return {
        "status": "appended",
        "mount": mount,
        "relative_path": relative_path,
        "text": text,
    }
```

## 3. Inputs and outputs

Inputs:

* `mount`: the governed virtual mount to write into
* `relative_path`: the file path inside that mount
* `text`: the text to append

Output:

* status, the mount-relative target, and the appended text

## 4. Natural-language paraphrases

* append `another line` to mount `skill_tmp` at `python-suite.txt`
* add `done\n` to mount `skill_output` at `log.txt`
* append text to a file with Python through a governed mount

## 5. One-sentence summary

Appending text to a file through a mount is a reusable governed Python
incremental-write capability.
