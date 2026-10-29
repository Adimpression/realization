# Realized Exchange

`realized-exchange` is Realization's entry-layer boundary for user-facing
artifact and portable-skill representations. It owns:

- artifact bundle YAML parsing and rendering;
- portable-skill schema hydration and validation;
- portable-skill compilation into artifact-centered canonical IR;
- canonical skill bundle export and deterministic exchange filenames;
- compatibility import and export for supported foreign representations;
- learning-context derived-skill compilation and YAML materialization; and
- portable skill-registry projection and its CLI adapter;
- governed run-bundle construction, governance snapshotting, and YAML
  loading/rendering; and
- external Markdown document ingestion and explicit installation of its
  optional controller extension methods; and
- the concrete workstation exchange provider composed by the CLI entrypoint.

The workstation consumes this capability through its transport-neutral
`SkillExchangeProvider` contract. Lower workstation packages therefore do not
import YAML adapters or repository-root compatibility modules.

Translation is not governance. This package does not admit an artifact, decide
current use, grant authority, select an ability, bind a host realizer, or
execute an operation. Callers pass translated values to the established
governance, controller, and runtime owners for those decisions.

The historical root modules `side`, `side_runtime_dependencies`,
`skill_schema_io`, `skill_export_projection`, `skill_compatibility_import`,
`skill_compatibility_export`, `skill_compiler`, `learning_context`, and
`learning_context_skill_projection`, `skill_registry`, and `run_bundle_io`
remain exact module-identity aliases during the qualification cycle. The
historical `external_markdown_learning_pipeline` path is likewise an exact
alias for the package-owned Markdown adapter. New production code imports
canonical package APIs.
