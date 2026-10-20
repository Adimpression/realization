# Ansible Commands 08 — Ensure Service Started And Enabled

This document teaches the bounded Ansible capability of managing a service state.

## 1. Core capability

When a user wants a service running and enabled at boot, the reusable capability
is service management by service name.

## 2. Executable Ansible relation

This capability should be learned as a reusable Ansible ability artifact.

```ansible
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Ensure service is started and enabled
      service:
        name: "{{ service_name }}"
        state: started
        enabled: true
```

The named playbook parameter is `service_name`.

## 3. Inputs and outputs

Input:

* `service_name`: the service to start and enable

Output:

* service running and enabled on the target

## 4. Natural-language paraphrases

* ensure the service `cron` is started and enabled
* start and enable a service through Ansible
* manage a service lifecycle declaratively

## 5. One-sentence summary

Ensuring a service is started and enabled by name is a reusable Ansible service
management capability.
