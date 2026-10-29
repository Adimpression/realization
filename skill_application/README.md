# Realized Skill Application

`realized-skill-application` owns application services that adapt governed
artifacts to the portable skill contracts and operate explicit composition
plans. It sits above semantic, governance, and runtime contracts and below
workstation sessions and entry/exchange formats.

The package exposes four explicit modules:

- `realized_skill_application.normalization` synthesizes portable boundary
  normalization from an artifact's declared inputs and outputs.
- `realized_skill_application.ir` projects a governed artifact into canonical
  skill IR, including lifecycle, compatibility, and hosting metadata.
- `realized_skill_application.composition` analyzes and executes explicit
  skill-composition plans through a caller-supplied invoker.
- `realized_skill_application.projection` classifies a governed artifact into
  its effective portable skill kind without parsing an exchange format.

It does not parse YAML, import foreign tool formats, decide admission or
authority, discover a host realizer, persist artifacts, manage workstation
sessions, invoke an LLM, or provide a launch surface. Those responsibilities
remain with their existing owners.
