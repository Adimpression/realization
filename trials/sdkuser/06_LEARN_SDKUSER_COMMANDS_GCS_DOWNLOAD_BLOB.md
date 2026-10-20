# SDK User Commands 06 — Google Cloud Storage Download Blob

This document teaches the bounded Python capability of downloading one blob from
Google Cloud Storage.

## 1. Core capability

When a user wants one cloud object saved locally from GCS, the reusable
capability is blob download by bucket, blob name, and destination path.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    bucket: str,
    blob_name: str,
    destination: str,
    *,
    __dependencies__: tuple[str, ...] = ("google-cloud-storage",),
) -> dict[str, str]:
    from google.cloud import storage

    client = storage.Client()
    bucket_ref = client.bucket(bucket)
    blob = bucket_ref.blob(blob_name)
    blob.download_to_filename(destination)
    return {"status": "downloaded", "bucket": bucket, "blob_name": blob_name, "destination": destination}
```

## 3. Inputs and outputs

Inputs:

* `bucket`: the GCS bucket name
* `blob_name`: the blob path inside the bucket
* `destination`: the local output path

Output:

* status, bucket, blob name, and destination path

## 4. Natural-language paraphrases

* download the GCS blob `reports/daily.json` from bucket `demo-bucket` to `/tmp/daily.json`
* fetch one object from Google Cloud Storage
* download a GCS blob with the Python SDK

## 5. One-sentence summary

Downloading a GCS blob by bucket, blob name, and destination is a reusable
Python SDK storage-read capability.
