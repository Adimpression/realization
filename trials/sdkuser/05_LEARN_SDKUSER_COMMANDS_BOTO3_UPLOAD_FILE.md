# SDK User Commands 05 — Boto3 Upload File To S3

This document teaches the bounded Python capability of uploading one local file
to S3 through boto3.

## 1. Core capability

When a user wants a file stored in an S3 bucket, the reusable capability is S3
upload by local path, bucket, and key.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    local_path: str,
    bucket: str,
    key: str,
    *,
    __dependencies__: tuple[str, ...] = ("boto3",),
) -> dict[str, str]:
    import boto3

    client = boto3.client("s3")
    client.upload_file(local_path, bucket, key)
    return {"status": "uploaded", "local_path": local_path, "bucket": bucket, "key": key}
```

## 3. Inputs and outputs

Inputs:

* `local_path`: the local file path to upload
* `bucket`: the destination bucket
* `key`: the destination object key

Output:

* status, local path, bucket, and key

## 4. Natural-language paraphrases

* upload `/tmp/report.txt` to the S3 bucket `demo-bucket` as key `reports/report.txt`
* send one local file to S3 with boto3
* upload a file to a bucket and key

## 5. One-sentence summary

Uploading a file to S3 by local path, bucket, and key is a reusable Python SDK
storage-write capability.
