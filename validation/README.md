# Realized Validation

`realized-validation` contains repository validation infrastructure shared by
multiple trial entry programs:

- layered acceptance orchestration and structured reports;
- disposable or RAM-backed SQLite paths; and
- durable SQLite report archival.

It is development tooling, not a production runtime dependency. Domain
validators, trial semantics, curricula, and corpora remain standalone entry
programs outside this package. The package locates a source checkout by default;
`REALIZED_VALIDATION_REPOSITORY_ROOT` can select one explicitly.

Historical imports through `validation_ladder` and `validation_sqlite` remain
exact compatibility aliases during the qualification period. New validation
code should import `realized_validation`.
