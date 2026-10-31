# Markdown Learning Vs Runtime Reduction

## Purpose

This document makes one architectural distinction explicit:

- `markdown-learn` is not the same control flow as the governed runtime reduction loop
- `import-skill` is not the same control flow as either of those

They all produce or use artifacts, but they do different jobs.

## The Three Paths

### 1. Runtime reduction

This is the normal governed control loop for an active prompt.

Where:
- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)

Main functions:
- [run()](governed_semantic_reduction_runtime.py#L34)
- [resume()](governed_semantic_reduction_runtime.py#L98)
- [reduce_not()](governed_semantic_reduction_runtime.py#L216)

When it is used:
- `realized-core run`
- `realized-core resume`
- any live governed prompt resolution path

Why it exists:
- reduce a current non-achievedness recursively
- manage frontier ordering
- decompose or refine live semantic nodes
- commit closure, pause, or incompletion on the active run

This is the recursive `Not` reduction loop.

### 2. Markdown learning

This is a bounded document-to-artifact learning pipeline.

Where:
- [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
- [markdown_learning_artifact_semantics.py](markdown_learning_artifact_semantics.py)

Main function:
- [learn_from_markdown_document()](external_markdown_learning_pipeline.py#L277)

When it is used:
- `realized-compatibility markdown-learn`
- trial corpus learning from `.md` lessons

Why it exists:
- parse a source document
- derive encounters, reusable relations, and executable artifacts
- functionalize fenced code or equation-bearing content
- persist reusable artifacts into the store

What it does not do:
- it does not call [reduce_not()](governed_semantic_reduction_runtime.py#L216)
- it does not enter the live recursive frontier loop

Why it is separate:
- the input is an external source document, not an active live non-achievedness
- the output is a bounded learned corpus, not direct closure of a root prompt
- learning needs document parsing, encounter extraction, and artifact shaping steps that do not belong in the live runtime loop

So markdown learning still performs semantic deconstruction, but it is a learning pipeline, not the runtime reducer.

Workstation note:

- this separation does not forbid later bounded runtime-style decomposition during `Itemize`
- it only means `Gather` / markdown learning is not itself the `reduce_not` loop
- the workstation may therefore:
  - learn or admit a markdown source in `Gather`
  - later decompose weakly structured source prose into candidate itemized material in `Itemize`
  - keep those decomposition results at the candidate layer until operator review and later drafting

### 3. Skill import

This is installation of already-declared artifacts.

Where:
- [skill_schema_io.py](skill_schema_io.py)
- [governed_skill_installation.py](governed_skill_installation.py)

Main functions:
- [artifact_from_skill_document()](skill_schema_io.py)
- [handle_import_skill_command()](governed_skill_installation.py)

When it is used:
- `main.py import-skill`
- governed bundle installation from `skill.yaml`

Why it exists:
- hydrate the portable skill schema into canonical artifacts
- evaluate governance and admission
- persist the installed artifacts

What it does not do:
- it does not call [learn_from_markdown_document()](external_markdown_learning_pipeline.py#L277)
- it does not call [reduce_not()](governed_semantic_reduction_runtime.py#L216)

Why it is separate:
- the skill bundle is already the learned or authored artifact boundary
- import is an installation path, not a derivation path

## Why This Separation Is Correct

The controller has to preserve three different abstractions:

1. runtime reasoning
- recursive reduction over live `Not`s

2. source learning
- bounded extraction from external markdown

3. artifact installation
- governance-aware persistence of already-formed skills

If these are collapsed into one loop:
- the runtime reducer gets polluted with document-ingestion concerns
- import becomes semantically ambiguous
- performance and governance become harder to reason about

## Design Rule

Use the runtime reducer when the system is trying to close a live non-achievedness.

Use markdown learning when the system is turning a source document into reusable artifacts.

Use skill import when the system is installing an already-formed skill declaration or bundle.

Those paths may share downstream persistence, governance, retrieval, and execution surfaces, but they should not be confused as one control loop.
