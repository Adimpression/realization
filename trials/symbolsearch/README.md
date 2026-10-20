# Symbol Search Capability Trials

This folder defines a gated shell-learning curriculum for code and text symbol
search tasks.

The goal is to teach reusable search abilities that can be learned directly from
fenced `bash` blocks when `--supported-executor bash` is enabled.

This curriculum follows these conventions:

* each lesson teaches one bounded symbol-search capability
* the executable surface is always a fenced `bash` block
* reusable inputs are exposed as shell variables such as `$root`, `$symbol`,
  `$pattern`, `$glob`, and `$module`
* the lessons prefer `rg` because it matches the project’s normal search style
* headings, paraphrases, and summaries are written to support later natural
  retrieval
* the fenced command is the primary executable relation

Canonical teaching shape:

* section 1: core capability
* section 2: executable bash relation
* section 3: inputs and outputs
* section 4: natural-language paraphrases
* section 5: one-sentence summary

The emphasis is on fast codebase lookup, not on full indexing systems.
