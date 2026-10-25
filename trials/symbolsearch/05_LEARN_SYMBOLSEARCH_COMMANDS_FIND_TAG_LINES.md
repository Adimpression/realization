# Symbol Search Commands 05 — Find Tagged Comment Lines

This document teaches the bounded shell capability of finding tagged comment
lines such as TODO or FIXME.

## 1. Core capability

When a user wants outstanding marked lines collected from a codebase, the
reusable capability is tag-line search by root and tag.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "$tag" "$root"
```

The named shell parameters are `$tag` and `$root`.

## 3. Inputs and outputs

Inputs:

* `tag`: the textual marker such as `TODO` or `FIXME`
* `root`: the directory tree to search

Output:

* matching tagged lines with file paths and line numbers

## 4. Natural-language paraphrases

* find all TODO lines under `.`
* search a tree for FIXME comments
* collect tagged comment lines

## 5. One-sentence summary

Finding tagged comment lines by tag and root is a reusable maintenance-search
capability.
