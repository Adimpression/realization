# Workstation Contracts

This distribution owns transport-neutral workstation API/ABI objects. It contains
only dataclasses, protocols, and deterministic routing helpers; it must not import
runtime, UI, service, adapter, or provider implementations.

Legacy modules re-export these objects during the strangler migration. Their
historical module names are retained on moved dataclasses and protocols so repr,
pickle lookup, and callers importing the old paths remain compatible.

The current host-interaction descriptor and attachment-scope contract lives in
the sibling `realized-host-interaction` substrate. It is not a general
host-operation provider registry. Re-exporting it from this package would
invert the six-layer dependency boundary by making the shared substrate import
a workstation package.
