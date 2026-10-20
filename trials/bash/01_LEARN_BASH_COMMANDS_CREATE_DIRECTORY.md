# Bash Commands 01 — Create Directory

This document teaches the bounded shell capability of creating a directory,
including any missing parent directories.

## 1. Core capability

When a user wants a filesystem location to exist before saving files into it,
the reusable capability is directory creation by path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
mkdir -p "$path"
```

The named shell parameter is `$path`.

## 3. Inputs and outputs

Input:

* `path`: the directory path that should exist

Output:

* directory creation side effect at the requested path

## 4. Natural-language paraphrases

* create the directory `/tmp/example-folder`
* make sure `/tmp/work/cache` exists
* create a folder at a given path

## 5. One-sentence summary

Creating a directory by path is the reusable shell substrate behind many setup
tasks.
