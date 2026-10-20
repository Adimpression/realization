# Bash Commands 10 — Create Tar Gz Archive

This document teaches the bounded shell capability of archiving a directory
into a compressed tarball.

## 1. Core capability

When a user wants to package a directory into one compressed file, the reusable
capability is tar.gz archive creation by source directory and archive path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
mkdir -p "$(dirname "$archive")"
tar -czf "$archive" -C "$source_dir" .
```

The named shell parameters are `$archive` and `$source_dir`.

## 3. Inputs and outputs

Inputs:

* `source_dir`: the directory to archive
* `archive`: the output tar.gz path

Output:

* compressed archive file at the destination path

## 4. Natural-language paraphrases

* create `/tmp/realized-tests.tar.gz` from `tests`
* archive `/tmp/project` into `/tmp/project.tar.gz`
* make a tar.gz archive from a directory

## 5. One-sentence summary

Creating a tar.gz archive from a directory is a reusable shell packaging
capability.
