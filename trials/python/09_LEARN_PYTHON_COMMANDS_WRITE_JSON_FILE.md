# Python Commands 09 — Write Json File

This document teaches the bounded Python capability of validating JSON text and
writing it to a file through a governed virtual mount.

## 1. Core capability

When a user wants structured JSON text normalized and saved, the reusable
capability is JSON-file writing by mount, relative path, and JSON text.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_tmp",
    relative_path: str = "config.json",
    json_text: str = "{}",
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    import json
    from python_skill_host import broker_request

    payload = json.loads(json_text)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    result = broker_request("fs.write_mount", mount=mount, relative_path=relative_path, text=rendered)
    if result.get("status") != "ok":
        return result
    return {"status": "written", "mount": mount, "relative_path": relative_path}
```

## 3. Inputs and outputs

Inputs:

* `mount`: the governed virtual mount to write into
* `relative_path`: the JSON file path inside that mount
* `json_text`: the JSON text that should be parsed and stored

Output:

* status and the mount-relative target that received the normalized JSON document

## 4. Natural-language paraphrases

* write the JSON text `{"status":"ok","enabled":true}` to mount `skill_tmp` at `config.json`
* save JSON into `settings.json` in a governed mount
* write validated JSON text to a file with Python through a governed mount

## 5. One-sentence summary

Writing normalized JSON text into a file through a mount is a reusable governed
Python data-persistence capability.
