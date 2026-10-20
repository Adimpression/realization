# Bash Commands 07 — Copy File

This document teaches the bounded shell capability of copying a file from one
path to another.

## 1. Core capability

When a user wants to duplicate a file at a new location, the reusable
capability is file copy by source and destination.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
mkdir -p "$(dirname "$destination")"
cp "$source" "$destination"
```

The named shell parameters are `$source` and `$destination`.

## 3. Inputs and outputs

Inputs:

* `source`: the existing file to copy
* `destination`: the output file path

Output:

* copied file at the destination path

## 4. Natural-language paraphrases

* copy `/etc/hosts` to `/tmp/hosts.copy`
* duplicate `/tmp/input.txt` into `/tmp/archive/input.txt`
* copy a file to a different path

## 5. One-sentence summary

Copying a file by source and destination is a reusable shell transfer
capability.
