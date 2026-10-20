# SDK User Commands 12 — Supabase Select Rows

This document teaches the bounded Python capability of selecting rows from a
Supabase table through the Python SDK.

## 1. Core capability

When a user wants rows retrieved from one hosted table, the reusable capability
is Supabase table selection by URL, API key, and table name.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    supabase_url: str,
    supabase_key: str,
    table: str,
    *,
    __dependencies__: tuple[str, ...] = ("supabase",),
) -> dict[str, object]:
    from supabase import create_client

    client = create_client(supabase_url, supabase_key)
    response = client.table(table).select("*").execute()
    return {"status": "ok", "table": table, "rows": response.data}
```

## 3. Inputs and outputs

Inputs:

* `supabase_url`: the Supabase project URL
* `supabase_key`: the Supabase API key
* `table`: the table name

Output:

* status, table name, and selected rows

## 4. Natural-language paraphrases

* select rows from Supabase table `profiles`
* fetch table data with the Supabase SDK
* read all rows from one hosted table

## 5. One-sentence summary

Selecting rows from a Supabase table by URL, key, and table name is a reusable
Python SDK hosted-data capability.
