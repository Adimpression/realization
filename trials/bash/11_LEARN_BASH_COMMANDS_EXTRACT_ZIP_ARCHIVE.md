# Bash Commands 11 — Extract Zip Archive

This document teaches the bounded shell capability of extracting a zip archive
into a destination directory.

## 1. Core capability

When a user wants the contents of a zip file unpacked into a folder, the
reusable capability is archive extraction by archive path and destination.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
mkdir -p "$destination"
unzip -o "$archive" -d "$destination"
```

The named shell parameters are `$archive` and `$destination`.

## 3. Inputs and outputs

Inputs:

* `archive`: the zip file to extract
* `destination`: the directory where contents should be unpacked

Output:

* extracted files and folders in the destination directory

## 4. Natural-language paraphrases

* extract `/tmp/example.zip` into `/tmp/example-unpacked`
* unzip `/tmp/reports.zip` to `/tmp/reports`
* unpack a zip archive into a folder

## 5. One-sentence summary

Extracting a zip archive by archive path and destination is a reusable shell
unpacking capability.
