# Python Commands 08 — Read Json File

This document teaches the bounded Python capability of loading JSON data from a
file through a governed virtual mount.

## 1. Core capability

When a user wants structured JSON content from disk, the reusable capability is
JSON-file reading by mount plus relative path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_tmp",
    *,
    relative_path: str = "config.json",
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    from python_skill_host import broker_request

    result = broker_request("fs.read_mount", mount=mount, relative_path=relative_path)
    if result.get("status") != "ok":
        return result
    payload = json.loads(result.get("text", ""))
    return {"status": "loaded", "mount": mount, "relative_path": relative_path, "payload": payload}
```

## 3. Inputs and outputs

Input:

* `mount`: the governed virtual mount to read from
* `relative_path`: the JSON file path inside that mount

Output:

* status, the mount-relative target, and the parsed JSON payload

## 4. Natural-language paraphrases

* load the JSON file `config.json` from mount `skill_tmp`
* read JSON from `settings.json` in a governed mount
* parse a JSON file with Python through a governed mount

## 5. One-sentence summary

Reading JSON from a file through a mount is a reusable governed Python
structured-data capability.
