# Python SDK User Capability Trials

This folder defines a gated Python-learning curriculum for common SDK usage
capabilities.

The goal is to teach reusable Python SDK abilities that can be learned directly
from fenced Python functions when `--supported-executor python3` is enabled.

This curriculum follows these conventions:

* each lesson teaches one bounded SDK capability
* the executable surface is always a fenced `python` block
* the function is always named `main`
* imports are placed inside `main`
* dependency metadata is kept inline in the signature as
  `__dependencies__: tuple[str, ...] = (...)`
* external SDK dependencies are explicit in the signature
* headings, paraphrases, and summaries are written to support later natural
  retrieval

Canonical teaching shape:

* section 1: core capability
* section 2: executable Python relation
* section 3: inputs and outputs
* section 4: natural-language paraphrases
* section 5: one-sentence summary

The emphasis is on bounded SDK tasks, not on full application architectures.
