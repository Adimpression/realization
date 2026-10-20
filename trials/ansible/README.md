# Ansible Capability Trials

This folder defines a gated Ansible-learning curriculum for common local
automation capabilities.

The goal is to teach reusable Ansible playbook abilities that can be learned
directly from fenced playbooks when `--supported-executor ansible` is enabled.

This curriculum follows these conventions:

* each lesson teaches one bounded Ansible capability
* the executable surface is always a fenced `ansible` block
* the playbook always targets `localhost`
* reusable inputs are expressed as Jinja variables such as `{{ package_name }}`,
  `{{ path }}`, `{{ service_name }}`, and `{{ destination }}`
* headings, paraphrases, and summaries are written to support later natural
  retrieval
* the playbook fence is the primary executable relation

Canonical teaching shape:

* section 1: core capability
* section 2: executable Ansible relation
* section 3: inputs and outputs
* section 4: natural-language paraphrases
* section 5: one-sentence summary

The emphasis is on bounded infrastructure and system tasks, not on large
multi-role playbook projects.
