```python
python3 -m unittest tests.test_boundary_shape_typing tests.test_decomposition_prompt_context tests.test_function_boundary tests.test_markdown_learning

set -a; source local.env >/dev/null 2>&1 || true
export LLM_PROVIDER=openai
export LLM_TIMEOUT_SECONDS=180

python3 main.py run --prompt 'I need to decide whether the medicine bottle on my desk says 10 mg or 100 mg. What should I do next?' --llm required --max-steps 24 --state-out reports/human_loop_probe_desk_label_260324.json
python3 main.py run --prompt 'Which of my handwritten notes says the bank account number? I have not provided the notes.' --llm required --max-steps 24 --state-out reports/human_loop_probe_handwritten_notes_260324.json
python3 main.py run --prompt 'You cannot determine this without me. Which of my private paper notes contains the bank account number? Pause and require human contribution rather than guessing.' --llm required --max-steps 24 --state-out reports/human_loop_probe_explicit_human_260324.json

export STATE_SQLITE_PATH=state/newton_force_learning_2603231954.sqlite3
python3 main.py run --prompt 'Calculate force for mass=3 and acceleration=4.' --llm off --max-steps 24

export STATE_SQLITE_PATH=state/pythagorean_learning_2603232131.sqlite3
python3 main.py run --prompt 'Calculate the length of the slanted side of a right angeled triangle if the other two sides are 5 metres each' --llm off --max-steps 24

export STATE_SQLITE_PATH=state/momentum_learning_260323214829.sqlite3
python3 main.py run --prompt 'Calculate momentum for mass=8 and velocity=12.' --llm off --max-steps 24


```