# Symbol Search Commands 06 — Find Markdown Headings

This document teaches the bounded shell capability of finding Markdown heading
lines in a tree.

## 1. Core capability

When a user wants document headings collected from Markdown files, the reusable
capability is heading-line search by root.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "^#+" "$root"
```

The named shell parameter is `$root`.

## 3. Inputs and outputs

Input:

* `root`: the directory tree to search

Output:

* Markdown heading lines with file paths and line numbers

## 4. Natural-language paraphrases

* find Markdown headings under `trials`
* locate heading lines in Markdown files
* search a tree for `#` headings

## 5. One-sentence summary

Finding Markdown headings by root is a reusable documentation-search
capability.
