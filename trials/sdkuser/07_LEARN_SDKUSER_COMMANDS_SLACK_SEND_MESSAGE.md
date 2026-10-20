# SDK User Commands 07 — Slack Send Message

This document teaches the bounded Python capability of sending one Slack message
through the Slack SDK.

## 1. Core capability

When a user wants one message posted to a Slack channel, the reusable capability
is Slack message send by token, channel, and text.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    token: str,
    channel: str,
    text: str,
    *,
    __dependencies__: tuple[str, ...] = ("slack_sdk",),
) -> dict[str, object]:
    from slack_sdk import WebClient

    client = WebClient(token=token)
    response = client.chat_postMessage(channel=channel, text=text)
    return {"status": "sent", "channel": channel, "timestamp": response["ts"]}
```

## 3. Inputs and outputs

Inputs:

* `token`: the Slack bot token
* `channel`: the Slack channel identifier
* `text`: the message text

Output:

* sent status, channel, and message timestamp

## 4. Natural-language paraphrases

* send the Slack message `deploy complete` to channel `C12345678`
* post one message with the Slack SDK
* send a Slack notification through Python

## 5. One-sentence summary

Sending one Slack message by token, channel, and text is a reusable Python SDK
messaging capability.
