# Ansible Commands 12 — Render Template To File

This document teaches the bounded Ansible capability of rendering templated
content into a file.

## 1. Core capability

When a user wants parameterized configuration text written to a file, the
reusable capability is template rendering by destination and template variables.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Render template content
      copy:
        dest: "{{ path }}"
        content: "port={{ port }}\n"
```

The named playbook parameters are `path` and `port`.

## 3. Inputs and outputs

Inputs:

* `path`: the file that should receive the rendered content
* `port`: the port value inserted into the configuration text

Output:

* file at the target path containing rendered template content

## 4. Natural-language paraphrases

* render `/tmp/app.conf` from the template text `port={{ port }}` with `port=8080`
* write templated port configuration into a file
* render a tiny config file with Ansible

## 5. One-sentence summary

Rendering templated content into a file is a reusable Ansible configuration
capability.
