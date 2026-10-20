# Cylinder Measures Learning Trial

The stronger enforcement is in [main.py](main.py) and the focused regression is in [tests/test_markdown_artifact_generation.py](tests/test_markdown_artifact_generation.py).

What changed:
- title repair no longer rewrites already-valid formal titles just because the question is generic
- title repair now mutates title structure only when the title itself is weak
- question repair can still run independently
- the title/question separation rationale is preserved unless the title truly needs repair

Focused retest passed:
- `python3 -m unittest tests.test_markdown_artifact_generation`
    - `Ran 6 tests`, `OK`
- `python3 -m unittest tests.test_markdown_ir tests.test_markdown_artifact_generation tests.test_title_depth`
    - `Ran 19 tests`, `OK`

OpenAI markdown-learn rerun also completed:
- report: [title_depth_openai_repair_report.json](reports/title_depth_openai_repair_report.json)
- state: [title_depth_openai_repair_state.json](reports/title_depth_openai_repair_state.json)
- db: [title_depth_openai_repair.sqlite3](state/title_depth_openai_repair.sqlite3)

The key result is that the knowledge titles are no longer being stored as raw numbered headings. They now come out like:
- `Cylinder Measures / Named quantities`
- `Cylinder Measures / Total surface area of a cylinder`
- `Cylinder Measures / Volume of a cylinder`
- `Cylinder Measures / Distinguishing the measures`

The repair layer works. The remaining gap is semantic richness, not heading leakage: titles such as `Named quantities` and `One-sentence summary` are categorized, but they remain too thin to be ideal long-term graph identities. A subsequent refinement should require weak generic current identities to be rewritten from encounter content rather than merely cleaned and categorized.
