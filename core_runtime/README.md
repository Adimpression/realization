# Realized Core Runtime

`realized-core-runtime` owns the dependency-inverted lifecycle that advances a
represented non-achievedness toward realization. It deliberately does not own
domain reduction rules, model providers, persistence, host interaction, or UI
behavior.

The embedding application supplies those capabilities through the protocols in
`realized_core_runtime.contracts`. The lifecycle invokes the supplied closure
and finalization operations, so existing persistence and reporting remain part
of the run without becoming dependencies of this package.

This separation keeps the package independently buildable and allows alternate
applications to provide their own semantic and infrastructure adapters without
changing the lifecycle algorithm.
