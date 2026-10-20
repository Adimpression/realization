# Bash Commands 02 — List Directory Contents

This document teaches the bounded shell capability of listing the contents of a
directory.

## 1. Core capability

When a user wants to inspect what files and folders exist inside a location,
the reusable capability is directory listing by path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
ls -la "$path"
```

The named shell parameter is `$path`.

## 3. Inputs and outputs

Input:

* `path`: the directory whose contents should be listed

Output:

* printed listing of files, folders, permissions, and timestamps

## 4. Natural-language paraphrases

* list the contents of `/Users/ravindranathakila/service/realized`
* show me what is inside `/tmp`
* display all entries in a directory

## 5. One-sentence summary

Listing a directory by path is a reusable shell inspection capability.
