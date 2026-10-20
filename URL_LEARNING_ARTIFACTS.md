# URL Learning Artifacts

## Purpose

This document defines the formal position for URL-origin learning artifacts in the repository.

The need is straightforward:

- the workstation should be able to learn from URLs
- fetched material should not collapse immediately into plain markdown only
- the stored result should remain useful for research, review, publication, replay, and audit
- images and illustrations should remain first-class preserved source material

The repository already has durable subject corpus storage through `LearningContext`.

What is missing is a first-class position for:

- URL fetch
- rendered capture
- extracted markdown
- structured source elements
- associated image and illustration preservation

## Core Position

URL learning should use a layered source representation, not a single-format one.

The recommended shape is:

1. faithful capture
2. canonical extracted markdown
3. structured sidecar records
4. preserved image and illustration assets

This means one fetched URL should not become only:

- one markdown file

It should become a bounded source bundle containing:

- what was fetched
- what was rendered
- what was extracted
- what assets were preserved
- what metadata and structure were observed

## Why Markdown Alone Is Not Enough

Markdown is good for:

- admission into subject workflows
- human review
- diffability
- deterministic publication projection inputs

Markdown alone is weak for:

- layout-sensitive evidence
- image and illustration provenance
- replay of rendered source state
- structured extraction of headings, figures, captions, lists, and tables
- later controller-assisted reasoning over source structure

So markdown should remain the canonical readable text projection, but not the only stored source artifact.

## Recommended Open Source Technology Shape

The strongest practical default for this repository is:

- Playwright
- Trafilatura
- SQLite FTS5
- filesystem-backed asset storage

Optional archival or fidelity tools can be added depending on how strong the capture requirement becomes.

## Primary Recommendation

### Playwright

Use Playwright for browser-grade fetch and render.

Why:

- modern pages are often JS-rendered
- lazy-loaded content and images need real browser execution
- screenshots are often useful for review and publication provenance
- DOM capture after rendering is materially better than raw `requests.get(...)` for many sites

Playwright should be treated as the acquisition and rendering layer.

### Trafilatura

Use Trafilatura for canonical article/text extraction into markdown.

Why:

- it is strong for article-like content
- it can emit markdown and structured outputs
- it is lighter and simpler than building custom extraction logic for every page family

Trafilatura should be treated as the primary markdown extraction layer.

### SQLite FTS5

Use SQLite FTS5 for local structured search over fetched URL sources.

Why:

- the repository already uses SQLite heavily
- it gives good full-text search without adding a second datastore
- it can index markdown, extracted elements, captions, alt text, and asset metadata
- it fits subject-scoped and later subject-import-aware retrieval

SQLite should remain a search and metadata index, not the only source-of-truth store for binary assets.

### Filesystem Asset Store

Use the filesystem as the durable store for:

- source markdown
- rendered HTML
- self-contained HTML snapshots
- screenshots
- extracted images
- asset manifests

Why:

- large binary assets and HTML snapshots are more natural on disk than inline in SQLite
- it preserves inspectability by hand
- it aligns with the repository’s existing `LearningContext` corpus home model

## Secondary or Optional Tools

### Unstructured

Use Unstructured when typed content elements are needed.

This becomes useful if the repository wants source-side typed records such as:

- title
- narrative text
- list item
- table
- caption
- figure-related text

Why:

- markdown alone is not enough when the controller or publication layer wants structured source semantics
- typed elements can later support sharper review and publication planning

Unstructured is a good secondary layer, not necessarily the first required layer.

### SingleFile

Use SingleFile when the goal is faithful single-page offline preservation.

Why:

- it keeps the page and its resources together in one HTML artifact
- it is strong for preserving what the user actually saw
- it helps with replay, audit, and image retention

SingleFile is especially useful when a URL source should remain inspectable as one durable artifact.

### ArchiveBox

Use ArchiveBox if the repository wants multi-format archival per URL.

Why:

- it already thinks in terms of snapshots and many extractors
- it preserves multiple output forms such as DOM, screenshot, PDF, and WARC-related artifacts
- it is useful for archival-grade source capture

ArchiveBox is stronger than needed for the smallest first cut, but useful if URL learning grows into long-lived archival ingestion.

### Browsertrix Crawler

Use Browsertrix when the problem becomes crawl-grade rather than single-page-grade.

Why:

- it supports browser-driven crawling
- it supports screenshots and text-to-WARC behavior
- it is more appropriate for large capture jobs and replay-oriented archival flows

Browsertrix is probably later work unless the repository starts learning from large URL sets or dynamic sites at scale.

## Recommended Repository Storage Shape

The repository already persists:

- `sources/<source-id>.json`
- `sources/<source-id>.md`

That should evolve into one source bundle shape per URL-origin source.

Suggested shape:

```text
corpus/<subject-id>/
  sources/
    <source-id>.json
    <source-id>.md
    <source-id>/
      rendered.html
      singlefile.html
      elements.json
      screenshot.png
      assets/
        image-001.png
        image-002.jpg
      asset-manifest.json
```

The important point is not the exact filenames.

The important point is:

- one durable metadata record
- one canonical markdown body
- one optional high-fidelity rendered capture
- one structured element sidecar
- one asset area for images and illustrations

## What `source.json` Should Know

For URL-origin learning, the source record should know at least:

- original URL
- final URL after redirects
- fetch timestamp
- fetch method
- media type
- title
- content hash
- screenshot path
- rendered HTML path
- self-contained HTML path if present
- extracted element path if present
- asset manifest path
- extraction toolchain versions
- any admission-specific metadata

Why:

- source provenance becomes stronger
- replay becomes possible
- review can inspect source fidelity
- publication can disclose source shape honestly

## Images And Illustrations

Images and illustrations should not be treated as disposable fetch-time decoration.

They may carry:

- figures
- diagrams
- captions
- explanatory labels
- embedded equations
- process illustrations

So the system should preserve:

- image URLs
- local stored asset paths
- alt text
- captions when extractable
- source position or relation when available

Why:

- publication may later depend on them
- controller-assisted review may need them
- plain markdown extraction may omit information the illustration carries

## Recommended Operational Shape

For the current repository, the clean operational path is:

1. fetch and render URL with Playwright
2. save one rendered HTML capture
3. save one screenshot
4. extract canonical markdown with Trafilatura
5. optionally extract typed elements with Unstructured
6. store image assets and one asset manifest
7. index textual surfaces in SQLite FTS5
8. admit the markdown and source metadata into `LearningContext`

This keeps the admission story readable while preserving enough fidelity for later sharper research and publication behavior.

## Why This Matters For Gather

Gather should not depend only on flattened markdown.

Better source bundles allow:

- clearer source review
- better comparison of extracted markdown against rendered source
- stronger image-aware interpretation
- better follow-up questions and later re-extraction

That makes subject admission sharper.

## Why This Matters For Publication

Publication should not be a dumb compiler over lossy input.

If the source layer retains:

- structure
- assets
- rendered state
- provenance

then publication can later become more intelligent without becoming unauditable.

It can:

- check source support more precisely
- preserve image/illustration linkage
- distinguish text-derived claims from figure-derived support
- improve transclusion and source honesty

## Recommended First Cut

The first cut should remain small.

Start with:

- Playwright
- Trafilatura
- filesystem asset bundle
- SQLite FTS5 metadata/search index

Later, add:

- Unstructured for typed element extraction
- SingleFile for one-file page preservation
- ArchiveBox or Browsertrix only if the archive/crawl need becomes dominant

## One-Sentence Summary

The right design is:

one URL should become a durable source bundle containing faithful capture, canonical markdown, structured sidecars, and preserved assets, with SQLite indexing over the textual and structural surfaces.
