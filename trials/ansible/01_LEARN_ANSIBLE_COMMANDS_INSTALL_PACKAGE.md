# Ansible Commands 01 — Ensure Package Installed

This document teaches the bounded Ansible capability of ensuring a package is
present on the target system.

## 1. Core capability

When a user wants a package installed declaratively, the reusable capability is
package installation by package name.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Ensure package is installed
      package:
        name: "{{ package_name }}"
        state: present
```

The named playbook parameter is `package_name`.

## 3. Inputs and outputs

Input:

* `package_name`: the package that should be present

Output:

* installed package state on the local target

## 4. Natural-language paraphrases

* ensure the package `git` is installed
* install `curl` through Ansible
* make sure a package is present on the host

## 5. One-sentence summary

Ensuring a package is installed by name is a reusable Ansible provisioning
capability.
