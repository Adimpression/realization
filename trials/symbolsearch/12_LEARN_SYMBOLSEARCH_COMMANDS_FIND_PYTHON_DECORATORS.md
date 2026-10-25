# Symbol Search Commands 12 — Find Python Decorators

This document teaches the bounded shell capability of finding Python decorator
lines.

## 1. Core capability

When a user wants decorator usage lines collected from a Python tree, the
reusable capability is decorator search by root.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "^@" "$root"
```

The named shell parameter is `$root`.

## 3. Inputs and outputs

Input:

* `root`: the directory tree to search

Output:

* decorator lines with file paths and line numbers

## 4. Natural-language paraphrases

* find Python decorators under `.`
* locate `@` decorator lines in a codebase
* search a tree for decorator usage

## 5. One-sentence summary

Finding Python decorator lines by root is a reusable code-structure search
capability.
