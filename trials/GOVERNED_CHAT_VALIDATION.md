# Governed Chat Validation

This trial qualifies the provider-backed governed-conversation product path
with the neutral Cedar resumption journey. It is not a generic chatbot
benchmark and does not replace deterministic engine or model-off conformance.

## What The Trial Measures

The default scenario maps every principle in
[Resumption](../RESUMPTION.md) to one or more observable probes. Ordinary
semantic turns enter as natural language through the shipped planner, the
transport-neutral conversation application, the canonical engine, SQLite, and
the shipped renderer. The harness uses public operations for restart,
transcript discard, rerendering, interruption, unbound-host isolation, stale
anchor arrangement, and inspection.

The report keeps four result classes separate:

1. **Structural conformance** checks causal bindings, revisions, achieved and
   non-achieved state, supersession, realignment, branches, interruption, path,
   replay, and rejection without mutation.
2. **Interpretation** checks whether ordinary language selected the intended
   operation family. The provider cannot choose causal identity or admission.
3. **Rendering** checks that admitted results pass through the product renderer
   while presentation remains non-authoritative.
4. **Performance** records turn duration plus provider timing and provenance
   already emitted by product planning, rendering, and rerendering receipts.

Provider or transport failure is `operational_error`; it is not reclassified as
a semantic failure. `llm_requests.jsonl` contains receipt-derived timing,
provider/model identity, response identity, and request/response digests. It
does not contain prompt text and does not claim to be a transport-attempt trace.

## Resumption Boundary

Each related turn names an exact persisted causal revision. Restart and provider
replacement reconstruct from SQLite, not transcript, hidden provider state, or
model cache. Interruption targets an execution attempt and does not create a
semantic revision. Augmentation, correction, redirection, realignment,
branching, merge, explanation, verification, reconstruction, and reversal
remain distinct operations.

The harness may arrange an operational condition, but it does not own a
planner, renderer, prompt, proposal normalizer, selector resolver, journal, or
recovery path. Recorded and fake providers are suitable for deterministic
tests; only a configured live-provider run counts as this trial's
conversational qualification.

## Run It

Use the configured provider and model with the default Cedar scenario:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py
```

Select an OpenAI model explicitly and bound each provider call:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py \
  --provider openai \
  --model gpt-5-nano-2025-08-07 \
  --provider-timeout-seconds 60
```

Use an already-running local llama.cpp server:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py \
  --provider llamacpp \
  --model Qwen/Qwen3-8B-GGUF
```

The default report location is `reports/governed_chat/<UTC timestamp>/`. It
contains the qualification report, product conversation journals, run bindings,
provider receipt evidence, and SQLite semantic/activity store.

The historical five-turn fixtures remain available for narrow compatibility
characterization when selected explicitly, but they are not Cedar or resumption
qualification evidence.

## Compare Speed Profiles

Record a normal run first, then make an isolated comparison:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py \
  --output-dir /tmp/governed-chat-fast-profile \
  --discovery off \
  --reflection off \
  --contemplation off
```

A faster profile is acceptable only if structural, interpretation, and
rendering evidence remain green. Add `--max-median-turn-seconds` or
`--max-single-turn-seconds` only after a stable baseline exists.

`--llm-policy` configures the semantic engine's optional internal model policy;
it does not replace the external planner/renderer selected by `--provider` and
`--model` for this live conversational trial.

## Interpretation

- High provider-request share points to model latency, retries, or excess serial
  planning/rendering calls.
- High non-provider time points to orchestration, persistence, inspection, or
  engine work.
- A fluent answer with a wrong operation, selector, causal anchor, or admitted
  state is a failed qualification.
- A correct transition with weak prose is a rendering failure, not a semantic
  mutation.
- Passing this bounded scenario proves only the declared Cedar scope under the
  recorded configuration; it does not prove general intelligence or arbitrary
  conversational quality.
