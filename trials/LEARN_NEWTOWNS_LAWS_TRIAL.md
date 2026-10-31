# Newton's Laws Learning Trial

The implementation was added in [main.py](main.py#L1466), [main.py](main.py#L5842), [main.py](main.py#L6597), [main.py](main.py#L7840), [main.py](main.py#L7935), [main.py](main.py#L7977), and [main.py](main.py#L9873).

What changed:
- Added `cross_boundary`, which writes a Python script string to a temp file and runs it through `uv run --no-project`, feeding structured JSON input and parsing structured stdout.
- Added real execution support for `function_bit = 1` artifacts. They are no longer passive metadata.
- Direct-resolution and realization-witness prompts can now return `function_artifact` plus `invocation_payload` for parameterized/calculation cases.
- Generated function artifacts are only admitted/persisted after successful execution, to avoid learning broken placeholder scripts.
- Reuse now executes learned function artifacts when matched, instead of requiring a static `answer`.
- Default ability scripts now expose `status`, `answer`, `result`, and `notes`.

The local regression suite in [tests/test_function_boundary.py](tests/test_function_boundary.py#L76) covers:
- raw `cross_boundary` execution
- parameter extraction into a function artifact
- learned `function_bit=1` reuse through the controller

Validation run:
```bash
uv run python -m py_compile compatibility_api/src/main.py tests/test_function_boundary.py tests/test_markdown_learning.py
python3 -m unittest tests/test_function_boundary.py
set -a; source local.env >/dev/null 2>&1 || true; python3 -m unittest tests/test_markdown_learning.py
```

Results:
- `test_function_boundary.py`: `Ran 3 tests`, `OK`
- `test_markdown_learning.py`: `Ran 4 tests`, `OK`

Explicit `f = ma` validation:
- controller-level reuse of a stored function artifact with `mass=3 acceleration=4`
- result: `attached=true`, `ready_for_commitment=true`, `answer="12"`, `confidence="high"`

Current boundary:
- automatic input extraction for function artifacts is structural, not magical. It currently handles explicit JSON and named inputs like `mass=3 acceleration=4`.
- fully free-form natural-language parameter extraction still belongs in the LLM proposal path.
