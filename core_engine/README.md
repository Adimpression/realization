# Realized Core Engine

`realized-core-engine` is the independently installable distribution of the
canonical governed realization engine, its state model, host mediation, and
plain SQLite persistence implementation. It also owns constitutional state,
composition-chain, decision-flow, transcript, and replay-comparison projection
over its concrete controller state, together with deterministic
encounter-to-artifact semantics used by optional external Markdown ingestion.
It contains no workstation, UI, gRPC, publication workflow, document-fetching
adapter, or executable entry point.

The engine is source-native under `src/realized_core_engine`. Repository-root
modules that retain historical import paths are compatibility facades and are
not assembled into this distribution. Distribution tests reject undeclared
dependencies, root-level Python modules, and outer application surfaces.

The package depends on `realized-core-runtime` for the dependency-inverted
run/resume lifecycle and on `realized-host-interaction` for the shared,
backend-neutral host substrate. `realized-core` is a separate, thin
command-line composition package that consumes this engine distribution.

## Boundary Of This Distribution

This strangler slice packages execution, state, host mediation, and plain
SQLite behind the public `run`, `resume`, and `inspect` ABI. It is not the
complete ability-delivery boundary:

- governed skill installation remains on the repository entry/exchange surface
- subject scope is not an argument of this public ABI
- `EngineConfiguration.host_interaction_context` may carry an immutable,
  caller-supplied `HostRealizerProvider`; the default composition supplies the
  packaged executor and broker set
- each provider advertises exact executor and broker identities and exposes
  prerequisite inspection before invocation
- `supported_executors` permits frameworks for controller planning; it does not
  install an ability, supply a realizer, admit an ability, or issue authority

An ability document, its admission, its subject visibility, its invocation
grant, and its host realizer remain separate architectural facts. Runtime
dispatch requires an exact declaration-to-realizer identity match; semantic
similarity cannot select an implementation.

## Python API

The public ABI is the typed `realized_core_engine` package. Applications use
`EngineConfiguration`, `EngineInlet`, and the `run`, `resume`, and `inspect`
functions rather than importing the canonical implementation modules directly:

```python
from pathlib import Path

from realized_core_engine import EngineConfiguration, run

result = run(
    "Compute force from mass and acceleration.",
    configuration=EngineConfiguration(
        sqlite_path=Path("state/realization.sqlite3"),
        max_steps=24,
        llm_policy="off",
    ),
)
print(result.summary)
```

`EngineInlet` is the explicit, provenance-bearing boundary for selected
evidence, human contributions, and committed prior results. A conversation
host may attach such an inlet and resume a paused run, but it must not pass an
ambient transcript as evidence. Turn ownership, transcript persistence, and
turn-to-run routing remain outside this engine package.

## Build

```console
uv build core_engine --out-dir dist/core-engine
```

The source distribution contains the package-owned implementation and can
rebuild the wheel without the repository beside it. The build uses ordinary
setuptools `src` discovery; no custom copy or manifest assembly step is
required.
