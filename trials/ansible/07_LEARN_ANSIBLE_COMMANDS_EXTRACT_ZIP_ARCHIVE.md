# Ansible Commands 07 — Extract Archive

This document teaches the bounded Ansible capability of unpacking an archive
into a destination directory.

## 1. Core capability

When a user wants an archive unpacked declaratively, the reusable capability is
archive extraction by source and destination.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Extract archive
      unarchive:
        src: "{{ archive }}"
        dest: "{{ destination }}"
        remote_src: true
```

The named playbook parameters are `archive` and `destination`.

## 3. Inputs and outputs

Inputs:

* `archive`: the archive file to unpack
* `destination`: the directory where contents should land

Output:

* extracted files in the destination

## 4. Natural-language paraphrases

* extract `/tmp/example.zip` into `/tmp/example-ansible-unpacked`
* unarchive one file into a directory
* unpack an archive with Ansible

## 5. One-sentence summary

Extracting an archive by source and destination is a reusable Ansible unpacking
capability.
