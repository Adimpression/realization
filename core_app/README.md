# Realized Core

`realized-core` is the independently installable command-line application for
the canonical governed realization engine and its SQLite state store. The
distribution contains only the narrow command-line composition package; it does not
contain engine modules, workstation code, Flutter/Textual UI, the gRPC host,
or the publication workflow.

The installable core intentionally separates five cohesive projects:

- `realized-core-runtime` owns the dependency-inverted run/resume lifecycle.
- `realized-core-engine` supplies the canonical domain engine, state model,
  host mediation, and plain SQLite adapter.
- `realized-core-llm` owns model-facing planning and rendering contracts.
- `realized-core-conversation` owns the transport-neutral conversational
  application service and translates advisory proposals to the engine ABI.
- `realized-core` composes those packages behind the narrow
  `run` / `resume` / `inspect` command-line interface and an optional thin
  conversation host.

## Build

Build its source distribution and wheel from the repository checkout:

```console
uv build core_app --out-dir dist/core
```

The resulting application and its declared engine/runtime dependencies are
self-contained with respect to Realized source code. Python dependencies are
installed normally by `uvx` or another package installer.

That statement is limited to the published governed lifecycle. This
distribution does not expose governed `import-skill`, subject activation, or
registration of new host-realizer providers. It executes the engine's packaged
realizers; `--supported-executor` permits advertised packaged frameworks but
does not install or implement one.

## Run

After publishing the five distributions to an index:

```console
uvx realized-core run \
  --prompt "Compute force from mass 3 kg and acceleration 4 m/s^2." \
  --sqlite ./state/realization.sqlite3 \
  --state-out ./state/run.json \
  --llm off
```

The executable supports the governed core lifecycle and its entry-layer chat
host:

```console
realized-core run --help
realized-core resume --help
realized-core inspect --help
realized-core chat --help
```

Start a terminal conversation whose turns are explicitly related to governed
runs:

```console
uvx realized-core chat \
  --root ./state/chat \
  --llm off
```

With `--llm off`, or with `--llm auto` when no provider is configured, plain
input creates a new typed objective. With an available provider, `auto` and
`required` interpret plain input through the shared conversation planner before
mechanical application validation and engine submission. `/use <revision-id>`
selects the exact causal revision for a related turn. `/continue <text>`
submits a typed continuation; with multiple active holds, use
`/continue <hold-id> -- <text>`. A follow-up derives a new objective from
explicit admitted material using `/follow-up <item-id,...> -- <text>`.
Correction requires an exact current target:
`/correct <item-id> -- <replacement>`.

The host stores transcript, exact revision bindings, active user selection,
and SQLite separately. It does not create JSON state checkpoints or infer
causal identity from transcript position.

The terminal loop belongs to `realized-core`, the entry package. The reusable
conversation service belongs to `realized-core-conversation` and calls the
engine's typed start, resumption, interruption, and inspection ABI; the engine
does not own a transcript or choose how turns relate.

Embedding applications can submit an explicit
`realized_core.conversation.ConversationTurnPlan` through
`CoreConversationHost.submit_plan`. Every plan is causally bound before engine
submission. An optional `on_attempt_running` callback receives the opaque
attempt identifier only after it is durably running, allowing the embedding
application to call `CoreConversationHost.interrupt` from its own concurrency
model. Attempt identity remains operational and never replaces the governed
scope, objective, branch, and revision identity.

Plain SQLite is always selected by this executable. Vector storage and Wasm
execution are not required. Wasmtime remains an optional extra for callers that
explicitly execute admitted Wasm abilities:

```console
uvx --from 'realized-core[wasm]' realized-core --help
```
