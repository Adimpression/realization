# SDK User Commands 01 — OpenAI Text Response

This document teaches the bounded Python capability of generating a text
response through the OpenAI SDK.

## 1. Core capability

When a user wants one text completion from an LLM through its SDK, the reusable
capability is OpenAI text generation by model and prompt.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    model: str,
    prompt: str,
    *,
    __dependencies__: tuple[str, ...] = ("openai",),
) -> dict[str, object]:
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(model=model, input=prompt)
    return {
        "status": "ok",
        "model": model,
        "text": response.output_text,
        "response_id": response.id,
    }
```

## 3. Inputs and outputs

Inputs:

* `model`: the OpenAI model name
* `prompt`: the user input text

Output:

* status, model, response text, and response identifier

## 4. Natural-language paraphrases

* generate a short text response with the OpenAI SDK using model `gpt-5.4` and prompt `Say hello in one sentence.`
* call the OpenAI SDK for one text response
* generate one LLM answer from a prompt

## 5. One-sentence summary

Generating a text response through the OpenAI SDK is a reusable Python SDK
completion capability.
