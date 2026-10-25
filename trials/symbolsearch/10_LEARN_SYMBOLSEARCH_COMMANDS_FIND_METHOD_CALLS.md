# Symbol Search Commands 10 — Find Method Call Pattern

This document teaches the bounded shell capability of finding method-call
patterns in source files.

## 1. Core capability

When a user wants lines that call a specific method pattern, the reusable
capability is method-call search by root and pattern.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "$pattern" "$root"
```

The named shell parameters are `$pattern` and `$root`.

## 3. Inputs and outputs

Inputs:

* `pattern`: the call pattern such as `\\.run\\(`
* `root`: the directory tree to search

Output:

* matching method-call lines with file paths and line numbers

## 4. Natural-language paraphrases

* find lines containing the method call `.run(` under `.`
* search for a method-call pattern
* find call sites that match one textual method pattern

## 5. One-sentence summary

Finding method-call patterns by pattern and root is a reusable call-site search
capability.
