# Python Commands 11 — Write Csv File

This document teaches the bounded Python capability of writing CSV text into a
file through a governed virtual mount.

## 1. Core capability

When a user wants CSV content saved as a file, the reusable capability is
CSV-file writing by mount, relative path, and CSV text.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    mount: str = "skill_tmp",
    relative_path: str = "data.csv",
    csv_text: str = "",
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    from python_skill_host import broker_request

    result = broker_request("fs.write_mount", mount=mount, relative_path=relative_path, text=csv_text)
    if result.get("status") != "ok":
        return result
    return {"status": "written", "mount": mount, "relative_path": relative_path}
```

## 3. Inputs and outputs

Inputs:

* `mount`: the governed virtual mount to write into
* `relative_path`: the CSV file path inside that mount
* `csv_text`: the CSV content to save

Output:

* status and the mount-relative target

## 4. Natural-language paraphrases

* write the CSV text `name,score\nAda,10\nBob,9\n` to mount `skill_tmp` at `data.csv`
* save CSV into `report.csv` in a governed mount
* write CSV text to a file with Python through a governed mount

## 5. One-sentence summary

Writing CSV text into a file through a mount is a reusable governed Python
tabular-persistence capability.
