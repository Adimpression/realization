# Core Runtime Determinism + Replay (reduce_not) Implementation Plan

## Purpose

This document is a concrete engineering plan for tightening the core runtime around:

- `reduce_not`-driven governed execution
- determinism knobs (what the runtime can *claim* is replayable, and under what constraints)
- replayability (what must be preserved and how we verify it)

The intent is to make the repo’s Deterministic profile in [OPEN_GOVERNANCE.md](OPEN_GOVERNANCE.md) implementable as real, testable runtime behavior, not only as a declaration.

Scope boundary:

- In scope: core controller runtime (`run` / `resume`), LLM supplement boundary, run bundle export, replay verification.
- In scope: DST discovery/normalization only as a *consumer* of the same runtime determinism + replay substrate.
- Out of scope: remote storage/services; workstation UI product work; changing the closed core theory.

---

## Current Baseline (What Exists Today)

### 1. Runtime reduction is already governed and step-recorded

Primary loop:

- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)
  - `run(max_steps=...)`: frontier stepping + recursion
  - `reduce_not(node, visiting=...)`: recursive descent, decomposition/refinement, closure/pause/incompletion
  - `pop_best_frontier()`: candidate selection proposal, stable tie-breaking and ordering for the *candidate list*

Step recording:

- [system_state.py](system_state.py) `SystemState.record_step(...)` appends a `StepRecord` into:
  - `ledger` (full history)
  - `trace` (same today; later we may differentiate)

Note:

- `StepRecord` includes timestamps today; replay comparison does not currently depend on them.

### 2. LLM supplementation is explicitly proposal-only and already “best-effort deterministic”

LLM supplement contract:

- [LLM.md](LLM.md)
- [supplement.py](supplement.py)

Key implemented properties:

- LLM outputs only create `ProposalObject` payloads, never direct commitments.
- Default request posture is conservative:
  - `temperature=0.0`
  - `response_format={"type": "json_object"}`
  - explicit schema-shape hint derived from heuristic fallback payload
- Policy knob exists: `--llm off|auto|required` and `LLM_SUPPLEMENT_POLICY`

Reality check:

- Temperature 0 is “least random” but not a cryptographic determinism guarantee. Even pinned prompts/params can change when provider-side backend changes, model snapshots change, or floating point kernels differ.
- Therefore: if we want deterministic/replayable claims, we need an explicit runtime definition that treats live LLM calls as nondeterministic unless they are recorded and replayed from a frozen transcript.

### 3. Run bundles and replay verification exist and are already useful

Run bundle:

- [run_bundle_io.py](run_bundle_io.py)
- Schema: `bssc_run_bundle.v1`
- Captures:
  - prompt, run outcome, final answer
  - governance rules + controller feature toggles
  - *metadata* `llm_policy` and `max_steps`
  - constitutional trace snapshot
  - governance snapshot receipts (policy/approval/revocation/incident/registry)
  - the referenced skills required for replay

Replay verification:

- [replay_verifier.py](replay_verifier.py)
- Reconstructs a fresh store, imports bundled skills, re-runs the prompt, then compares:
  - final answer
  - run outcome
  - effect trace signatures (including receipt digests)
  - composition-chain signatures (semantic development path)
  - governance snapshot receipts

Existing regression surface:

- [tests/test_run_bundle_io.py](tests/test_run_bundle_io.py)

### 4. Where DST currently hooks into this substrate

DST discovery/normalization uses the same governed proposal boundary:

- [dst/src/dst/orchestration.py](dst/src/dst/orchestration.py)
  - emits `ProposalType.DST_DISCOVERY` and `ProposalType.DST_NORMALIZATION`
- [dst/src/dst/discovery.py](dst/src/dst/discovery.py)
- [dst/src/dst/normalization.py](dst/src/dst/normalization.py)

This is important for determinism because:

- DST uses LLM-generated structured JSON to produce typed CTFS models.
- For “Deterministic.Replay” claims we must be able to re-run that generation deterministically or replay it from a transcript.

---

## Problem Statement (What Is Missing)

### A. The repo can replay effects and semantic development, but not “the decision flow”

Today replay compares:

- effect traces and their receipts
- composition chain signatures
- final answer

But we do not yet have replay assertions that cover:

- the *proposal decisions* that caused a branch to be taken
- the *frontier selection decisions* that shaped the reduction order
- the supplement request/response digests that produced key proposals

This means:

- replay can prove “same output + same effect boundary”
- replay cannot yet prove “same internal governed path justified it”

That gap matters directly for:

- `Deterministic.TraceCompleteness`
- drift control (“why did this run change?”)

### B. Determinism is not a first-class runtime contract yet

We have:

- `--llm off|auto|required`
- feature toggles for `discovery/reflection/contemplation`

We do not have:

- an explicit `determinism mode` that constrains the runtime and what it is allowed to do
- a uniform way to *bind* determinism settings into the state/bundle for replay
- a uniform way to declare: “this run is replayable” vs “this run is governed but nondeterministic”

### C. “LLM determinism” is not currently recordable/replayable

Even with temperature 0, live providers may vary.

For deterministic claims, the runtime needs one of:

1. LLM-off execution (pure heuristic + deterministic structure)
2. LLM-recorded execution (record supplement calls and replay from transcript)
3. LLM-replay execution (no provider calls; strictly consume transcript)

Today we have none of (2) and (3) in the core runtime/bundle.

---

## Target Contract (What We Want)

### 1. Explicit runtime determinism posture

Introduce a first-class execution posture with three levels:

1. `governed` (default)
   - LLM may be used (`auto|required`), host effects may occur when admitted.
   - Replay is “best effort”: compares effect boundary + composition chain + final answer.
   - This posture MUST NOT be marketed as deterministic.

2. `deterministic` (claimable)
   - LLM is either fully off, or strictly transcript-backed.
   - Any non-deterministic inputs are either banned or fully recorded.
   - Run bundles include determinism settings and the replay transcript when relevant.

3. `replay` (verification posture)
   - No provider calls.
   - Reconstruct execution from bundle + transcript + bounded deterministic runtime.
   - Output includes a structured mismatch report (what diverged and where).

### 2. Replay must be decision-aware, not only outcome-aware

For deterministic claims, replay verification must cover:

- effect boundary equality (already present)
- semantic development path equality (already present)
- a stable signature of the controller decision flow:
  - frontier selection decisions
  - supplement proposal request/response receipts
  - proposal governance decisions (admit/reject/revise)
  - commit/pause/incompletion decisions

This does not require full byte-identical logs.
It requires stable *decision receipts* that can be canonicalized.

---

## Concrete Implementation Plan (Incremental, Backwards-Compatible)

### Phase 0: Document the determinism contract (this file) and link it

Changes:

- Add this plan document.
- Link it from:
  - README (as a “core runtime” tracker)
  - OPEN_GOVERNANCE deterministic sections (as implementation pointer)

No code changes.

### Phase 1: Add a typed determinism policy object (additive)

Goal:

- Make determinism settings explicit, serializable, and bundleable.

Add a new dataclass (name suggestion):

- `RuntimeDeterminismPolicy` in `applied_theory_types.py`

Fields (initial cut):

- `mode`: `governed|deterministic|replay`
- `llm_strategy`: `off|live|record|replay`
- `llm_seed`: `int|None`
- `llm_system_fingerprint`: `str|None` (captured from provider responses when available)
- `clock_strategy`: `real|frozen|canonicalized`
- `random_strategy`: `real|seeded`
- `host_effect_strategy`: `allow|deny|record_only`
- `note`: freeform text for operator/CI labeling

Wiring points:

- `SystemState` gains `determinism_policy: RuntimeDeterminismPolicy` with default `mode="governed"`.
- `run_bundle_document(...)` includes the serialized policy under `run.determinism_policy`.
- `replay_run_bundle_document(...)` uses it to decide how strict replay must be.

Backwards compatibility:

- If `determinism_policy` is absent (older bundles/state), default to `mode="governed"`.

Tests:

- Unit tests for `to_dict/from_dict` stability.
- Run-bundle round-trip tests asserting the policy is present when set.

### Phase 2: Introduce “supplement receipts” and a transcript cassette (additive)

Goal:

- Enable deterministic runs that still use LLM assistance by recording and replaying supplement calls.

Add a transcript model:

- `LLMSupplementReceipt`:
  - `proposal_type`
  - `mode` (`fast|deep`)
  - request digest (canonical digest of system/dev msg, prompt text, schema hint, and selected parameters)
  - response digest (canonical digest of `raw_text` and parsed JSON payload)
  - provider/model/base_url
  - seed used (if any) + returned `system_fingerprint` (if present)
  - parsing status (ok/repair path used/error)

Where to capture:

- In [supplement.py](supplement.py):
  - extend `ask_llm(...)` to optionally accept `seed` for providers that support it
  - capture returned provider metadata if available (OpenAI exposes `system_fingerprint` on responses for some models/versions)
  - emit a `LLMSupplementReceipt` per `propose_json(...)` call

Where to store:

- Add `SystemState.llm_transcript: list[dict[str, Any]]` (append-only)
- Or store under `SystemState.trace` as `record_step(kind="llm_supplement", payload=receipt)`
  - Prefer a dedicated `llm_transcript` collection so the bundle export boundary is explicit.

How replay uses it:

- Implement `llm_strategy="replay"`:
  - disable provider calls
  - satisfy `propose_json(...)` from the transcript by matching `(proposal_type, mode, request_digest)`
  - if mismatch: fail with a structured “receipt mismatch” explaining what differs

How record uses it:

- Implement `llm_strategy="record"`:
  - allow provider calls
  - store receipts as above

Backwards compatibility:

- Existing controllers without transcript remain unchanged.
- Existing bundles without transcript remain replayable in “governed” mode.

Tests:

- New tests that:
  - run a small controller path with a mocked LLM (deterministic)
  - export a bundle including transcript
  - replay with provider disabled and transcript-backed supplement
  - assert replay equality for:
    - final answer
    - composition chain signature
    - effect trace signatures (if any)
    - transcript receipt signatures

### Phase 3: Add a stable “decision-flow signature” for deterministic replay

Goal:

- Make replay “decision aware” without requiring byte-identical logs.

Add a canonical signature extractor:

- `controller_decision_flow_signature(state) -> list[dict[str, Any]]`

Inputs:

- `state.trace` (StepRecords) + optional `llm_transcript`

Canonicalization rules:

- ignore timestamps
- ignore volatile ids except where they are the *semantic* subject (ex: proposal ids should be replaced with stable digests)
- preserve:
  - `kind`
  - `action` (or an enumerated action family)
  - salient payload fields (candidate ordering digests, selected candidate id digest, governance decision)

Where to store:

- In constitutional trace snapshot:
  - add `decision_flow_signatures`
  - add a digest receipt for it

Where to compare:

- `compare_bundle_trace_to_state(...)` should compare this in deterministic/replay mode.

Backwards compatibility:

- For older bundles: the field is missing, so “governed replay” does not check it.
- Only `mode in {"deterministic","replay"}` requires it.

Tests:

- Extend [tests/test_run_bundle_io.py](tests/test_run_bundle_io.py) with a deterministic-mode case that asserts:
  - decision flow signature matches during replay.

### Phase 4: Tighten reduce_not determinism (remove incidental nondeterminism)

Goal:

- ensure the non-LLM path is stable across runs, and that the LLM-record/replay path matches request digests.

Concrete audit checklist (apply systematically across core runtime seams):

- Any iteration over `set` must be sorted before use in decision shaping or prompt shaping.
- Any iteration over `dict` must be stable (insertion order is stable, but only if the dict was built deterministically).
- Any “top K” selection must:
  - specify a stable tie-breaker
  - record the candidate order/digest into a step receipt
- Any randomness must be:
  - forbidden in deterministic mode, or
  - derived from an explicit seeded PRNG bound into `RuntimeDeterminismPolicy`

Concrete files to inspect/patch (in order):

- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)
- [fallback_not_generation.py](core_engine/src/realized_core_engine/fallback_not_generation.py)
- [not_elaboration_ranking.py](core_engine/src/realized_core_engine/not_elaboration_ranking.py)
- [retrieval_ranking.py](retrieval_ranking.py)
- [title_semantics.py](title_semantics.py)

Tests:

- Add a small deterministic regression pack (see Phase 5) that runs the same prompt twice under `llm=off` and asserts:
  - composition chain signature equality
  - decision flow signature equality

### Phase 5: Add a “controller drift replay pack” aligned with the determinism contract

Goal:

- Make “determinism + replay” a routine guardrail, not an aspirational feature.

This should build on [HEURISTIC_DETERMINISTIC_SCALE_IMPLEMENTATION.md](HEURISTIC_DETERMINISTIC_SCALE_IMPLEMENTATION.md):

- Convert known historical regressions into small deterministic replay sentinels.
- Store them as inlined Python tests (no external fixtures) when the behavior is small enough.
- Store bundle-like sentinels only when:
  - effect traces matter, or
  - LLM transcript replay is being exercised.

Deliverable:

- `tests/test_controller_determinism_replay_pack.py`
  - each case is a “prompt + store seed + expected decision signatures”
  - each case is runnable under `llm=off`

### Phase 6: Extend deterministic posture to DST (consumer validation)

Goal:

- Ensure DST discovery/normalization can be replay-verified under deterministic claims.

Approach:

- When `determinism_policy.llm_strategy="replay"`:
  - DST discovery and normalization must consume transcript-backed LLM proposals.
- When `llm_strategy="off"`:
  - DST should have a deterministic fallback posture:
    - fixtures for tests
    - heuristic no-op / “needs operator input” behavior for non-fixture runs

Tests:

- `dst/tests`:
  - a deterministic-run test for a fixture case that runs:
    - discovery -> normalization
    - export run bundle
    - replay with transcript-backed supplement
    - verify decision flow signatures remain stable

---

## Compatibility and Rollout Strategy

### Backwards compatibility guarantees

- Existing CLI flags keep their meaning.
- Existing run bundles (`bssc_run_bundle.v1`) remain readable.
- Deterministic enforcement is opt-in via `determinism_policy.mode`.

### Migration mechanics

- Add new fields to run bundle under `run.*` and `constitutional_trace.*`.
- Treat the schema as “v1 + additive fields” initially.
- Only bump schema version when we need a hard guarantee that fields exist.

### What should be considered “deterministic compliant” in this repo

To claim deterministic compliance for a run, we require:

- `determinism_policy.mode == "deterministic"`
- and either:
  - `llm_strategy == "off"`
  - or `llm_strategy == "record"` at capture time and `llm_strategy == "replay"` at verification time
- replay verification checks:
  - final answer equality
  - effect trace signature equality (if effects were present)
  - composition chain signature equality
  - decision flow signature equality
  - governance snapshot receipt equality

---

## Execution Checklist (What We Implement Next)

1. Implement `RuntimeDeterminismPolicy` and serialize it in `SystemState` and run bundles.
2. Implement LLM transcript receipts + `llm_strategy="replay"` runtime.
3. Add decision-flow signatures into constitutional trace and replay verifier.
4. Add deterministic regression pack tests (LLM off) and transcript-backed replay tests.
5. Apply the determinism audit checklist to eliminate incidental nondeterminism.
6. Validate DST discovery/normalization under transcript-backed deterministic replay.
