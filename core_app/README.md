# Realized Core

`realized-core` is the independently installable command-line application for
the canonical governed realization engine and its SQLite state store. The
distribution contains only the narrow command-line composition package; it does not
contain engine modules, workstation code, Flutter/Textual UI, the gRPC host,
or the publication workflow.

The installable core intentionally has three layers:

- `realized-core-runtime` owns the dependency-inverted run/resume lifecycle.
- `realized-core-engine` supplies the canonical domain engine, state model,
  host mediation, and plain SQLite adapter.
- `realized-core` composes those packages behind the narrow
  `run` / `resume` / `inspect` command-line interface.

## Build

Build its source distribution and wheel from the repository checkout:

```console
uv build core_app --out-dir dist/core
```

The resulting application and its declared engine/runtime dependencies are
self-contained with respect to Realized source code. Python dependencies are
installed normally by `uvx` or another package installer.

That statement is limited to the published `run` / `resume` / `inspect`
lifecycle. This distribution does not expose governed `import-skill`, subject
activation, or registration of new host-realizer providers. It executes the
engine's packaged realizers; `--supported-executor` permits advertised packaged
frameworks but does not install or implement one.

## Run

After publishing the three distributions to an index:

```console
uvx realized-core run \
  --prompt "Compute force from mass 3 kg and acceleration 4 m/s^2." \
  --sqlite ./state/realization.sqlite3 \
  --state-out ./state/run.json \
  --llm off
```

The executable supports only the governed core lifecycle:

```console
realized-core run --help
realized-core resume --help
realized-core inspect --help
```

Plain SQLite is always selected by this executable. Vector storage and Wasm
execution are not required. Wasmtime remains an optional extra for callers that
explicitly execute admitted Wasm abilities:

```console
uvx --from 'realized-core[wasm]' realized-core --help
```
