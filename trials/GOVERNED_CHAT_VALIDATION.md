# Governed Chat Validation

This characterization trial observes whether the standalone core can sustain a
small but meaningful conversation through explicit governed reductions. It is
not a qualification gate, a unit test for prompt routing, or a generic model
benchmark.

## What The Trial Measures

Each scenario contains one independent turn followed by three follow-ups and
one correction. Each related turn receives the immediately preceding committed
result through the governed `prior_result` inlet. The transcript remains a
host-owned record; it is not silently admitted as engine evidence. The bounded
project-brief fixture tests exact conversational state changes; the herb-garden
fixture is a more open-ended planning stress case.

The report keeps three judgments separate:

1. **Structural integrity** checks completion, non-empty answers, run identity,
   parent-run linkage, treatment, and durable checkpoint creation.
2. **Semantic continuity** checks whether explicit facts and corrected facts
   survive the five-turn chain. These are deterministic concept checks, not an
   LLM judging its own output.
3. **Performance** records every turn and every logical `ask_llm` request. A
   logical request may perform provider-internal retries; those attempts are
   included in its duration but are not counted separately. Timing is
   observational unless an explicit threshold is supplied.

Provider or transport failure is reported as `operational_error`. It is never
counted as evidence that the conversation is semantically bad.

The companion `llm_requests.jsonl` is flushed after every logical request so a
manually interrupted latency investigation still preserves request shape and
timing evidence. It does not claim to be a transport-attempt trace.

## Resumption Boundary

This trial characterizes the current policy: each related turn receives only
the immediately preceding committed result as an explicit `prior_result` inlet.
That policy is a deliberately incomplete baseline, not the general resumption
contract. In particular, the trial does not project explicit achieved and
non-achieved state, supersession, governed path provenance, or identity across
turns.

The governing distinctions and constraints are defined in
[Resumption](../RESUMPTION.md). The transcript must not silently become evidence,
and an LLM-output cache must not substitute for an explicit resumption inlet.

## Run It

Use the configured provider and model:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py
```

Run the bounded state-transformation scenario:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py \
  --scenario trials/governed_chat/FIVE_TURN_PROJECT_BRIEF.json
```

Select the small OpenAI model explicitly and bound each provider call:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py \
  --provider openai \
  --model gpt-5-nano-2025-08-07 \
  --provider-timeout-seconds 60
```

Use a running local llama.cpp server:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py \
  --provider llamacpp \
  --model Qwen/Qwen3-8B-GGUF
```

The default report location is `reports/governed_chat/<UTC timestamp>/`. The
directory contains the evaluation report plus the normal transcript, run
bindings, checkpoints, and SQLite artifact store created by the core host.

## Compare Speed Profiles

First record the normal governed configuration. Then run an isolated comparison
with optional mechanisms disabled:

```console
uv run --frozen python trials/GOVERNED_CHAT_VALIDATION.py \
  --output-dir /tmp/governed-chat-fast-profile \
  --discovery off \
  --reflection off \
  --contemplation off
```

That comparison does not establish that the faster profile is acceptable. It
is acceptable only if the semantic and structural scores remain green. Once a
stable baseline exists, timing can become a gate with
`--max-median-turn-seconds` and `--max-single-turn-seconds`.

`--llm-policy off` is available only as a negative-path diagnostic. With these
scenarios, the first run remains incomplete and therefore cannot legally parent
the next follow-up. It is not a comparable five-turn latency baseline.

## Interpretation

- High LLM-request share means model latency, internal retries, or too many
  serial logical requests is the primary speed problem.
- High non-LLM time means controller reduction, persistence, or artifact
  retrieval needs profiling.
- Good early turns and weak late turns indicate that carrying only the prior
  committed result loses necessary conversational state.
- A correction that preserves the old fact but omits the new one is a semantic
  failure even if the run is structurally complete.
- A plausible answer with broken parent linkage is a governance failure.

The scenario is deliberately narrow. Passing it demonstrates the observed
behavior under one bounded scenario and configuration; it does not prove a
general form of conversational continuity or chatbot quality.
