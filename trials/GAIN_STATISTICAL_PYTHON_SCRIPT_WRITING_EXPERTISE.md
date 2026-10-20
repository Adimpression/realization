# Gain Curriculum: Statistical Python Script Writing Expertise

This file defines a bounded expertise-gain curriculum for teaching a fresh
controller a narrow domain:

- basic statistical language
- basic Python scripting language
- inline-metadata Python scripts
- basic import and library use
- one concrete statistical scripting task: z-score calculation

The controller is assumed to begin with only general English, logic, and basic
math. This curriculum is therefore incremental by design.

## Goal

After the curriculum, the controller should be better able to:

- explain basic statistical terms
- explain basic Python scripting terms
- relate imports and libraries to scripts
- relate inline metadata to Python script execution
- explain what a z-score is and what inputs determine it
- write a simple Python script that computes a z-score

## Anti-Fake Constraint

This curriculum is not validated by one exact-repeat success.

It must distinguish:

1. exact recall
2. 
2. paraphrase transfer
3. compositional synthesis

## Execution Modes

Use an isolated temporary state DB for this curriculum. Do not use the normal
shared DB.

Suggested environment:

```bash
set -a
source local.env
export LLM_PROVIDER=openai
export STATE_DB_NAME=realization_gain_statistical_python
```

## Curriculum Structure

The curriculum is divided into:

- teaching prompts
- immediate probe prompts
- synthesis probes

The teaching prompts are allowed to introduce concepts. The probes are used to
see whether the controller can reuse what it harvested.

## Teaching Prompts

Run these in order.

1. `What is statistics?`
2. `What is Python scripting?`
3. `What does a basic Python script look like?`
4. `What is an inline metadata Python script?`
5. `What is a Python import?`
6. `What is a Python library?`
7. `How do you use a Python library using inline metadata?`
8. `Which Python library can help with statistics?`
9. `What is a z-score?`
10. `What inputs are needed to calculate a z-score?`
11. `What is the formula for a z-score?`
12. `Write a Python function that calculates a z-score from x, mean, and standard deviation.`
13. `Write a Python script that calculates a z-score.`

## Immediate Probes

These are intended to test near-transfer, not exact repetition.

1. `Statistics?`
2. `Python script?`
3. `How do imports relate to a Python script?`
4. `How do inline metadata and imports work together in a Python script?`
5. `Which Python library would you choose for a statistics script?`
6. `What does a z-score measure?`
7. `What values do I need before I can compute a z-score?`

## Synthesis Probes

These are the real expertise checks.

1. `Write a minimal inline-metadata Python script that imports a statistics-capable library.`
2. `Write a Python script that computes the z-score for x=12, mean=10, std=2.`
3. `Explain what each part of the z-score script is doing.`
4. `Write an inline-metadata Python script that reads x, mean, and std from JSON stdin and prints the z-score as JSON.`

## Stronger Generalization Probes

These should be run after the earlier sequence if the controller is behaving
well.

1. `What is the sum of the ideas behind statistics and Python scripting in one sentence?`
2. `What is the difference between a Python import and a Python library?`
3. `Write an inline-metadata Python script that uses a statistics library to compute a z-score and prints the result.`
4. `If x=14, mean=11, and std=1.5, what z-score would your script produce?`

## Expected Evidence of Learning

The controller should show at least some of the following:

- later prompts load learned artifacts from the isolated DB
- later prompts close with fewer blockers than equivalent fresh-state runs
- later prompts produce knowledge or closure-pattern artifacts related to the
  taught expertise
- exact-repeat prompts may be answered by direct learned reuse
- paraphrase probes may still require the LLM, but should show relevant learned
  artifacts in context

## What Does Not Count As Learning

The following do not count:

1. only the exact original prompt can be answered later
2. the controller answers correctly only because the base model already knew it,
   while `learned_artifacts` stays empty or irrelevant
3. script-writing prompts succeed, but no artifacts related to scripting,
   knowledge, or closure are harvested
4. paraphrase probes fail in the same way as a fresh-state baseline and no reuse
   appears

## Minimum Acceptance Signals

At minimum, a reasonable gain run should show:

1. the teaching prompts complete cleanly
2. at least one knowledge artifact related to Python/statistics is harvested
3. at least one later prompt loads relevant learned artifacts
4. at least one probe benefits from prior learning in a way visible in state
5. the final z-score script prompt completes with an answer-bearing witness
6. at least one z-score-related artifact is reusable as either knowledge or a function-bearing ability

## Recommended Evaluation Pattern

Use this order:

1. cold baseline on two target probes with DB disabled
2. run the full teaching curriculum against the isolated DB
3. rerun exact-repeat probes with DB enabled
4. run paraphrase probes with DB enabled
5. run synthesis probes with DB enabled
6. compare:
   - correctness
   - `learned_artifacts`
   - proposal count
   - ledger evidence of learning-context load
   - latency

## Notes

- Exact-repeat improvement demonstrates durable recall.
- Paraphrase improvement demonstrates transferable reuse.
- Synthesis improvement demonstrates actual expertise growth.
- If only exact-repeat improves, the system is learning narrowly.
- If paraphrase and synthesis improve, the system is learning more like a real
  expertise gain.
