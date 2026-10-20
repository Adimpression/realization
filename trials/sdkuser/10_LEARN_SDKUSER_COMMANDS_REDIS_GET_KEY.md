# SDK User Commands 10 — Redis Get Key

This document teaches the bounded Python capability of reading one Redis key.

## 1. Core capability

When a user wants the current value of one Redis key, the reusable capability is
Redis key lookup by URL and key name.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    redis_url: str,
    key: str,
    *,
    __dependencies__: tuple[str, ...] = ("redis",),
) -> dict[str, object]:
    import redis

    client = redis.from_url(redis_url)
    value = client.get(key)
    decoded = value.decode("utf-8") if isinstance(value, bytes) else value
    return {"status": "ok", "key": key, "value": decoded}
```

## 3. Inputs and outputs

Inputs:

* `redis_url`: the Redis connection URL
* `key`: the key to read

Output:

* status, the key, and the decoded value

## 4. Natural-language paraphrases

* read the Redis key `session:42`
* fetch one key from Redis with the Python SDK
* get one cached value from Redis

## 5. One-sentence summary

Reading one Redis key by connection URL and key name is a reusable Python SDK
cache-read capability.
