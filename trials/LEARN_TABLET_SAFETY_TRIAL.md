# Tablet Safety Learning Trial

The generic fixes were implemented in [main.py](main.py), with regression coverage in [tests/test_markdown_artifact_generation.py](tests/test_markdown_artifact_generation.py) and [tests/test_artifact_boundary_shape.py](tests/test_artifact_boundary_shape.py).

What changed:
- richer `Not` extraction now carries better uncertainty, confirmation, and explicit-absence distinctions
- markdown-learned knowledge artifacts now use encounter-grounded question/answer construction instead of leaking `Canonical prompt forms` into answers
- structured-learning records no longer inherit bridge answers unless the run itself directly closed with that answer
- knowledge artifacts no longer get write/read boundary terms just because their answer text describes actions
- executable selection now prioritizes boundary/input compatibility ahead of superficial text overlap
- stored default invocation payloads are only used for compute-style prompts, not descriptive prompts like `What is ...?`
- answer reuse is blocked across compute-vs-descriptive posture mismatches
- ordinal/section discriminator mismatches like `second` vs `third` no longer count as the same encountered `Not`

Validation:
- `python3 -m unittest discover -s tests`
    - `Ran 30 tests in 243.234s`
    - `OK`
- [tablet_safety_validation report](reports/tablet_safety_validation_20260325_002234/report.json)
    - `status: ok`
- [boundary_shape_validation report](reports/boundary_shape_validation_20260325_002823/report.json)
    - `status: ok`
- [learned_function_validation report](reports/learned_function_validation_20260325_005730/report.json)
    - `status: ok`

Net result:
- the 10-case tablet/prompt suite now passes on a fresh DB
- boundary-shape artifact picking still works
- markdown knowledge reuse and learned function reuse both still work after the generic fixes
