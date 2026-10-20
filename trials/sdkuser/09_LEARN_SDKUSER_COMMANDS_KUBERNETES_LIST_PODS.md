# SDK User Commands 09 — Kubernetes List Pods

This document teaches the bounded Python capability of listing pods in one
namespace through the Kubernetes SDK.

## 1. Core capability

When a user wants the pods currently present in a namespace, the reusable
capability is Kubernetes pod listing by namespace.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    namespace: str,
    *,
    __dependencies__: tuple[str, ...] = ("kubernetes",),
) -> dict[str, object]:
    from kubernetes import client, config

    config.load_kube_config()
    api = client.CoreV1Api()
    pods = api.list_namespaced_pod(namespace=namespace)
    names = [item.metadata.name for item in pods.items]
    return {"status": "ok", "namespace": namespace, "pods": names}
```

## 3. Inputs and outputs

Input:

* `namespace`: the Kubernetes namespace

Output:

* status, namespace, and pod names

## 4. Natural-language paraphrases

* list pods in the Kubernetes namespace `default`
* inspect pods through the Kubernetes Python SDK
* enumerate pod names in one namespace

## 5. One-sentence summary

Listing pods by namespace through the Kubernetes SDK is a reusable Python SDK
cluster-inspection capability.
