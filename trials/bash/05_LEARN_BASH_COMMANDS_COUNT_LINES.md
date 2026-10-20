# Bash Commands 05 — Count Lines In File

This document teaches the bounded shell capability of counting how many lines a
file contains.

## 1. Core capability

When a user wants a quick size or record count proxy for a text file, the
reusable capability is line counting by file path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
wc -l < "$path"
```

The named shell parameter is `$path`.

## 3. Inputs and outputs

Input:

* `path`: the file whose lines should be counted

Output:

* one numeric line count

## 4. Natural-language paraphrases

* count the lines in `/etc/hosts`
* tell me how many lines are in `/tmp/data.txt`
* get the line count for a file

## 5. One-sentence summary

Counting lines in a file is a reusable shell measurement capability.
