# Ansible Commands 11 — Ensure User Exists

This document teaches the bounded Ansible capability of ensuring a local user
account exists.

## 1. Core capability

When a user wants a local account present declaratively, the reusable capability
is user creation by account name.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Ensure user exists
      user:
        name: "{{ username }}"
        state: present
```

The named playbook parameter is `username`.

## 3. Inputs and outputs

Input:

* `username`: the local account that should exist

Output:

* user present on the target system

## 4. Natural-language paraphrases

* ensure the user `demo-ansible` exists
* create a local account through Ansible
* make sure a user account is present

## 5. One-sentence summary

Ensuring a user exists by account name is a reusable Ansible account-management
capability.
