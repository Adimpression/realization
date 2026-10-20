# Symbol Search Commands 03 — Find Python Class Definition

This document teaches the bounded shell capability of finding a Python class
definition by name.

## 1. Core capability

When a user wants the defining line for a Python class, the reusable capability
is class-definition search by root and class name.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "^class ${symbol}\\b" "$root"
```

The named shell parameters are `$symbol` and `$root`.

## 3. Inputs and outputs

Inputs:

* `symbol`: the Python class name
* `root`: the directory tree to search

Output:

* matching Python class definition lines

## 4. Natural-language paraphrases

* find the Python class definition for `BSSCController` under `/Users/ravindranathakila/service/realized`
* locate where a class is defined
* search for a `class` line by name

## 5. One-sentence summary

Finding a Python class definition by name is a reusable symbol-definition
capability.
