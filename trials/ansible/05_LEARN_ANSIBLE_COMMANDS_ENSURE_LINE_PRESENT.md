# Ansible Commands 05 — Ensure Line Present In File

This document teaches the bounded Ansible capability of ensuring one line is
present in a file.

## 1. Core capability

When a user wants a configuration line guaranteed to exist without duplicating
it repeatedly, the reusable capability is line insertion by path and line.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Ensure line is present
      lineinfile:
        path: "{{ path }}"
        line: "{{ line }}"
        create: true
```

The named playbook parameters are `path` and `line`.

## 3. Inputs and outputs

Inputs:

* `path`: the file to edit
* `line`: the line that should be present

Output:

* file with the requested line present

## 4. Natural-language paraphrases

* ensure the line `export DEMO=1` is present in `/tmp/ansible.env`
* add one configuration line to a file if missing
* manage a single line in a file with Ansible

## 5. One-sentence summary

Ensuring a line is present by path and line is a reusable Ansible text-editing
capability.
