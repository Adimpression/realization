# Symbol Search Commands 04 — Find Import Statements

This document teaches the bounded shell capability of finding import lines that
mention a target module or symbol.

## 1. Core capability

When a user wants to see how a module or symbol is imported, the reusable
capability is import-line search by root and import target.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "^(from|import) .*${module}" "$root"
```

The named shell parameters are `$module` and `$root`.

## 3. Inputs and outputs

Inputs:

* `module`: the imported module or symbol to match
* `root`: the directory tree to search

Output:

* matching import lines with file paths and line numbers

## 4. Natural-language paraphrases

* find import statements mentioning `json` under `.`
* locate import lines for one module
* search for Python imports mentioning a target

## 5. One-sentence summary

Finding import statements by module and root is a reusable code-structure
search capability.
