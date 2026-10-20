# Bash Command Capability Trials

This folder defines a gated bash-learning curriculum for common shell
capabilities.

The goal is to teach reusable command-oriented abilities that can be learned
directly from fenced bash blocks when `--supported-executor bash` is enabled.

This curriculum follows these conventions:

* each lesson teaches one bounded shell capability
* the executable surface is always a fenced `bash` block
* reusable inputs are exposed as shell variables such as `$path`, `$url`,
  `$pattern`, `$archive`, and `$destination`
* commands are practical POSIX or macOS-friendly shell commands
* headings, paraphrases, and summaries are written to help later natural
  retrieval
* the fenced command is the primary executable relation, not just an example

Canonical teaching shape:

* section 1: core capability
* section 2: executable bash relation
* section 3: inputs and outputs
* section 4: natural-language paraphrases
* section 5: one-sentence summary

The emphasis is on bounded shell execution, not on large shell programs.
