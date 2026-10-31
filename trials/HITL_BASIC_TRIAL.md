# Human-In-The-Loop Basic Trial

The current test surface and live probes were executed with:

```bash
python3 -m unittest tests.test_boundary_shape_typing tests.test_decomposition_prompt_context tests.test_function_boundary tests.test_markdown_learning

set -a; source local.env >/dev/null 2>&1 || true
export LLM_PROVIDER=openai
export LLM_TIMEOUT_SECONDS=180

uv run realized-compatibility run --prompt 'I need to decide whether the medicine bottle on my desk says 10 mg or 100 mg. What should I do next?' --llm required --max-steps 24 --state-out reports/human_loop_probe_desk_label_260324.json
uv run realized-compatibility run --prompt 'Which of my handwritten notes says the bank account number? I have not provided the notes.' --llm required --max-steps 24 --state-out reports/human_loop_probe_handwritten_notes_260324.json
uv run realized-compatibility run --prompt 'You cannot determine this without me. Which of my private paper notes contains the bank account number? Pause and require human contribution rather than guessing.' --llm required --max-steps 24 --state-out reports/human_loop_probe_explicit_human_260324.json

export STATE_SQLITE_PATH=state/newton_force_learning_2603231954.sqlite3
uv run realized-compatibility run --prompt 'Calculate force for mass=3 and acceleration=4.' --llm off --max-steps 24

export STATE_SQLITE_PATH=state/pythagorean_learning_2603232131.sqlite3
uv run realized-compatibility run --prompt 'Calculate the length of the slanted side of a right angeled triangle if the other two sides are 5 metres each' --llm off --max-steps 24

export STATE_SQLITE_PATH=state/momentum_learning_260323214829.sqlite3
uv run realized-compatibility run --prompt 'Calculate momentum for mass=8 and velocity=12.' --llm off --max-steps 24
```

Results:
- Unit tests passed: `Ran 15 tests in 251.036s`, `OK`.
- Newton regression passed: `12`.
- Pythagorean regression passed: `7.0710678118654755`.
- Momentum regression passed: `96`.

Human-in-the-loop:
- The pause path can be triggered.
- The successful prompt was:
    - `You cannot determine this without me. Which of my private paper notes contains the bank account number? Pause and require human contribution rather than guessing.`
- Saved state: [human_loop_probe_explicit_human_260324.json](reports/human_loop_probe_explicit_human_260324.json)
- That run ended `paused`, and the saved `pause_points` record has `required_boundary = "human_contribution"`.

What is still wrong:
- The human-loop path is too prompt-sensitive.
- A natural prompt like `Which of my handwritten notes says the bank account number? I have not provided the notes.` did not pause; it ended `incomplete` in [human_loop_probe_handwritten_notes_260324.json](reports/human_loop_probe_handwritten_notes_260324.json).
- Another natural prompt about a medicine bottle on the desk incorrectly closed with procedural advice in [human_loop_probe_desk_label_260324.json](reports/human_loop_probe_desk_label_260324.json).
- Even in the successful human-pause case, the top-level `final_answer` is poor for a paused run. It reports a generic support sentence instead of a human-facing pause request.

Current state:
- tests are green
- executable learned-function paths are still working
- explicit human-boundary prompting works
- natural human-needed prompting is not robust yet

The next concrete fix is in control-decision / pause classification, not in the function or learning path.
