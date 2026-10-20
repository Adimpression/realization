# Ansible Commands 06 — Download Url To File

This document teaches the bounded Ansible capability of downloading a URL into a
local file.

## 1. Core capability

When a user wants remote content fetched and saved declaratively, the reusable
capability is URL download by source URL and destination path.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Download URL to file
      get_url:
        url: "{{ url }}"
        dest: "{{ destination }}"
```

The named playbook parameters are `url` and `destination`.

## 3. Inputs and outputs

Inputs:

* `url`: the remote resource to fetch
* `destination`: the local output file path

Output:

* downloaded file at the destination

## 4. Natural-language paraphrases

* download `https://example.com` to `/tmp/example-ansible.html`
* fetch a URL into a file with Ansible
* save remote content locally through a playbook

## 5. One-sentence summary

Downloading a URL into a file is a reusable Ansible fetch capability.
