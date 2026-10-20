# Boundary Shape Validation Trial

The artifact-search refactor was implemented in [store.py](store.py#L1857). The new path keeps the existing normalized artifact tables, adds a hybrid retrieval layer, and preserves the old retrieval path as fallback so tuned behavior is not discarded.

What changed:
- Multi-view search projection for each artifact in [store.py](store.py#L1938)
    - separate topic, failure, and repair views
    - explicit applicability/exclusion text
    - reuse of the controller’s structured non-achievedness extraction
- New search-side schema in [store.py](store.py#L2826)
    - `bssc_artifact_search_units`
    - `bssc_artifact_search_fts`
    - `bssc_artifact_topic_vec`
    - `bssc_artifact_failure_vec`
    - `bssc_artifact_repair_vec`
    - `bssc_artifact_search_links`
- Hybrid candidate generation and score fusion in [store.py](store.py#L3541) and [store.py](store.py#L3702)
    - FTS5
    - multi-view vectors
    - metadata bonuses
    - exclusions penalties
    - legacy retrieval retained as a backstop
- New direct regression coverage in [tests/test_artifact_search_hybrid.py](tests/test_artifact_search_hybrid.py#L58)
- A corrupted line in [main.py](main.py#L4763) that blocked compilation was also repaired

Important implementation note:
- The installed backend here is `sqlite_vec`, not `sqlite_vector`.
- The implementation retains the installed backend and combines relational metadata, FTS5, multiple vector side tables, and application-side fusion. It does not force a backend swap.

Validation:
- Pre-refactor baseline on the green branch state: `36` tests OK, boundary-shape validation OK.
- Post-refactor:
    - `python3 -m unittest discover -s tests`
    - result: `Ran 38 tests in 293.981s`, `OK`
    - `python3 BOUNDARY_SHAPE_VALIDATION.py`
    - result: `status = ok`
    - report: [report.json](reports/boundary_shape_validation_20260325_094654/report.json)
    - `python3 LEARNED_FUNCTION_VALIDATION.py --domains newton_force momentum pythagorean_hypotenuse`
    - result: `status = ok`
    - report: [report.json](reports/learned_function_validation_20260325_094759/report.json)

The retrieval-critical learned-function cases still work on fresh learned stores:
- Newton force -> `12`
- Pythagorean hypotenuse -> `5`
- Momentum -> `96`

The refactor preserves the prior tuning, and the full post-change validation passed.
