# URL Learning Artifacts Implementation

## Purpose

This document gives implementation guidance for adding URL-origin learning artifacts to the repository without weakening subject continuity, source provenance, or later publication quality.

It is intentionally suggestive rather than over-prescriptive.

The core implementation rule is:

- admit markdown
- preserve more than markdown

## Why This Deserves A Dedicated Layer

The repository already has:

- durable `LearningContext`
- durable source records
- deterministic subject projection
- deterministic publication projection

What it does not yet have is a first-class URL acquisition and source-bundle layer.

Without that layer:

- URL learning becomes lossy too early
- images and illustrations become weakly preserved
- review sees less than what was actually fetched
- publication remains unnecessarily compiler-like

So the missing implementation slice is not “fetch URL and write one markdown file”.

It is:

- acquire
- preserve
- extract
- structure
- index
- admit

## Suggested First-Cut Stack

Implement the first cut with:

- Playwright
- Trafilatura
- filesystem-backed source bundles
- SQLite FTS5

Why this first:

- it is enough to solve the real problem
- it fits the repository’s current Python and filesystem-heavy model
- it avoids overcommitting to a heavy archival stack too early

## Current State

The first URL-learning cut now exists.

It already provides:

- Playwright-based browser acquisition
- Trafilatura-based canonical markdown extraction
- persisted source bundles with `rendered.html`, `screenshot.png`, `elements.json`, `asset-manifest.json`, and preserved downloaded assets
- admission through the existing `source -> delta -> context` path instead of a parallel subject-update path

Current operator-facing inspection reality:

- the fetched material is already inspectable on disk inside the staged source bundle
- the canonical text body is persisted as staged source markdown
- the richer bundle artifacts are persisted alongside it
- the workstation now exposes a first staged-source inventory plus selected-source detail pane in `Gather`
- the first default per-subject source set is now persisted as `All Gather Sources`
- the first operator-managed selected source sets are now live on top of `All Gather Sources`
- reopening one specific selected staged source inside gather-scoped chat is now live as a first-cut source-layer action
- the latest assistant reply can now be applied back as a new staged `llm_curation` revision without admitting it into corpus
- selected source-set curation is now live through:
  - `@llm` for source-set metadata curation
  - `=` for manual source-set metadata curation
- the first selected source-set discovery flow is now live through:
  - `Find Sources In Chat` using the set's saved query/topic
  - `Apply Discovered Sources` to stage new source records or link existing ones back into that set
- URL-backed staged-source refresh is now live through:
  - `Refresh Selected Source`
  - a new staged `refresh` revision
- source-set sync is now live through:
  - `Sync Source Set`
  - batch URL refresh over the selected source set's URL-backed staged sources
- the first selected-source merge-back flow is now live through:
  - `Merge Back In Chat`
  - `Apply Merge-Back Proposal` to write a staged `merge` revision
- the first selected source-set merge-back flow is now live through:
  - `Merge Source Set In Chat`
  - `Apply Source-Set Merge-Back` to update `SourceCollection` metadata only
- the selected staged-source detail pane now shows revision history and a latest-change summary against the previous revision when one exists
- `Change Diff Baseline (...)` now lets operators browse the selected staged source against older revisions
- the selected staged-source detail pane now shows a first deterministic export proposal preview from current governed learnings without auto-applying a merge
- the selected source-set detail pane now shows a first deterministic source-set export preview from current governed learnings without auto-applying a merge
- richer source-side export-history browsing and fuller governed multi-source diff/export proposal application are still future work

The main work still left from this document is:

- SQLite FTS5 indexing over URL-origin source bundles
- governed preview/confirmation in workstation research before admission
- richer source-side query/reuse over the persisted structured sidecars
- widening the new staged-source-first URL flow beyond the current first saved-query discovery/refresh/sync/merge cuts into richer source-side revision/query/reuse operations

## Suggested Progression

Before the next deeper ingestion slice, preserve this boundary:

- URL capture may create or refresh one staged source bundle in `Gather`
- that staged bundle is still only a source
- explicit import should be what creates or updates admitted `LearningSource`

### Phase 1. Add URL Source Bundles To `LearningContext`

This phase is now complete through a staged-source-first version of the flow:

- URL capture writes staged source metadata, markdown, and bundle artifacts into Gather
- explicit import later creates admitted `LearningSource`

Introduce a URL-origin source flow that writes:

- one `LearningSource` record
- one canonical markdown body
- one rendered HTML capture
- one screenshot
- one asset manifest

Why:

- this is the minimum useful fidelity step
- it keeps admission readable while preserving the rendered source state

Suggested changes:

- extend `VALID_LEARNING_SOURCE_KINDS` in [learning_context.py](learning_context.py) to include one URL-specific kind such as `url`
- extend source metadata rather than replacing the current `LearningSource` shape
- keep `sources/<source-id>.md` as the canonical text ingress body
- add a sibling source bundle directory for related artifacts

Suggested persistence shape:

```text
sources/
  <source-id>.json
  <source-id>.md
  <source-id>/
    rendered.html
    screenshot.png
    asset-manifest.json

This is also the current practical answer to “what got fetched?” today:

- the canonical markdown body
- the source metadata JSON
- the richer artifact bundle rooted under the same `source-id`
```

### Phase 2. Add Structured Sidecars

Add one `elements.json` sidecar produced either from:

- Trafilatura structured output
- Unstructured typed elements

Why:

- later controller-assisted research and publication work should not reason only over flattened markdown
- typed structural records make figures, headings, lists, and tables easier to reason about

Do not make structured sidecars mandatory for the first cut if that slows adoption.

Make them additive.

### Phase 3. Add Asset Preservation

Preserve relevant images and illustration assets into:

- `sources/<source-id>/assets/`

and record them in:

- `asset-manifest.json`

Why:

- images and diagrams may carry educational meaning
- markdown extraction alone may lose source meaning
- publication may later need controlled reuse of those visuals or at least their provenance

The manifest should know:

- original asset URL
- local stored path
- content hash
- alt text when available
- caption or surrounding text when available
- MIME type

### Phase 4. Add SQLite FTS5 Indexing

Create one local indexing layer for URL-origin sources.

Suggested index surfaces:

- markdown body text
- structured element text
- image alt text
- image captions
- source title
- source URL

Why:

- subject-scoped search becomes much stronger
- later subject-bound controller/runtime bootstrap has better source-side retrieval
- review and publication can query source support more directly

Keep the index as a projection, not the primary durable store.

The primary durable store should remain:

- filesystem bundle plus source metadata JSON

### Phase 5. Add Subject Workflow Entry

The first-cut URL learning path now exists inside workstation research.

The remaining workflow move is to make it governed before admission.

Possible workflow:

1. enter URL
2. fetch and render
3. preview extracted markdown
4. preview screenshot and source metadata
5. confirm admission

Why:

- the user should see what was fetched before it mutates subject state
- controller- or publication-grade intelligence still depends on governed admission

## Suggested Repository Insertion Points

### Source Model Layer

Relevant file:

- [learning_context.py](learning_context.py)

Suggested role:

- extend `LearningSource` metadata for URL-origin captures
- add one URL source kind
- preserve body markdown plus bundle-relative artifacts

Why:

- `LearningContext` is the durable admitted subject continuity root
- but the next correction is to let URL capture land first in a staged gather source bundle before explicit admission

### Fetch And Acquisition Layer

Likely new module:

- `url_learning_capture.py`

Suggested role:

- fetch via Playwright
- normalize redirects/final URL
- save rendered HTML
- save screenshot
- call markdown extraction
- save asset manifest
- return one structured capture result for admission

Why:

- the repository should not bury URL-fetch logic inside UI code or markdown-only codepaths

### External Markdown Learning Bridge

Relevant files:

- [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
- [workstation/learning_capture.py](workstation/learning_capture.py)

Suggested role:

- reuse existing markdown admission mechanics once URL extraction has produced the canonical markdown body
- avoid forking a second admission model

Why:

- URL learning should converge into the same `source -> delta -> context` path, not invent a parallel subject-update path

### Workstation Gather Layer

Relevant file:

- [workstation/subject_workflow.py](workstation/subject_workflow.py)

Suggested role:

- surface URL capture as one gather ingress action
- show preview of:
  - staged source metadata
  - extracted markdown
  - screenshot and asset bundle
  - whether the captured source has already been imported
  - whether the captured source has corpus-side merge-back proposals pending
  - asset count and basic source metadata
- require explicit confirmation before admission

Why:

- the user should understand what is being admitted
- sharper research comes from visible source shape, not hidden conversion

### Publication Layer

Relevant files:

- [publication_projection.py](publication_projection.py)
- [publication.py](publication.py)

Suggested role:

- retain source linkage from claims/sections back to URL-origin sources
- later allow figure-aware or illustration-aware publication logic

Why:

- publication should be able to remain honest about visual or structured source provenance

## Suggested `LearningSource` Metadata Additions

The existing `LearningSource` record should probably gain optional metadata such as:

- `origin_url`
- `final_url`
- `fetched_at_epoch_ms`
- `rendered_html_relpath`
- `self_contained_html_relpath`
- `screenshot_relpath`
- `elements_relpath`
- `asset_manifest_relpath`
- `fetch_tool`
- `extract_tool`
- `content_hash`

Why:

- most of the needed semantics fit naturally as source metadata
- this keeps the first cut compatible with the current source record shape

## Suggested Structured Sidecar Shape

The sidecar does not need a huge ontology at first.

It only needs enough structure to be useful later.

Suggested minimal element record:

- `element_id`
- `kind`
- `text`
- `sequence_index`
- `metadata`

Useful `kind` values:

- `title`
- `heading`
- `paragraph`
- `list_item`
- `table`
- `caption`
- `figure_reference`
- `code_block`

Why:

- this is enough to support later review/publication assistance without forcing a giant schema too early

## Suggested Asset Manifest Shape

Each asset record should know:

- `asset_id`
- `source_url`
- `local_relpath`
- `mime_type`
- `content_hash`
- `alt_text`
- `caption_text`
- `sequence_index`

Why:

- publication and review may need to understand whether an image is only decorative or substantively explanatory

## Retrieval Guidance

The controller/runtime should not pull URL source material ambiently from one global soup.

Instead:

- keep URL-origin retrieval subject-aware
- later allow imported-subject source bundles through the same bounded subject-import machinery

Why:

- URL learning should strengthen subject-bounded research
- it should not become another uncontrolled global retrieval surface

## Recommended Tool Adoption Order

### First

- Playwright
- Trafilatura
- SQLite FTS5

Why:

- highest value
- lowest conceptual overhead
- fits current repository shape

### Second

- Unstructured

Why:

- valuable once typed source elements start paying for themselves

### Third

- SingleFile

Why:

- useful when page-faithful preservation becomes important per source

### Later

- ArchiveBox or Browsertrix

Why:

- stronger archival or crawl-grade tooling is useful, but heavier
- this should wait until the repository truly needs archival breadth rather than first-cut source bundles

## What Not To Do

- do not store only one markdown file and discard everything else
- do not store binary image blobs inside SQLite as the primary representation
- do not let URL-origin source retrieval become ambient global retrieval
- do not skip preview/confirmation for source admission
- do not make publication depend on ephemeral fetch results rather than persisted source bundles

## One-Sentence Summary

Implement URL learning as one governed source-bundle pipeline: browser-grade acquisition, canonical markdown extraction, structured sidecars, preserved assets, SQLite indexing, and explicit admission into `LearningContext`.
