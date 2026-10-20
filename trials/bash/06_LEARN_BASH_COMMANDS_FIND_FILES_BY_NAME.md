# Bash Commands 06 — Find Files By Name

This document teaches the bounded shell capability of finding files under a
root directory by a specific file name pattern.

## 1. Core capability

When a user wants to locate matching files in a directory tree, the reusable
capability is recursive file search by root and name.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
find "$root" -type f -name "$name"
```

The named shell parameters are `$root` and `$name`.

## 3. Inputs and outputs

Inputs:

* `root`: the directory tree to search
* `name`: the file name or glob pattern to match

Output:

* matching file paths printed to standard output

## 4. Natural-language paraphrases

* find files named `README.md` under `/Users/ravindranathakila/service/realized`
* search `/tmp` for files called `config.json`
* locate files by name beneath a root directory

## 5. One-sentence summary

Finding files by root and name is a reusable shell discovery capability.
