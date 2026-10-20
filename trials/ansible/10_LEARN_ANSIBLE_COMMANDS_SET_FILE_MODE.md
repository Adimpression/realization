# Ansible Commands 10 — Ensure File Mode

This document teaches the bounded Ansible capability of enforcing a file mode.

## 1. Core capability

When a user wants file permissions set declaratively, the reusable capability is
mode enforcement by path and mode.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Ensure file mode
      file:
        path: "{{ path }}"
        mode: "{{ mode }}"
        state: file
```

The named playbook parameters are `path` and `mode`.

## 3. Inputs and outputs

Inputs:

* `path`: the file whose permissions should be set
* `mode`: the mode such as `0644`

Output:

* file at the requested mode

## 4. Natural-language paraphrases

* ensure the file `/tmp/ansible.env` has mode `0644`
* set a file mode through Ansible
* manage file permissions declaratively

## 5. One-sentence summary

Enforcing a file mode by path and mode is a reusable Ansible permission
capability.
