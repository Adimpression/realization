# Coordinated Transformation

Dependency-free Python implementation of the snapshot-local Coordinated
Transformation in Federated Systems (CTFS) formal model.

The governing theory is documented in
[COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md](COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md).
Its subject-workflow integration constraints are documented in
[COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY_IMLEMENTATION.md](COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY_IMLEMENTATION.md).

The package evaluates explicit model snapshots. It does not discover facts,
revise snapshots, call an LLM, perform host effects, or persist workflow state.
