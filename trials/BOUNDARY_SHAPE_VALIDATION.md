# Boundary Shape Validation

This suite is meant to test artifact-side boundary shape end to end:
- storage outside the JSON blob
- retrieval selection
- executable invocation
- disambiguation between semantically related artifacts with different boundary shapes

It uses a fresh SQLite store and imported deterministic ability artifacts from:

- `tests/fixtures/boundary_shape_artifacts/hi_responder.yaml`
- `tests/fixtures/boundary_shape_artifacts/personalized_greeter.yaml`
- `tests/fixtures/boundary_shape_artifacts/file_greeting_reader.yaml`
- `tests/fixtures/boundary_shape_artifacts/hi_email_sender.yaml`

## Fast Run

Run the automated suite:

```bash
python3 boundary_shape_validation.py
```

It writes a fresh DB and a report under `reports/boundary_shape_validation_<timestamp>/`.

The report checks four cases:

1. `Say hi.`
   Expected artifact: `Hi Responder`
   Expected boundary shape: `d*`

2. `Say hi to name='Ada'.`
   Expected artifact: `Personalized Greeter`
   Expected boundary shape: `a* d*`

3. `Read the greeting from path='...'.`
   Expected artifact: `File Greeting Reader`
   Expected boundary shape: `a'* b'* d*`

4. `Send an email to recipient='alice@example.com' message='hi'.`
   Expected artifact: `Hi Email Sender`
   Expected boundary shape: `a* c*`

For each case the suite also requires:
- `run_outcome = completed`
- correct `final_answer`
- `cross_boundary_execution = true`

## Manual CLI Run

Pick a fresh DB path:

```bash
export STATE_SQLITE_PATH=state/boundary_shape_manual.sqlite3
unset STATE_DB_URL STATE_DB_HOST STATE_DB_PORT STATE_DB_USER STATE_DB_PASSWORD STATE_DB_NAME
```

Import the fixtures:

```bash
python3 main.py artifact-import \
  --artifact-dir tests/fixtures/boundary_shape_artifacts \
  --normalized-out-dir reports/boundary_shape_manual_normalized
```

Create a file for the read-reference test:

```bash
printf 'hi from file\n' > /tmp/boundary_shape_greeting.txt
```

Run the prompts:

```bash
python3 main.py run --prompt "Say hi." --llm off --max-steps 24
python3 main.py run --prompt "Say hi to name='Ada'." --llm off --max-steps 24
python3 main.py run --prompt "Read the greeting from path='/tmp/boundary_shape_greeting.txt'." --llm off --max-steps 24
python3 main.py run --prompt "Send an email to recipient='alice@example.com' message='hi'." --llm off --max-steps 24
```

Expected top-level `final_answer` values:

```text
hi
hi, Ada
hi from file
simulated send to alice@example.com: hi
```

## Manual Verification

To prove the correct artifact fired, save state and inspect the evidence context:

```bash
python3 main.py run \
  --prompt "Send an email to recipient='alice@example.com' message='hi'." \
  --llm off \
  --max-steps 24 \
  --state-out reports/boundary_shape_manual_email.json
```

Then inspect:

```bash
python3 main.py inspect \
  --state reports/boundary_shape_manual_email.json
```

You should see:
- an evidence `context.artifact_id`
- `context.cross_boundary_execution = true`

Then check the stored boundary terms for that artifact:

```bash
python3 - <<'PY'
import sqlite3
db = "state/boundary_shape_manual.sqlite3"
artifact_id = "REPLACE_WITH_ARTIFACT_ID_FROM_STATE"
con = sqlite3.connect(db)
rows = con.execute(
    "SELECT boundary_term FROM bssc_artifact_boundary_shape_terms WHERE artifact_id = ? ORDER BY term_index",
    (artifact_id,),
).fetchall()
print([row[0] for row in rows])
con.close()
PY
```

Expected terms by case:

```text
Hi Responder -> ['d*']
Personalized Greeter -> ['a*', 'd*']
File Greeting Reader -> ["a'*", "b'*", 'd*']
Hi Email Sender -> ['a*', 'c*']
```

## Why These Cases Matter

This suite is not just checking execution. It is checking selection pressure.

- `Say hi.` must not drift into the email sender.
- `Send an email ...` must not collapse to the output-only responder.
- `Read the greeting from path=...` must choose a read-reference artifact rather than a generic greeting artifact.
- `Say hi to name='Ada'.` must choose the value-parameterized artifact instead of the zero-input responder.

If those distinctions fail, boundary shape is being stored but not actually governing reuse.
