# Symbol Search Commands 07 — Find Symbol In File Glob

This document teaches the bounded shell capability of searching for a symbol
within only files that match a given glob.

## 1. Core capability

When a user wants the search limited to one file family, the reusable
capability is glob-constrained symbol search by root, glob, and symbol.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n -g "$glob" "$symbol" "$root"
```

The named shell parameters are `$glob`, `$symbol`, and `$root`.

## 3. Inputs and outputs

Inputs:

* `glob`: the ripgrep file glob such as `*.py`
* `symbol`: the symbol or text to search for
* `root`: the directory tree to search

Output:

* matching lines only from files that satisfy the glob

## 4. Natural-language paraphrases

* search only `*.py` files under `.` for `CrossBoundaryResult`
* constrain a symbol search to one file family
* search one symbol inside files matching a glob

## 5. One-sentence summary

Finding a symbol within a file glob is a reusable filtered-search capability.
