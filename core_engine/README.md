# Realized Core Engine

`realized-core-engine` is the independently installable distribution of the
canonical governed realization engine, its state model, host mediation, and
plain SQLite persistence implementation. It contains no workstation, UI,
gRPC, publication workflow, or executable entry point.

The engine remains single-source in the repository root during the strangler
migration. `module_manifest.txt` declares the exact transitive root-module
closure assembled into this wheel; it is not a second source tree. Tests
recompute the closure and reject undeclared dependencies or outer application
surfaces.

The package depends on `realized-core-runtime` for the dependency-inverted
run/resume lifecycle. `realized-core` is a separate, thin command-line
composition package that consumes this engine distribution.

## Boundary Of This Distribution

This first strangler slice packages execution, state, built-in host mediation,
and plain SQLite behind the public `run`, `resume`, and `inspect` ABI. It is not
the complete ability-delivery boundary:

- governed skill installation remains on the repository entry/exchange surface
- subject scope is not an argument of this public ABI
- host realizers are the packaged executor and broker set, not
  caller-registered providers
- `supported_executors` permits those packaged frameworks; it does not install
  an ability, register an executor, or prove that an external binary exists

An ability document, its admission, its subject visibility, and its host
realizer remain separate architectural facts.

## Python API

The public ABI is the typed `realized_core_engine` package. Applications use
`EngineConfiguration` and the `run`, `resume`, and `inspect` functions rather
than importing the canonical implementation modules directly:

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

## Build

```console
uv build core_engine --out-dir dist/core-engine
```

The source distribution embeds the exact canonical module closure declared by
`module_manifest.txt`, so a wheel can be rebuilt from the archive without the
repository beside it. In a repository checkout, those modules remain
single-source at the root. Assembly clears generated Python build output before
copying the manifest closure so removed modules cannot leak from a stale build
directory.
