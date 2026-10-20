# SDK User Commands 03 — Anthropic Message

This document teaches the bounded Python capability of generating a message
through the Anthropic SDK.

## 1. Core capability

When a user wants one model-generated message through the Anthropic SDK, the
reusable capability is Anthropic text generation by model and prompt.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    model: str,
    prompt: str,
    *,
    max_tokens: int = 200,
    __dependencies__: tuple[str, ...] = ("anthropic",),
) -> dict[str, object]:
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return {"status": "ok", "model": model, "text": text}
```

## 3. Inputs and outputs

Inputs:

* `model`: the Anthropic model name
* `prompt`: the user input text
* `max_tokens`: the completion limit

Output:

* status, model, and generated text

## 4. Natural-language paraphrases

* generate a short message with the Anthropic SDK using model `claude-sonnet-4-5` and prompt `Summarize API reliability in one sentence.`
* call the Anthropic SDK for one answer
* generate one model message from a prompt

## 5. One-sentence summary

Generating a message through the Anthropic SDK is a reusable Python SDK
completion capability.
