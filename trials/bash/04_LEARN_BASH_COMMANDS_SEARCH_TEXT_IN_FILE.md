# Bash Commands 04 — Search Text In File

This document teaches the bounded shell capability of searching for a pattern
inside a text file.

## 1. Core capability

When a user wants to locate lines containing specific text, the reusable
capability is line-oriented search by pattern and file path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
grep -n "$pattern" "$path"
```

The named shell parameters are `$pattern` and `$path`.

## 3. Inputs and outputs

Inputs:

* `pattern`: the text to search for
* `path`: the file to search

Output:

* matching lines with line numbers

## 4. Natural-language paraphrases

* search for `TODO` in `README.md`
* find lines containing `localhost` in `/etc/hosts`
* grep for a pattern in a file

## 5. One-sentence summary

Searching text in a file is a reusable shell retrieval capability built from a
pattern and a path.
