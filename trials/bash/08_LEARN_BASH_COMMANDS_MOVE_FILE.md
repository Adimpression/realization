# Bash Commands 08 — Move File

This document teaches the bounded shell capability of moving or renaming a file
from one path to another.

## 1. Core capability

When a user wants to relocate or rename a file, the reusable capability is file
move by source and destination.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
mkdir -p "$(dirname "$destination")"
mv "$source" "$destination"
```

The named shell parameters are `$source` and `$destination`.

## 3. Inputs and outputs

Inputs:

* `source`: the existing file path
* `destination`: the new file path

Output:

* the file moved or renamed into the destination path

## 4. Natural-language paraphrases

* move `/tmp/hosts.copy` to `/tmp/hosts.moved`
* rename `/tmp/report.txt` to `/tmp/report.old.txt`
* move a file to a new path

## 5. One-sentence summary

Moving a file by source and destination is a reusable shell relocation
capability.
