# API Client Commands 12 — Poll Job Status Until Complete

This document teaches the bounded Python capability of polling a JSON endpoint
until a job reaches a terminal status.

## 1. Core capability

When a user wants an asynchronous job checked until completion, the reusable
capability is JSON status polling by URL, field name, target value, and timing
controls.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    url: str,
    status_field: str,
    target_value: str,
    *,
    poll_interval_seconds: float = 1.0,
    max_attempts: int = 10,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    import json
    import time
    from urllib.request import urlopen

    last_payload = {}
    for attempt in range(1, max_attempts + 1):
        with urlopen(url) as response:
            last_payload = json.loads(response.read().decode("utf-8"))
        if str(last_payload.get(status_field)) == target_value:
            return {"status": "completed", "attempt": attempt, "payload": last_payload}
        time.sleep(poll_interval_seconds)
    return {"status": "timeout", "attempt": max_attempts, "payload": last_payload}
```

## 3. Inputs and outputs

Inputs:

* `url`: the job-status endpoint
* `status_field`: the JSON field to inspect
* `target_value`: the value that indicates completion
* `poll_interval_seconds`: how long to wait between checks
* `max_attempts`: the maximum number of checks

Output:

* completion or timeout status, attempt count, and the last JSON payload

## 4. Natural-language paraphrases

* poll `https://api.example.com/jobs/42` until the JSON field `status` becomes `completed`
* check a job-status endpoint until it finishes
* repeatedly fetch JSON until a target field reaches one value

## 5. One-sentence summary

Polling a JSON job endpoint until completion is a reusable Python async-API
monitoring capability.
