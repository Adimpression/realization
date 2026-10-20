# Help

## How `reduce_not` Links To Workstation, Gather, Subject, And Publication

Short answer:

- `reduce_not` is directly central to the controller runtime.
- it is not the core engine of the workstation `Gather`, `Itemize`, `Draft`, `Review`, `Subject`, or `Publication` flows.
- the connection is indirect, mainly through nested controller usage and later artifact reuse.

## What `reduce_not` Actually Is

`reduce_not` lives in the governed reduction runtime:

- [governed_semantic_reduction_runtime.py#L261](governed_semantic_reduction_runtime.py#L261)

It is entered from the governed runtime loop:

- [governed_semantic_reduction_runtime.py#L46](governed_semantic_reduction_runtime.py#L46)
- [governed_semantic_reduction_runtime.py#L143](governed_semantic_reduction_runtime.py#L143)

That means:

- `reduce_not` is the recursive `Not` reducer for one live controller run.
- it manages decomposition, refinement, reflection/contemplation policy, child reduction, and closure/pause/incompletion.

## How It Links To Workstation

Ordinary workstation chat is not `reduce_not`.

The normal workstation chat turn is host-owned:

- [workstation/runtime_core/src/workstation/runtime/core/session.py](workstation/runtime_core/src/workstation/runtime/core/session.py)
- [workstation/llm_driver.py#L269](workstation/llm_driver.py#L269)

That path is:

- `workstation session`
- `OpenAI/tool loop`
- `workstation capabilities`

The controller link appears only when workstation code explicitly boots a nested controller through the narrow runtime facade:

- [runtime_controller_api.py#L30](runtime_controller_api.py#L30)

Examples:

- [workstation/capabilities.py#L2944](workstation/capabilities.py#L2944)
- [host_brokers.py#L1142](host_brokers.py#L1142)

Important nuance:

- nested controller bootstrap does not automatically mean the full `run()` / `reduce_not()` loop is entered.
- some nested workstation paths use controller helper methods such as [main.py#L2818](main.py#L2818) `execute_function_artifact(...)` rather than the live recursive reduction loop itself.

So the correct statement is:

- workstation can reach controller behavior
- but workstation chat is not itself the `reduce_not` runtime

## How It Links To Gather

Gather is not driven by `reduce_not`.

The live workstation research path is owned by the subject workflow and learning-capture path:

- [workstation/subject_workflow.py#L682](workstation/subject_workflow.py#L682)
- [workstation/subject_workflow.py#L715](workstation/subject_workflow.py#L715)
- [workstation/learning_capture.py](workstation/learning_capture.py)
- [learning_context.py#L660](learning_context.py#L660)

That path is:

- `chat or markdown`
- `gather admission`
- `LearningContext persistence`

This separation is already stated explicitly in:

- [MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md#L39](MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md#L39)
- [MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md#L118](MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md#L118)

So gather admission is a corpus-maintenance path, not a call into `reduce_not`.

## How It Links To Subject

Subject truth lives in the subject corpus `LearningContext`, not in the controller run state:

- [learning_context.py#L660](learning_context.py#L660)

The controller does have a function named `load_learning_context`, but that is different:

- [governed_prior_learning_reuse.py#L731](governed_prior_learning_reuse.py#L731)

That controller-side function means:

- load relevant prior reusable artifacts from the configured artifact store
- make them available for later governed reuse during controller runtime

It does **not** mean:

- load the subject corpus `LearningContext` from `corpus/<subject>/...`

This naming collision matters. It is the main reason people over-connect `reduce_not` to subject maintenance.

The real bridge is weaker:

- subject gathering can produce persisted artifacts and skill-shaped projections
- later controller runs can retrieve and reuse those artifacts
- that reused material may influence later `reduce_not` behavior

Those projections establish bounded visibility and provenance. They do not by
themselves install or admit a governed ability or provide its host realizer.

So the relation is:

- `Subject -> reusable artifacts -> controller prior-learning reuse -> possible later reduction support`

not:

- `Subject -> reduce_not`

## How It Links To Publication

Publication is downstream of subject corpus, not downstream of `reduce_not`.

The publication build path is:

- [workstation/subject_workflow.py#L850](workstation/subject_workflow.py#L850)
- [publication_projection.py#L413](publication_projection.py#L413)

That means:

- load subject `LearningContext`
- project it into a publication graph
- render and persist report artifacts

So publication is a subject-projection pipeline, not a controller-reduction pipeline.

## Clean Mental Model

Use this model:

- `reduce_not`
  Controller runtime for reducing one live non-achievedness.
- `Workstation`
  Host shell that may call tools and may sometimes bootstrap a nested controller.
- `Gather`
  Admission workflow into subject corpus.
- `Subject`
  Durable maintained corpus.
- `Publication`
  Deterministic projection from subject corpus.

The real linkage is therefore:

- `Workstation -> optional nested controller -> controller helpers and sometimes governed reduction`
- `Gather -> Subject`
- `Subject -> Publication`
- `Subject-derived artifacts -> artifact store -> prior-learning reuse -> later controller support`

## One-Sentence Summary

`reduce_not` is the controller's live recursive reasoning loop; workstation gather and publication are separate corpus and projection workflows that may feed artifacts into later controller reuse, but they are not themselves driven by `reduce_not`.
