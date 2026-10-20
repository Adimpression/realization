# Symbol Search Commands 11 — Find Yaml Keys

This document teaches the bounded shell capability of finding YAML key lines by
key name.

## 1. Core capability

When a user wants one configuration key located across YAML files, the reusable
capability is YAML-key search by root and key.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "^\\s*${key}:" "$root"
```

The named shell parameters are `$key` and `$root`.

## 3. Inputs and outputs

Inputs:

* `key`: the YAML key name to match
* `root`: the directory tree to search

Output:

* matching YAML key lines with file paths and line numbers

## 4. Natural-language paraphrases

* find YAML keys named `artifact_type` under `/Users/ravindranathakila/service/realized`
* search YAML files for one key
* locate one configuration key across a tree

## 5. One-sentence summary

Finding YAML key lines by key and root is a reusable configuration-search
capability.
