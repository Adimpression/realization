# DST

`dst` is Realization's Decision Support Tool package. It preserves the logical
bridge from governed candidate-path discovery, through typed case
normalization, to coordinated-transformation evaluation and revision-aware
decision support.

The governing theory is documented in [DST.md](DST.md). Implementation and
compatibility constraints are documented in
[DST_IMPLEMENTATION.md](DST_IMPLEMENTATION.md).

The import surface remains `dst`. The package includes its checked-in source
cases, typed fixtures, discovery fixtures, normalized fixtures, and prompt
contract so an installed distribution retains the same deterministic
substrate as the source checkout.

The distribution is independently buildable and importable. Its semantic-text,
title, proposal, itemization, decision-review, and transformation-construct
values are package-native, and no DST module imports a repository-root
implementation module.

Live proposal orchestration is explicit dependency inversion rather than a
hidden runtime lookup. Callers provide a `DstControllerBootstrap` to the live
pipeline or construct-discovery entry point. A missing realization fails closed
with `DstControllerBootstrapUnavailable`; the package never selects or imports
an application controller on its own. In the workstation, subject workflow
passes this operation through its host-actions contract, the runtime adapter
uses the registered controller-runtime provider, and the executable composition
root binds that provider to the concrete application controller.
