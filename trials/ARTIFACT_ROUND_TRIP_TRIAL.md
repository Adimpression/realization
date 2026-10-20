# Artifact Round-Trip Trial

Import/export is split into [side.py](side.py), multi-document `---` YAML import works, and the full unit suite passed: `python3 -m unittest discover -s tests` -> `Ran 39 tests in 376.784s`, `OK`.

Fresh-database builds exported one `---`-separated YAML bundle per source under [curriculum_bundle_build_20260325_190119](reports/curriculum_bundle_build_20260325_190119). The manifest is [manifest.json](reports/curriculum_bundle_build_20260325_190119/manifest.json).

Bundles:
- [LEARN_NEWTOWNS_LAWS.yaml](reports/curriculum_bundle_build_20260325_190119/bundles/LEARN_NEWTOWNS_LAWS.yaml)
- [LEARN_MOMENTUM.yaml](reports/curriculum_bundle_build_20260325_190119/bundles/LEARN_MOMENTUM.yaml)
- [GAIN_PYTHOGOREAN_THEORM.yaml](reports/curriculum_bundle_build_20260325_190119/bundles/GAIN_PYTHOGOREAN_THEORM.yaml)
- [LEARN_TABLET_SAFETY.yaml](reports/curriculum_bundle_build_20260325_190119/bundles/LEARN_TABLET_SAFETY.yaml)
- [GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE.yaml](reports/curriculum_bundle_build_20260325_190119/bundles/GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE.yaml)

Per-bundle import smoke is in [per_bundle_report.json](reports/curriculum_bundle_build_20260325_190119/import_smoke/per_bundle_report.json). Results:
- Newton bundle imports and answers `12`
- Momentum bundle imports and answers `96`
- Pythagorean bundle imports and answers `7.0710678118654755`
- Tablet-safety bundle imports and gives the expected “do not take / identify first” guidance
- Statistical-Python bundle imports, but `Python script?` is still `incomplete`

Four bundles are valid reload targets. The statistical bundle was exported, but it is not yet a trustworthy future-load bundle; its run report is [report.json](reports/curriculum_bundle_build_20260325_190119/runs/GAIN_STATISTICAL_PYTHON_SCRIPT_WRITING_EXPERTISE/report.json). The combined-import note is also in the manifest: importing all unrelated bundles into one DB can create ambiguity on overly generic prompts, so future tests should use per-bundle imports until domain gating is available.

Load commands:
```bash
python3 main.py artifact-import --artifact-file reports/curriculum_bundle_build_20260325_190119/bundles/LEARN_NEWTOWNS_LAWS.yaml
python3 main.py artifact-import --artifact-file reports/curriculum_bundle_build_20260325_190119/bundles/GAIN_PYTHOGOREAN_THEORM.yaml
python3 main.py artifact-import --artifact-file reports/curriculum_bundle_build_20260325_190119/bundles/LEARN_TABLET_SAFETY.yaml
```

Follow-up work should repair statistical curriculum retrieval and generation so its exported bundle is as reliable as the other four.
