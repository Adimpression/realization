# Bash Commands 13 — Compute Sha256 Checksum

This document teaches the bounded shell capability of computing the sha256
checksum of a file.

## 1. Core capability

When a user wants to verify or compare file content by digest, the reusable
capability is sha256 computation by file path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
shasum -a 256 "$path"
```

The named shell parameter is `$path`.

## 3. Inputs and outputs

Input:

* `path`: the file whose checksum should be computed

Output:

* sha256 digest line emitted to standard output

## 4. Natural-language paraphrases

* compute the sha256 checksum of `/etc/hosts`
* hash `/tmp/archive.zip` with sha256
* get the sha256 digest of a file

## 5. One-sentence summary

Computing a sha256 checksum by file path is a reusable shell verification
capability.
