# Probability And Information Relation Validation Trial

The cumulative validator in [PROBABILITY_INFORMATION_RELATION_VALIDATION.py](PROBABILITY_INFORMATION_RELATION_VALIDATION.py) was run against the ten documents in order on one fresh SQLite database.

Checks run:
- `python3 -m py_compile PROBABILITY_INFORMATION_RELATION_VALIDATION.py`
- `python3 -m unittest tests.test_markdown_artifact_generation tests.test_markdown_ir tests.test_title_depth`
    - `Ran 20 tests in 14.516s`
    - `OK`
- `python3 PROBABILITY_INFORMATION_RELATION_VALIDATION.py`

Artifacts from the run:
- validator: [PROBABILITY_INFORMATION_RELATION_VALIDATION.py](PROBABILITY_INFORMATION_RELATION_VALIDATION.py)
- report: [report.json](reports/probability_information_relation_validation_20260326_223324/report.json)
- DB: [probability_information_relation_validation.sqlite3](reports/probability_information_relation_validation_20260326_223324/probability_information_relation_validation.sqlite3)

Result:
- overall status: `failed`

What the validation proved:
- `01` is good: same-document substrate relation formed correctly.
- `02` to `04` still form local same-document structure, but they do not carry the expected cross-document reuse links back to earlier families.
- `05` to `10` are the real break: the later substrate families are often not retained as stable semantic titles at all. They collapse into symbolic/expression-shaped titles such as `U From Frac...`, `D From Sum...`, `I From Sum...`, `R From Sum...`, and the cross-document relation edges are missing.

Concrete failure pattern:
- [01_LEARN_PROBABILITY_RELATIONS_FOUNDATIONS.md](01_LEARN_PROBABILITY_RELATIONS_FOUNDATIONS.md): passed
- [02_LEARN_PROBABILITY_RELATIONS_RATIO.md](02_LEARN_PROBABILITY_RELATIONS_RATIO.md): missing relation to additive combination
- [03_LEARN_PROBABILITY_RELATIONS_COMPLEMENT.md](03_LEARN_PROBABILITY_RELATIONS_COMPLEMENT.md): missing relation to ratio formation
- [04_LEARN_PROBABILITY_RELATIONS_CONDITIONAL.md](04_LEARN_PROBABILITY_RELATIONS_CONDITIONAL.md): missing relation to ratio formation
- [05_LEARN_PROBABILITY_RELATIONS_BAYES.md](05_LEARN_PROBABILITY_RELATIONS_BAYES.md): substrate family not preserved as `inverse conditional update`; prior relations missing
- [06_LEARN_PROBABILITY_RELATIONS_EXPECTATION.md](06_LEARN_PROBABILITY_RELATIONS_EXPECTATION.md): substrate family not preserved as `weighted aggregation`
- [07_LEARN_PROBABILITY_RELATIONS_VARIANCE.md](07_LEARN_PROBABILITY_RELATIONS_VARIANCE.md): substrate family not preserved; missing expectation relation
- [08_LEARN_PROBABILITY_RELATIONS_COVARIANCE.md](08_LEARN_PROBABILITY_RELATIONS_COVARIANCE.md): substrate family not preserved; missing expectation relation
- [09_LEARN_INFORMATION_RELATIONS_ENTROPY.md](09_LEARN_INFORMATION_RELATIONS_ENTROPY.md): substrate family not preserved; missing weighted-aggregation-family relation
- [10_LEARN_INFORMATION_RELATIONS_KL_DIVERGENCE.md](10_LEARN_INFORMATION_RELATIONS_KL_DIVERGENCE.md): substrate family not preserved; missing ratio and weighted-aggregation-family relations

The current system remains effective at same-document local decomposition, but it does not yet form the deeper semantic relation graph reliably across the probability/information ladder. The immediate weakness is title formation for substrate families and cross-document dependency emission.
