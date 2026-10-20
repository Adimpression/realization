# Python Command Capability Trials

This folder defines a gated Python-learning curriculum for common command-style
capabilities.

The goal is to teach reusable Python abilities that can be learned directly from
fenced Python functions when `--supported-executor python3` is enabled.

This curriculum follows these conventions:

* each lesson teaches one bounded Python capability
* the executable surface is always a fenced `python` block
* the function is always named `main`
* imports are placed inside `main`
* dependency metadata is kept inline in the signature as
  `__dependencies__: tuple[str, ...] = ()`
* file-bearing skills should prefer governed broker surfaces such as
  `fs.read_mount`, `fs.write_mount`, `fs.list_mount`, `fs.find_mount`,
  `store.named_query`, `store.skill_state`, and `net.http_get_text` rather
  than raw paths, raw SQLite, or raw network access
* when a lesson uses filesystem data, the preferred inputs are a `mount` name
  plus a `relative_path`
* the code is intentionally simple and command-specific
* headings, paraphrases, and summaries are written to support later natural
  retrieval

Canonical teaching shape:

* section 1: core capability
* section 2: executable Python relation
* section 3: inputs and outputs
* section 4: natural-language paraphrases
* section 5: one-sentence summary

The emphasis is on reusable Python task abilities, not on large frameworks or
multi-file applications.
