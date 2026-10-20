# Ansible Commands 02 — Ensure Directory Exists

This document teaches the bounded Ansible capability of creating a directory
with a desired mode.

## 1. Core capability

When a user wants a directory declaratively present with specific permissions,
the reusable capability is directory creation by path and mode.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Ensure directory exists
      file:
        path: "{{ path }}"
        state: directory
        mode: "{{ mode }}"
```

The named playbook parameters are `path` and `mode`.

## 3. Inputs and outputs

Inputs:

* `path`: the directory that should exist
* `mode`: the directory mode such as `0755`

Output:

* directory present with the requested permissions

## 4. Natural-language paraphrases

* create the directory `/tmp/ansible-demo` with mode `0755`
* ensure `/tmp/cache` exists and is mode `0700`
* make a directory through Ansible

## 5. One-sentence summary

Ensuring a directory exists by path and mode is a reusable Ansible filesystem
capability.
