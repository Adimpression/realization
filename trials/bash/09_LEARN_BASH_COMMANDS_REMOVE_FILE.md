# Bash Commands 09 — Remove File

This document teaches the bounded shell capability of removing a file by path.

## 1. Core capability

When a user wants to delete a specific file, the reusable capability is file
removal by path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rm -f "$path"
```

The named shell parameter is `$path`.

## 3. Inputs and outputs

Input:

* `path`: the file path to remove

Output:

* removal side effect at the requested file path

## 4. Natural-language paraphrases

* remove `/tmp/hosts.moved`
* delete `/tmp/old.log`
* remove a file by path

## 5. One-sentence summary

Removing a file by path is a reusable shell cleanup capability.
