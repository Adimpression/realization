# Symbol Search Commands 08 — Find Environment Variable Names

This document teaches the bounded shell capability of finding environment
variable names or references matching a pattern.

## 1. Core capability

When a user wants environment variable references collected, the reusable
capability is environment-name search by root and pattern.

## 2. Executable Bash relation

This capability should be learned as a reusable bash ability artifact.

```bash
rg -n "$pattern" "$root"
```

The named shell parameters are `$pattern` and `$root`.

## 3. Inputs and outputs

Inputs:

* `pattern`: the environment variable text to match, such as `OPENAI`
* `root`: the directory tree to search

Output:

* matching lines that mention the environment variable pattern

## 4. Natural-language paraphrases

* find environment variable names containing `OPENAI` under `/Users/ravindranathakila/service/realized`
* search a codebase for one env-var pattern
* locate environment variable references by text

## 5. One-sentence summary

Finding environment variable references by pattern and root is a reusable
configuration-search capability.
