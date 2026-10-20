# Learned Function Validation

This is the operator-facing suite for validating learned executable artifacts from fresh markdown learning runs.

It checks the full path:

1. learn from a markdown curriculum into a fresh SQLite/vector store
2. ensure the learned store contains at least one `ability` artifact with `function_bit = 1`
3. invoke the controller with `--llm off`
4. verify the final answer is numerically correct
5. verify the answer came from cross-boundary execution of a learned function artifact

## What it covers

The suite currently validates:

* Newton force calculation from [LEARN_NEWTOWNS_LAWS.md](LEARN_NEWTOWNS_LAWS.md)
* Pythagorean hypotenuse calculation from [GAIN_PYTHOGOREAN_THEORM.md](GAIN_PYTHOGOREAN_THEORM.md)
* Momentum calculation from [LEARN_MOMENTUM.md](LEARN_MOMENTUM.md)

Each domain is learned into its own fresh SQLite file under the run report directory.

## Run it

Prerequisite:

* `OPENAI_API_KEY` must be available in the environment or in [local.env](local.env)

Command:

```bash
python3 learned_function_validation.py
```

Optional deterministic seed:

```bash
python3 learned_function_validation.py --seed 42
```

Optional explicit report directory:

```bash
python3 learned_function_validation.py \
  --report-dir reports/manual_learned_function_validation
```

Optional subset run:

```bash
python3 learned_function_validation.py \
  --domains pythagorean_hypotenuse
```

## What success looks like

The script prints a JSON report and writes the same report to:

* `reports/learned_function_validation_<timestamp>/report.json`

For each domain it reports:

* the fresh SQLite path
* the markdown learn report/state paths
* how many `function_bit = 1` ability artifacts were persisted
* each probe prompt
* the expected and observed numeric value
* the selected artifact id/title/type
* whether `cross_boundary_execution` was true

The overall run succeeds only if:

* the learn phase succeeds
* at least one `function_bit = 1` ability artifact is persisted per domain
* each off-LLM prompt completes
* each final numeric answer matches expectation
* the answer came from a learned ability artifact with `function_bit = 1`
* the saved evidence context reports `cross_boundary_execution = true`

## Prompts the suite exercises

The suite intentionally uses operator-friendly prompts that you can run manually after learning:

### Newton

* `Calculate force for mass=3 and acceleration=4.`
* `Use Newton's second law to compute force with mass=5 and acceleration=2.`
* `What force do you get for mass=6 and acceleration=3?`

### Pythagorean

* `Calculate the length of the slanted side of a right angeled triangle if the other two sides are 5 metres each`
* `What is the length of the hypotenuse when a=3 and b=4?`
* `Calculate the slanted side if a=8 and b=15.`

### Momentum

* `Calculate momentum for mass=8 and velocity=12.`
* `Calculate momentum for mass=10 and velocity=5.`
* `What is the momentum when mass is 8 and velocity is 6?`

Note:

* the third Newton and momentum prompts are deterministic from the suite seed
* if you change the seed, the report becomes the authoritative run record for those generated cases

## How to inspect failures

If a case fails, inspect:

* the per-domain learn report
* the per-case state JSON
* the domain SQLite DB

The saved state JSON is the best place to confirm whether:

* the final answer was missing or wrong
* the wrong artifact was selected
* `cross_boundary_execution` did not occur
* the controller fell back to non-executable learned support instead of a function artifact

## Manual follow-up

After a successful learn run for a given domain, you can manually reuse the learned DB by exporting its SQLite path into `STATE_SQLITE_PATH` and then invoking `main.py run --llm off` with the same style of prompts.
