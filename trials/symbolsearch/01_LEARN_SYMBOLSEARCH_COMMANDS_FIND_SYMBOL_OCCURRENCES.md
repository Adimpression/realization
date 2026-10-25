# Symbol Search Commands 01 — Find Symbol Occurrences

This document teaches the bounded shell capability of finding occurrences of a
symbol beneath a root directory.

## 1. Core capability

When a user wants every textual occurrence of one symbol in a tree, the reusable
capability is recursive symbol search by root and symbol.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "$symbol" "$root"
```

The named shell parameters are `$symbol` and `$root`.

## 3. Inputs and outputs

Inputs:

* `symbol`: the text or symbol to find
* `root`: the directory tree to search

Output:

* matching lines with file paths and line numbers

## 4. Natural-language paraphrases

* find every occurrence of `BSSCController` under `.`
* search a tree for one symbol
* locate all textual references to a symbol

## 5. One-sentence summary

Finding symbol occurrences by symbol and root is a reusable code-search
capability.
