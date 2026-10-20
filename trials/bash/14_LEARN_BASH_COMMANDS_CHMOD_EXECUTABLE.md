# Bash Commands 14 — Change File Mode

This document teaches the bounded shell capability of changing file permissions
using a mode value and a path.

## 1. Core capability

When a user wants to make a file executable or otherwise adjust permissions, the
reusable capability is chmod by mode and path.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
chmod "$mode" "$path"
```

The named shell parameters are `$mode` and `$path`.

## 3. Inputs and outputs

Inputs:

* `mode`: the permission mode such as `755` or `644`
* `path`: the file whose mode should be changed

Output:

* permission change side effect on the target path

## 4. Natural-language paraphrases

* make `/tmp/demo.sh` executable with mode `755`
* change `/tmp/report.txt` to mode `644`
* chmod a file using a numeric mode

## 5. One-sentence summary

Changing file mode by mode and path is a reusable shell permission-management
capability.
