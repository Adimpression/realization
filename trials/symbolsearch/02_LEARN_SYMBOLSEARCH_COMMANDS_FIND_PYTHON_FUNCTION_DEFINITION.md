# Symbol Search Commands 02 — Find Python Function Definition

This document teaches the bounded shell capability of finding a Python function
definition by name.

## 1. Core capability

When a user wants the defining line for a Python function, the reusable
capability is definition search by root and function name.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "^def ${symbol}\\(" "$root"
```

The named shell parameters are `$symbol` and `$root`.

## 3. Inputs and outputs

Inputs:

* `symbol`: the Python function name
* `root`: the directory tree to search

Output:

* matching Python function definition lines

## 4. Natural-language paraphrases

* find the Python function definition for `run` under `.`
* locate where a Python function is defined
* search for a `def` line by function name

## 5. One-sentence summary

Finding a Python function definition by name is a reusable symbol-definition
capability.
