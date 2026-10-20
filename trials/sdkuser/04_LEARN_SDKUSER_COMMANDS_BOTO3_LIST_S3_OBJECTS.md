# SDK User Commands 04 — Boto3 List S3 Objects

This document teaches the bounded Python capability of listing objects in an S3
bucket through boto3.

## 1. Core capability

When a user wants the current object keys in one bucket, the reusable
capability is S3 object listing by bucket name.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    bucket: str,
    *,
    prefix: str = "",
    __dependencies__: tuple[str, ...] = ("boto3",),
) -> dict[str, object]:
    import boto3

    client = boto3.client("s3")
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    keys = [item["Key"] for item in response.get("Contents", [])]
    return {"status": "ok", "bucket": bucket, "prefix": prefix, "keys": keys}
```

## 3. Inputs and outputs

Inputs:

* `bucket`: the S3 bucket name
* `prefix`: an optional key prefix

Output:

* status, bucket, prefix, and the matching object keys

## 4. Natural-language paraphrases

* list objects in the S3 bucket `demo-bucket` with the boto3 SDK
* enumerate keys in one bucket
* list S3 objects through boto3

## 5. One-sentence summary

Listing S3 objects by bucket and prefix is a reusable Python SDK storage
inspection capability.
