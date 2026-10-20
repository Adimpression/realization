# Ansible Commands 09 — Clone Git Repository

This document teaches the bounded Ansible capability of cloning a Git repository
into a destination directory.

## 1. Core capability

When a user wants a repository checked out declaratively, the reusable
capability is git clone by repository URL and destination path.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Clone Git repository
      git:
        repo: "{{ repo_url }}"
        dest: "{{ destination }}"
```

The named playbook parameters are `repo_url` and `destination`.

## 3. Inputs and outputs

Inputs:

* `repo_url`: the repository URL to clone
* `destination`: the local checkout directory

Output:

* repository checkout at the destination

## 4. Natural-language paraphrases

* clone `https://github.com/octocat/Hello-World.git` into `/tmp/hello-world`
* check out a git repository with Ansible
* clone a repository to a local path

## 5. One-sentence summary

Cloning a Git repository by URL and destination is a reusable Ansible source
deployment capability.
