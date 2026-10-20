# Ansible Commands 04 — Write File Content

This document teaches the bounded Ansible capability of writing exact text into a
file.

## 1. Core capability

When a user wants a file created or replaced with specific content, the reusable
capability is content deployment by path and text.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Write file content
      copy:
        dest: "{{ path }}"
        content: "{{ content }}"
```

The named playbook parameters are `path` and `content`.

## 3. Inputs and outputs

Inputs:

* `path`: the file to create or replace
* `content`: the exact text that should be written

Output:

* file at the target path containing the requested text

## 4. Natural-language paraphrases

* write the text `ready=true` to `/tmp/ansible.env`
* create `/tmp/app.conf` with specific content
* write exact file content with Ansible

## 5. One-sentence summary

Writing file content by path and text is a reusable Ansible deployment
capability.
