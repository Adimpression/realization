# Realized Core LLM

`realized-core-llm` owns provider-neutral conversational planning and rendering
contracts, prompt construction, typed OpenAI-compatible transport, and provider
receipts.

The transport is deliberately stateless. It constructs provider clients,
applies caller-declared compatibility and retry policies, and converts provider
responses into typed text, tool-call, and metadata values. It does not retain
conversation history, reduction state, resumption state, or cached answers.

Controller and workstation adapters retain their own prompts, request policy,
session lifecycle, tool mediation, and receipts. LLM output remains advisory:
this package owns no causal identity, semantic admission, governance decision,
authority grant, realizer dispatch, host session, or UI behavior.
