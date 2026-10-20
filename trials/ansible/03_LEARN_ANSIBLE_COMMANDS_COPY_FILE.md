# Ansible Commands 03 — Copy File To Destination

This document teaches the bounded Ansible capability of copying a file to a
destination path.

## 1. Core capability

When a user wants one file deployed to another path, the reusable capability is
file copy by source and destination.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Copy file to destination
      copy:
        src: "{{ source }}"
        dest: "{{ destination }}"
        remote_src: true
```

The named playbook parameters are `source` and `destination`.

## 3. Inputs and outputs

Inputs:

* `source`: the existing file path
* `destination`: the new file path

Output:

* copied file at the destination

## 4. Natural-language paraphrases

* copy `/etc/hosts` to `/tmp/ansible-hosts.copy`
* deploy one local file into another location
* copy a file with Ansible

## 5. One-sentence summary

Copying a file by source and destination is a reusable Ansible transfer
capability.
