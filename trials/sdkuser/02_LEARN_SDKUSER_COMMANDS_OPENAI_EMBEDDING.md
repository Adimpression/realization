# SDK User Commands 02 — OpenAI Embedding

This document teaches the bounded Python capability of creating an embedding
through the OpenAI SDK.

## 1. Core capability

When a user wants vector embeddings from text through its SDK, the reusable
capability is OpenAI embedding creation by model and input text.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    model: str,
    text: str,
    *,
    __dependencies__: tuple[str, ...] = ("openai",),
) -> dict[str, object]:
    from openai import OpenAI

    client = OpenAI()
    response = client.embeddings.create(model=model, input=text)
    vector = response.data[0].embedding
    return {"status": "ok", "model": model, "dimensions": len(vector), "embedding": vector}
```

## 3. Inputs and outputs

Inputs:

* `model`: the embedding model name
* `text`: the text to embed

Output:

* status, model, vector dimension count, and the embedding values

## 4. Natural-language paraphrases

* create an embedding with the OpenAI SDK using model `text-embedding-3-small` and text `semantic search`
* compute one embedding through the OpenAI SDK
* turn text into a vector with the OpenAI client

## 5. One-sentence summary

Creating an embedding through the OpenAI SDK is a reusable Python SDK vector
capability.
