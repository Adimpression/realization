# Statistical Python Script-Writing Expertise Trial Conclusion

## Foundation phase

`supplement.py` became the canonical home for the LLM supplement layer, accompanied by the following changes:

- `LLMSupplement`, `ask_llm`, and related helpers moved into [supplement.py](supplement.py).
- The curriculum in [GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE.md](GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE.md) was extended to teach `z-score`, required inputs, the formula, and a function-bearing step explicitly.
- The SQLite persistence path in [store.py](store.py) was corrected so hybrid search links do not fail with `FOREIGN KEY constraint failed` when a `related_artifact_id` has not yet been persisted.
- Regression coverage was added in [tests/test_artifact_search_hybrid.py](tests/test_artifact_search_hybrid.py).

The full test suite was run with `python3 -m unittest discover -s tests` and reported `Ran 44 tests in 299.745s`, `OK`.

Fresh statistical validation first taught only `What is statistics?`, then probed `What is Python scripting?` with `--llm off`. The probe remained `incomplete` rather than returning the statistics definition, demonstrating that the previous cross-topic collapse no longer occurred.

The same fresh database produced these results:

- `What is statistics?` completed with the statistics answer in [1.json](reports/statistical_minicheck_after_fk_fix_20260325_210718/1.json).
- `What is Python scripting?` completed with a distinct Python scripting answer in [2.json](reports/statistical_minicheck_after_fk_fix_20260325_210718/2.json).
- `Python script?` completed from prior learning with `--llm off` in [3_probe_python_script.json](reports/statistical_minicheck_after_fk_fix_20260325_210718/3_probe_python_script.json).

This phase verified the supplement split, the persistence correction, the statistical concept-isolation correction, and off-LLM reuse for `Python script?` on a fresh database. It did not certify the complete executable bundle: the expanded curriculum had not yet been rerun, and the live z-score ability remained LLM-bound while collecting z-score-specific artifacts.

## Bundle certification phase

The subsequent certification phase completed the reusable statistical bundle path. Runtime changes in [main.py](main.py), with regression coverage in [tests/test_function_boundary.py](tests/test_function_boundary.py), accomplished the following:

- Generated Python ability wrappers were repaired so callable snippets become valid executable scripts.
- Compute/template reuse was changed to prefer invokable function artifacts over structured-learning records.
- Explicit `lookup_keys` were included in structured matching.
- Boundary-shape rejection was relaxed where it had incorrectly blocked internal compute abilities with `c*`.

Certification used these artifacts:

- Bundle: [GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE.yaml](reports/statistical_bundle_from_learned_db_20260325_225632/GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE.yaml)
- Fresh imported database: [import_fixed.sqlite3](reports/statistical_bundle_from_learned_db_20260325_225632/import_fixed.sqlite3)
- Certification summary: [summary_final_cert.json](reports/statistical_bundle_from_learned_db_20260325_225632/summary_final_cert.json)

The learned source database and fresh imported database produced the following results with `--llm off`:

- `Python script?` completed.
- `Write a Python script that computes the z-score for x=12, mean=10, std=2.` returned `1`.
- `If x=14, mean=11, and std=1.5, what z-score would your script produce?` returned `2`.

The imported bundle can be exercised with:

```bash
export STATE_SQLITE_PATH=reports/statistical_bundle_from_learned_db_20260325_225632/import_fixed.sqlite3

uv run realized-compatibility run --prompt 'Python script?' --llm off --max-steps 24
uv run realized-compatibility run --prompt 'Write a Python script that computes the z-score for x=12, mean=10, std=2.' --llm off --max-steps 24
uv run realized-compatibility run --prompt 'If x=14, mean=11, and std=1.5, what z-score would your script produce?' --llm off --max-steps 24
```

The bundle can be loaded into another database with:

```bash
export STATE_SQLITE_PATH=/path/to/new.sqlite3
uv run realized-compatibility artifact-import \
  --artifact-file reports/statistical_bundle_from_learned_db_20260325_225632/GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE.yaml \
  --normalized-out-dir reports/statistical_bundle_from_learned_db_20260325_225632/normalized_dir
```

The focused regression suite, including the new function-boundary cases, passed. A full `python3 -m unittest discover -s tests` run was started but did not complete because the repository's long LLM/network-bound section continued after the fast suites passed.

The certification did not include a cold, line-by-line execution of the complete expanded curriculum against a brand-new database. Those runs were operationally too slow to serve as the certification path. Instead, the exported bundle was imported and fully verified against a fresh database, establishing the supported future-loading path.
