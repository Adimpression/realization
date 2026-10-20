# Python Commands 10 — Read Csv File

This document teaches the bounded Python capability of reading rows from a CSV
file through a governed virtual mount.

## 1. Core capability

When a user wants structured tabular rows from a CSV file, the reusable
capability is CSV-file reading by mount plus relative path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_tmp",
    *,
    relative_path: str = "data.csv",
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import csv
    import io
    from python_skill_host import broker_request

    result = broker_request("fs.read_mount", mount=mount, relative_path=relative_path)
    if result.get("status") != "ok":
        return result
    rows = list(csv.DictReader(io.StringIO(result.get("text", ""))))
    return {"status": "loaded", "mount": mount, "relative_path": relative_path, "rows": rows}
```

## 3. Inputs and outputs

Input:

* `mount`: the governed virtual mount to read from
* `relative_path`: the CSV file path inside that mount

Output:

* status, the mount-relative target, and parsed rows as dictionaries

## 4. Natural-language paraphrases

* read the CSV file `data.csv` from mount `skill_tmp`
* load rows from `scores.csv` in a governed mount
* parse a CSV file with Python through a governed mount

## 5. One-sentence summary

Reading CSV rows from a file through a mount is a reusable governed Python
tabular-data capability.
