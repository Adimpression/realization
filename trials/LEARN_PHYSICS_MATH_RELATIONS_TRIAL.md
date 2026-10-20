# Physics Math Relations Trial

The implementation changes are in [main.py](main.py). Markdown title repair is stronger for both knowledge and ability artifacts: if a heading/current identity is organizational or meta, the repair pass rebuilds identity from encounter semantics instead of preserving the section label. Explicit `related_titles` handling and post-learn relation resolution let later learned artifacts point back to earlier substrate artifacts using persisted canonical IDs rather than stale in-memory IDs.

The trial uses the curriculum [LEARN_PHYSICS_MATH_RELATIONS.md](LEARN_PHYSICS_MATH_RELATIONS.md), the live validator [SEMANTIC_RELATION_VALIDATION.py](SEMANTIC_RELATION_VALIDATION.py), and focused regression coverage in [tests/test_markdown_artifact_generation.py](tests/test_markdown_artifact_generation.py).

Validation:
- `python3 -m unittest tests.test_markdown_artifact_generation tests.test_markdown_ir tests.test_title_depth`
- result: `Ran 20 tests`, `OK`

Live OpenAI validation:
- report: [report.json](reports/semantic_relation_validation_20260326_220139/report.json)
- status: `ok`

What that run proved:
- the substrate title is no longer `1 Reusable Substrate`; it became `Physics Math Relations / P From X And Y`
- later laws reuse it semantically:
    - force artifact relates to the substrate artifact
    - momentum artifact relates to the substrate artifact
- off-LLM prompt reuse works on the learned DB:
    - `Calculate P from x=2 and y=6.` -> `12`
    - `Calculate F from m=3 and a=4.` -> `12`
    - `Calculate p from m=5 and v=7.` -> `35`

The document exercises both title formation and semantic relation formation, not just decomposition. One residual gap remains: some meta knowledge sections such as `One Sentence Summary` still survive as generic knowledge identities. The executable/substrate relation path works; summary-section identity cleanup remains a separate refinement.
