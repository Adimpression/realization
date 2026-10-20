# V2.0.3 - LLM Supplements in `main.py`

## 1. Status

This document describes the LLM supplement layer that is actually implemented in `main.py`.

It replaces the older theory-heavy note. If this document and the code diverge, `main.py` wins.

The key invariant is unchanged:

> The LLM belongs to the space of governable proposals, not to the space of justified commitments.

In code terms, the LLM may generate `ProposalObject` payloads. The controller still owns admission, revision, rejection, evidence handling, certainty-state updates, pausing, closure, artifact registration, and persistence, even when some working assessments are proposal-informed.

---

## 2. Core Contract

The supplement layer is conservative in four ways:

1. Every LLM output is wrapped as a `ProposalObject`.
2. Proposal generation is separated from proposal governance.
3. No LLM call directly closes a node, assigns final certainty, or admits evidence.
4. If the LLM path fails, the controller falls back to bounded heuristic payloads instead of giving the model extra authority.

The operational shape is:

```text
governed state slice
  -> supplement call
  -> JSON payload
  -> ProposalObject registration
  -> admit / revise / reject
  -> controller uses the proposal under normal governance
```

---

## 3. Runtime Model

### 3.1 Providers

The current implementation supports exactly two providers:

- `openai`
- `llamacpp`

`llamacpp` is treated as an OpenAI-compatible HTTP endpoint. Its base URL is normalized to end in `/v1`, and the code may try to discover a model by querying `GET /models`.

### 3.2 Policy

The controller accepts `--llm off|auto|required`.

- `off`: disable supplements entirely.
- `auto`: use supplements when the provider is available; otherwise continue with heuristics.
- `required`: fail if the configured provider is unavailable.

Availability is computed as follows:

- `openai`: enabled only if `OPENAI_API_KEY` is present.
- `llamacpp`: treated as enabled whenever that provider is selected.

### 3.3 Required Python Client

The code uses the `openai` Python package for both providers.

If that package is missing, supplement calls fail.

### 3.4 Environment Variables

| Variable | Meaning | Default |
| --- | --- | --- |
| `LLM_PROVIDER` | Provider name: `openai` or `llamacpp` | `openai` |
| `OPENAI_API_KEY` | API key for `openai` | none |
| `OPENAI_MODEL` | Default OpenAI model | empty |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible base URL override | none |
| `LLAMACPP_BASE_URL` | Base URL for local `llamacpp` server | `http://127.0.0.1:8080` |
| `LLAMACPP_MODEL` | Preferred `llamacpp` model | none |
| `LLAMACPP_API_KEY` | API key sent to `llamacpp` endpoint | `llama.cpp` |
| `LLM_FAST_MODEL` | Override model for fast mode | falls back to provider default |
| `LLM_DEEP_MODEL` | Override model for deep mode | falls back to provider default |
| `LLM_FAST_MAX_TOKENS` | Max completion tokens for fast mode | `3072` |
| `LLM_DEEP_MAX_TOKENS` | Max completion tokens for deep mode | `4096` |
| `LLM_TIMEOUT_SECONDS` | Client timeout for each call | `30.0` for OpenAI, `2.5` for llama.cpp |
| `LLM_SUPPLEMENT_POLICY` | Default CLI policy | `auto` |

Model resolution is provider-specific:

- `openai`: use `LLM_FAST_MODEL` or `LLM_DEEP_MODEL` when set, otherwise `OPENAI_MODEL`.
- `llamacpp`: use the explicit fast/deep override if present; otherwise `LLAMACPP_MODEL`; otherwise a discovered `/models` entry; otherwise `OPENAI_MODEL`; otherwise `local-model`.

---

## 4. How a Supplement Call Is Built

All supplement calls flow through `LLMSupplement.propose_json(...)`.

Each request contains:

- a short developer message instructing the model to return exactly one JSON object
- a task label derived from `ProposalType`
- a depth label: `quick pass` for `fast`, `deeper pass` for `deep`
- a schema hint taken from the fallback payload
- a governed state snapshot from `proposal_state_slice(...)`

The prompt state slice is important. It includes:

- the overall task id, focus, status, and certainty
- up to 6 learned artifacts already loaded from the artifact store
- the current frontier size
- the last 6 ledger steps
- the active item, if any:
  - status, role, depth, certainty, blockers, conflicts
  - support ids and evidence summaries
  - pause points
  - child summaries

The request is JSON-only by design:

- `temperature=0.0`
- `response_format={"type": "json_object"}`
- `reasoning_effort="minimal"` in fast mode
- `reasoning_effort="medium"` in deep mode

`ask_llm(...)` contains provider compatibility retries:

- if `max_tokens` is rejected, retry with `max_completion_tokens`
- if `reasoning_effort` is rejected, drop it and retry
- if `temperature` is rejected, drop it and retry
- if `response_format` is rejected, drop it and retry

Returned text is parsed by `_extract_json_payload(...)`, which accepts:

- raw JSON
- fenced JSON
- the first embedded object or array found in the response

If parsing still fails:

- `required` policy raises
- otherwise the call falls back to the heuristic schema payload

`LLMSupplementResult.source` is one of:

- `llm`
- `heuristic`
- `disabled`

---

## 5. Modes

### 5.1 Meaning

The code defines two supplement modes:

- `fast`
- `deep`

These are not just labels. They affect:

- model selection
- token budget
- reasoning effort
- capability registration

When supplements are enabled, the controller registers two reusable capabilities:

- `llm_fast_supplement`
- `llm_deep_supplement`

Their `realizer` is recorded as `<provider>:<model>`.

### 5.2 Mode Selection Rules

The controller uses a mixture of forced mode selection and contextual selection.

Forced `fast`:

- `ControlDecisionProposal`
- `NodeAssessmentProposal`
- `CandidateSelectionProposal`
- `DirectResolutionProposal`

Forced `deep`:

- `ContemplationProposal`
- `RetrievalPlanProposal`
- `UncertaintyAssessmentProposal`
- `ReframeProposal`
- `DiscoveryAuditProposal`

Context-sensitive:

- `SemanticTargetProposal`
- `NotDecompositionProposal`
- `RealizationWitnessProposal`
- `CapabilityDraftProposal`
- `ReflectionProposal`
- `ExplanationDraft`
- `NextActionProposal`

The contextual rule is:

- use `deep` at the root
- use `deep` after the node has been visited more than once
- use `deep` when the node has more than one blocker
- otherwise use `fast`

---

## 6. Proposal Object and Governance

Every supplement payload is wrapped in:

```python
ProposalObject(
    id,
    proposal_type,
    target_scope,
    originating_not_id,
    mode,
    prompt_state_reference,
    revision_count,
    governance_status,
    payload,
    source,
    provider,
    model,
    rationale,
    raw_text,
    created_at,
)
```

### 6.1 Governance Status Values

The enum supports:

- `suggested`
- `admitted`
- `revised`
- `rejected`
- `holdon`
- `escalated`

Current `main.py` actively uses:

- `admitted`
- `revised`
- `rejected`

`holdon` and `escalated` exist in the type system but are not assigned in the current control flow.

### 6.2 Registration Effects

Every proposal is durably registered in:

- `SystemState.proposals`
- the ontology (`kind="proposal"`)
- the step ledger (`proposal_registered`)

Governance transitions are also ledgered via `proposal_governance`.

### 6.3 Cached Proposal Families

Two proposal types are cached against a local state snapshot:

- `ControlDecisionProposal`
- `NodeAssessmentProposal`

This avoids repeated supplement calls when the node state has not materially changed.

### 6.4 Deprecated Proposal Families

Older theory text mentioned `DutyFrameProposal` and `DutyTemplateProposal`.

The current code does not generate them. In fact, `SystemState.from_dict(...)` explicitly filters those proposal types out when loading older saved state.

Duty-like reuse now appears through artifact harvesting and template-bearing artifact types, not through live proposal families.

---

## 7. Implemented Proposal Catalog

### 7.1 Framing and Control

#### `SemanticTargetProposal`

Purpose:

- clarify the user request at root initialization

Key fields:

- `target_kind`
- `goal_statement`
- `scope_candidates`
- `exclusions`
- `ambiguity_notes`
- `alternate_semantic_framings`

Used in:

- `initialize_root_semantics()`

#### `ControlDecisionProposal`

Purpose:

- drive immediate local workflow control

Key fields:

- `should_pause`
- `pause_reason`
- `required_boundary`
- `needs_retrieval`
- `needs_reframe`
- `reframe_reason`
- `should_decompose`
- `can_refine_directly`
- `suggested_focus`

Used in:

- `should_pause()`
- `needs_reframing()`
- `pause_boundary_for()`
- `pause_reason()`
- other local control checks

#### `NodeAssessmentProposal`

Purpose:

- assess support, certainty, closure readiness, governance risk, and conflicts

Key fields:

- `support_score`
- `certainty`
- `ready_for_commitment`
- `should_reflect`
- `governance_violation`
- `governance_concerns`
- `conflict_descriptions`

Used in:

- `infer_support()`
- `infer_certainty()`
- `infer_status()`
- `surface_conflicts()`
- `has_governance_violation()`
- `is_committable()`

#### `CandidateSelectionProposal`

Purpose:

- order candidate nodes for frontier or child processing

Key fields:

- `selected_candidate_id`
- `ordered_candidate_ids`
- `rationale`

Used in:

- `pop_best_frontier()`
- child ordering

#### `ReflectionProposal`

Purpose:

- retrospective diagnostic review of the current local composition

Key fields:

- `coherence_assessment`
- `overscoping_detected`
- `relevance_judgment`
- `holdon_consistency_notes`
- `boundary_assessment`
- `recommended_mode`
- `issues_list`

Used in:

- `reflect()`

This proposal is advisory. It is admitted as working reflection state but does not change closure state directly.

#### `ContemplationProposal`

Purpose:

- compare plausible next trajectories

Key fields:

- `primary_trajectory`
- `alternates`
- `plausibility_ranking`
- `stop_conditions`
- `scope_elevation_rationale`

Used in:

- `contemplate()`

#### `ReframeProposal`

Purpose:

- suggest a better decomposition-scoped sibling framing

Key fields:

- `candidate_reframed_not`
- `reframing_reason`
- `semantic_loss_gain_notes`
- `preservation_obligations`

Used in:

- `reframe_upward()`
- `propose_higher_order_framing()`

#### `ExplanationDraft`

Purpose:

- generate a human-facing status note for trace reporting

Key fields:

- `summary`
- `progress_note`
- `continuation_note`
- `clarification_prompts`

Used in:

- `emit_trace_report()`

#### `NextActionProposal`

Purpose:

- propose a single best next action

Key fields:

- `action_kind`
- `reason`
- `focus`
- `needs`
- `stop_conditions`
- `alternates`

Status in current code:

- implemented as a helper
- not currently called from `run()` or `reduce_not()`

### 7.2 Reduction and Direct Realization

#### `NotDecompositionProposal`

Purpose:

- decide whether to keep the current item whole or split it into children

Key fields:

- `decompose_now`
- `preserve_parent`
- `preserve_reason`
- `children`
- `alternate_decompositions`

Used in:

- `decompose_or_refine()`

Important boundary:

- the LLM may suggest child nodes
- the controller still computes child faithfulness afterward with `semantic_bearing_level(...)`

#### `DirectResolutionProposal`

Purpose:

- decide whether the active item is trivial enough for immediate direct answer

Key fields:

- `resolved`
- `answer`
- `justification`
- `confidence`
- `closure_status`
- `answer_kind`

Used in:

- root-level `refine_directly()`

Important boundary:

- even a `ready` answer does not close the node by itself
- the controller first converts it into evidence and then re-runs normal support and commitment checks

#### `RealizationWitnessProposal`

Purpose:

- provide a bounded present realization when direct resolution was not admitted

Key fields:

- `realizable_now`
- `answer`
- `answer_kind`
- `witness_kind`
- `witness_steps`
- `validation_check`
- `confidence`
- `closure_status`

Used in:

- root-level `refine_directly()`

### 7.3 Pause, Retrieval, and Capability Emergence

#### `UncertaintyAssessmentProposal`

Purpose:

- structure why closure is premature

Key fields:

- `uncertainty_loci`
- `insufficiency_classes`
- `ambiguity_classes`
- `conflict_descriptions`
- `tests`
- `reasons_to_refrain_from_closure`

Used in:

- `commit_pause()`

#### `RetrievalPlanProposal`

Purpose:

- specify what to look up, where, and how to decide when enough support exists

Key fields:

- `retrieval_queries`
- `source_classes`
- `retrieval_plan`
- `evidence_expectations`
- `triangulation_plan`
- `stop_conditions`

Used in:

- `commit_pause()` when the control decision says retrieval is needed

#### `CapabilityDraftProposal`

Purpose:

- draft a missing governed capability when support acquisition is blocked

Key fields:

- `capability_kind`
- `semantic_role`
- `affordance`
- `input_form`
- `output_form`
- `limits`
- `sub_capabilities`
- `recommended_tooling_family`

Used in:

- `ensure_generated_capability()`

Important boundary:

- this drafts a capability description
- the controller still performs the actual capability registration

### 7.4 Development and Learning

#### `DiscoveryAuditProposal`

Purpose:

- harvest reusable residue from the run after outcome determination

Key fields:

- `pain_class`
- `gain_class`
- `gain_types`
- `enablers`
- `diagnostics`
- `artifacts`

Used in:

- `perform_discovery_harvest()`
- always attempted during `finalize_run()`

This is the main bridge from LLM supplement output into reusable artifacts.

---

## 8. How the Controller Actually Uses the Supplement Layer

The active LLM integration points in the main control loop are:

1. Root framing:
   - `initialize_root_semantics()` requests `SemanticTargetProposal`.

2. Repeated control and assessment:
   - `ControlDecisionProposal` and `NodeAssessmentProposal` are consulted throughout status, pause, conflict, and commitment checks.

3. Reflection and contemplation:
   - `reflect()` and `contemplate()` generate advisory diagnostics and path comparisons.

4. Decomposition:
   - `decompose_or_refine()` either preserves the current item or creates governed children from `NotDecompositionProposal`.

5. Direct resolution:
   - the root may use `DirectResolutionProposal` or `RealizationWitnessProposal` to produce support-bearing evidence.

6. Reframing:
   - `ReframeProposal` can create a decomposition-scoped sibling replacement.

7. Pause handling:
   - `UncertaintyAssessmentProposal` explains the pause.
   - `RetrievalPlanProposal` supplies external research directions when needed.
   - `CapabilityDraftProposal` can surface missing support-acquisition capabilities.

8. Finalization:
   - `DiscoveryAuditProposal` produces reusable residue.
   - `ExplanationDraft` produces a human-readable trace summary.

This means the supplement layer is not a single "reasoning step". It is a distributed advisory service embedded into multiple controller decisions.

---

## 9. Fallback Behavior

Fallback behavior is a first-class part of the implementation.

If a supplement call fails and policy is not `required`, the controller:

- uses the supplied fallback payload
- still registers a `ProposalObject`
- marks its source as `heuristic`
- records an `llm_fallback` ledger step

This matters because the controller is designed to remain operational without silently changing the theory of authority.

The fallback payloads are conservative by design:

- control fallbacks mirror structural state
- direct-resolution fallbacks refuse to infer answers
- retrieval fallbacks ask for support collection rather than pretend retrieval happened
- discovery fallbacks generate bounded harvest candidates from current run state

---

## 10. Artifact Learning, Reuse, and Persistence

### 10.1 Artifact Types

The controller supports these artifact types:

- `knowledge`
- `ability`
- `capability`
- `duty_template`
- `closure_pattern`
- `rejection_pattern`
- `uncertainty_pattern`
- `composition`
- `evaluation`

All non-`knowledge` artifact types are treated as template-bearing.

### 10.2 Discovery Harvest

`DiscoveryAuditProposal` may propose up to 3 artifact candidates.

The controller normalizes and validates them in `build_artifact_from_payload(...)`.

Important rules:

- rejected artifacts are dropped
- artifacts missing `title`, `scope`, or `justification` are dropped
- template-bearing artifacts with incomplete schema are downgraded to `candidate`
- `knowledge` artifacts carry no template schema

### 10.3 Ability Artifacts

`ability` artifacts are special:

- representation is forced to `python_script`
- the stored script must use inline dependency metadata
- the script is expected to use `argparse`
- stdin is preferred, with optional `--input-json`
- dependencies must include `msgspec` and `orjson`

If the script is missing or does not match the required shape, the controller:

- downgrades admissibility to `candidate`
- generates a default script skeleton

### 10.4 Learned Artifact Context

At controller initialization:

- `ArtifactStore.load_relevant_artifacts(...)` is called for the root semantic unit
- matching prior artifacts are loaded into `state.learned_artifacts`
- these learned artifacts are included in future supplement state slices

The controller also has one exact reuse shortcut:

- if a learned `knowledge` artifact exactly matches the active root question, it can instantiate support directly before asking the LLM for fresh direct resolution

### 10.5 Persistence

Artifact persistence is best-effort and uses a MySQL-compatible store.

Environment variables:

- `STATE_DB_URL`
- `STATE_DB_PORT`
- `STATE_DB_NAME`
- `STATE_DB_USER`
- `STATE_DB_PASSWORD`

Supported Python backends:

- `mysql.connector`
- `pymysql`

Persisted tables:

- `bssc_artifacts`
- `bssc_discovery_audits`

Persistence failure does not overturn the governed run outcome.

---

## 11. CLI Surface

Run a fresh task:

```bash
python main.py run --prompt "..." --llm auto
```

Resume a saved task:

```bash
python main.py resume --state-in run_state.json --llm auto
```

Inspect saved state:

```bash
python main.py inspect --state run_state.json
```

Useful optional flags:

- `--evidence-file`
- `--state-out`
- `--max-steps`

The run summary emitted by `main.py` includes:

- the supplement profile under `llm`
- run outcome
- development pain/gain summary
- artifact ids
- counts of proposals, evidence, capabilities, commitments, artifacts, and audits
- frontier and recent ledger entries

---

## 12. Practical Negative Doctrine

The current implementation does **not** let the LLM do any of the following by itself:

- attach evidence
- admit evidence
- assign final certainty or commit a certainty judgment by itself
- commit closure
- pause the system directly
- register a capability directly
- persist artifacts directly
- override conflicts or blockers
- bypass controller governance

Instead, the LLM can only influence those outcomes indirectly by supplying structured proposal payloads that the controller later interprets under its normal rules. In particular, working support and certainty estimates may be proposal-informed, but closure and commitment remain controller-governed.

That is the implementation-level invariant that keeps the LLM supplement conservative.

---

## 13. Short Version

`main.py` implements the LLM as a typed JSON proposal service with:

- two modes: `fast` and `deep`
- two providers: `openai` and `llamacpp`
- explicit fallback-to-heuristic behavior
- proposal registration plus separate governance
- multiple concrete proposal families wired into framing, control, decomposition, pause, retrieval, reframing, explanation, and artifact harvest
- no direct authority over evidence, certainty, or closure

That is the actual current architecture.
