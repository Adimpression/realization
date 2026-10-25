# Symbol Search Commands 09 — Find Exact Word References

This document teaches the bounded shell capability of finding exact word
references to a term.

## 1. Core capability

When a user wants only whole-word matches rather than partial substrings, the
reusable capability is exact-word search by root and symbol.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n -w "$symbol" "$root"
```

The named shell parameters are `$symbol` and `$root`.

## 3. Inputs and outputs

Inputs:

* `symbol`: the exact word to find
* `root`: the directory tree to search

Output:

* whole-word matches with file paths and line numbers

## 4. Natural-language paraphrases

* find exact word references to `artifact` under `.`
* search only exact matches for one word
* avoid partial substring matches in a code search

## 5. One-sentence summary

Finding exact word references by symbol and root is a reusable precise-search
capability.
