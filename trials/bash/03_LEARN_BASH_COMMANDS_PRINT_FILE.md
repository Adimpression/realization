# Bash Commands 03 — Print File Contents

This document teaches the bounded shell capability of printing the contents of a
text file.

## 1. Core capability

When a user wants to inspect a file directly in the terminal, the reusable
capability is file printing by path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
cat "$path"
```

The named shell parameter is `$path`.

## 3. Inputs and outputs

Input:

* `path`: the file path to print

Output:

* the file text emitted to standard output

## 4. Natural-language paraphrases

* print `/etc/hosts`
* show the contents of `/tmp/example.txt`
* display a text file in the shell

## 5. One-sentence summary

Printing a file by path is the reusable shell substrate for direct text
inspection.
