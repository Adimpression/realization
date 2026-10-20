## Heuristic Deterministic Scale

This document orders key prompt-matching, scoring, ranking, and grounding paths from the most heuristic to the most deterministic.

Interpretation of `Determinism Impact`:
- `Very Low`: primarily natural-language or lexical guesswork
- `Low`: still language-led, but with some bounded shaping
- `Medium`: mixed heuristic and structural comparison
- `High`: mostly normalized structural comparison
- `Very High`: canonical or reconstructible structure with little or no prompt-surface freedom

The important review question is not only "is this heuristic?" but also "does this heuristic merely propose candidates, or does it directly decide identity, decomposition, or closure?"

### Very Low

1. `semantic_prompt_directive_profile()`
   Location: [prompt_directives.py:80](prompt_directives.py#L80)
   Determinism Impact: `Very Low`
   Why: regex-based interpretation of prompt form such as `state`, `derive`, `construct`, `distinguish`, and split-result phrasing.
   Review note: this is a prompt-surface classifier, not a structural proof.

2. `_normalize_directive_focus()`
   Location: [prompt_directives.py:35](prompt_directives.py#L35)
   Determinism Impact: `Very Low`
   Why: strips prompt scaffolding like "the relation that describes..." or "the full ... pathway from..." using surface patterns.
   Review note: useful for retrieval focus, but not safe as a sole identity-grounding source.

3. `semantic_prompt_action_posture()`
   Location: [semantic_prompt_posture.py:14](semantic_prompt_posture.py#L14)
   Determinism Impact: `Very Low`
   Why: routes prompts into broad postures like `direct_resolution`, `compute_or_template`, `next_step_guidance`, and `clarify_before_acting` using regexes and prompt markers.
   Review note: posture is useful policy input, but still natural-language classification.

4. `semantic_requested_output_keys()`
   Location: [semantic_text.py:389](semantic_text.py#L389)
   Determinism Impact: `Very Low`
   Why: derives output quantities from phrases like "calculate X" or "give me X and Y separately".
   Review note: this is bounded extraction, but still prompt-surface dependent.

5. `semantic_requested_output_phrases()`
   Location: [semantic_text.py:427](semantic_text.py#L427)
   Determinism Impact: `Very Low`
   Why: preserves raw requested phrases before later lookup/normalization.
   Review note: especially risky when later grounding discards the governing object and keeps only leaf phrases.

6. `selection_signal_tokens()` and `selection_signal_phrases()`
   Location: [retrieval_ranking.py:230](retrieval_ranking.py#L230), [retrieval_ranking.py:256](retrieval_ranking.py#L256)
   Determinism Impact: `Very Low`
   Why: token and n-gram extraction for lightweight lexical alignment.
   Review note: best treated as candidate-generation or tie-break support, not as closure evidence.

7. `artifact_selection_text()`
   Location: [retrieval_ranking.py:319](retrieval_ranking.py#L319)
   Determinism Impact: `Very Low`
   Why: concatenates title, question, answer, aliases, scope, and constraints into one ranking surface.
   Review note: useful for loose retrieval; dangerous if later structural distinctions are not strong enough to override it.

8. `artifact_focus_alignment_score()`
   Location: [retrieval_ranking.py:448](retrieval_ranking.py#L448)
   Determinism Impact: `Very Low`
   Why: uses lexical containment, lookup keys, and token overlap to decide whether an artifact is "about" a focus.
   Review note: this is a classic heuristic alignment score, not a title-depth or boundary proof.

9. `artifact_prompt_decision_mismatch_penalty()`
   Location: [retrieval_ranking.py:503](retrieval_ranking.py#L503)
   Determinism Impact: `Very Low`
   Why: checks prompt/answer safety posture through phrase markers like uncertainty, emergency guidance, hold guidance, and affirmative action.
   Review note: policy-helpful, but entirely surface-led.

10. `best_reusable_title_for_phrase()`
    Location: [main.py:3370](main.py#L3370)
    Determinism Impact: `Very Low`
    Why: scores reusable titles against prompt-local output phrases and context tokens.
    Review note: this is still natural-language ranking, even though it operates over prior artifacts.

### Low

11. `artifact_action_alignment_penalty()`
    Location: [retrieval_ranking.py:199](retrieval_ranking.py#L199)
    Determinism Impact: `Low`
    Why: compares prompt action families against artifact action families using canonical action buckets like `read`, `write`, `move`, `list`.
    Review note: more bounded than free text overlap, but still inferred from language markers.

12. `answer_candidate_rank()`
    Location: [main.py:5317](main.py#L5317)
    Determinism Impact: `Low`
    Why: this is the master policy tuple that mixes heuristic penalties and structural ranks.
    Review note: tuple position is policy. Earlier heuristic penalties can dominate later deterministic checks.

13. `shared_reusable_family_title()`
    Location: [main.py:3315](main.py#L3315)
    Determinism Impact: `Low`
    Why: begins from normalized title segments, but still performs heuristic family lifting when only one common segment remains.
    Current finding: if multiple namespaces share the same terminal family segment, this can lift the root into the wrong family. Review the one-segment branch at [main.py:3351](main.py#L3351).

14. `refine_structured_learning_from_reuse()`
    Location: [main.py:3423](main.py#L3423)
    Determinism Impact: `Low`
    Why: combines requested-output phrase extraction, title matching, split-result detection, and then writes back `title_identity` and `component_nots`.
    Review note: this is the most important mixed seam because heuristic matching can directly alter identity and decomposition payloads.

### Medium

15. `not_elaboration_alignment_rank()`
    Location: [fallback_not_semantics.py:454](fallback_not_semantics.py#L454)
    Determinism Impact: `Medium`
    Why: computes a deterministic tuple, but its inputs come from fallback structured-learning views, lookup keys, posture labels, and repair/misalignment fields that still originate partly from heuristic text interpretation.
    Review note: structurally ordered, but not purely structural.

16. `semantic_prompt_prefers_direct_knowledge_answer()`
    Location: [semantic_prompt_posture.py:60](semantic_prompt_posture.py#L60)
    Determinism Impact: `Medium`
    Why: not a raw regex-only function; it composes directive profile, named-input detection, posture, and focus presence into a higher-level routing decision.
    Review note: still heuristic, but more policy-shaped than the raw classifiers above.

17. `artifact_output_lookup_keys()`
    Location: [retrieval_ranking.py:381](retrieval_ranking.py#L381)
    Determinism Impact: `Medium`
    Why: partly structural from output contracts and output fields, partly heuristic from titles and questions.
    Review note: useful example of a mixed path where contract data and language cues are intentionally fused.

### High

18. `normalize_semantic_title_identity()`
    Location: [title_semantics.py:248](title_semantics.py#L248)
    Determinism Impact: `High`
    Why: canonicalizes semantic titles into stable slash or Prolog forms.
    Review note: this is a normalization function, not a matcher.

19. `derive_semantic_title_depth_segments()`
    Location: [title_semantics.py:280](title_semantics.py#L280)
    Determinism Impact: `High`
    Why: deterministically exposes title-depth segments from a normalized identity.
    Review note: once the title identity is fixed, segmentation is stable.

20. `classify_title_depth_relation()`
    Location: [title_semantics.py:611](title_semantics.py#L611)
    Determinism Impact: `High`
    Why: compares normalized prefix chains and returns stable relations like `same_identity`, `prior_is_ground_prefix`, and `shared_ground_prefix`.
    Review note: this is one of the clearest theory-faithful title-depth comparators in the repo.

21. `boundary_shape_rank()`
    Location: [boundary.py:483](boundary.py#L483)
    Determinism Impact: `High`
    Why: compares declared boundary terms directly rather than reading prompt language.
    Review note: a strong example of structural ranking that should usually outrank loose lexical fit.

### Very High

22. `normalize_skill_region_body()`
    Location: [skill_boundary_normalization.py:71](skill_boundary_normalization.py#L71)
    Determinism Impact: `Very High`
    Why: canonical flattening of region bodies into typed path-ledger leaves.
    Review note: this is the kind of path the repo is aiming toward when it wants composition to be law-like rather than prompt-like.

23. `reconstruct_skill_region_body()`
    Location: [skill_boundary_normalization.py:123](skill_boundary_normalization.py#L123)
    Determinism Impact: `Very High`
    Why: reconstructs structured bodies from canonical leaves with explicit incompatibility failures.
    Review note: this is close to maximally deterministic in the current system.

### Review Use

When reviewing a new path, classify it with these questions:

1. Does it depend on regexes, token overlap, phrase overlap, or title/question wording?
   If yes, it belongs near the top of this scale.

2. Does it compare normalized identities, boundary shapes, or canonical leaf ledgers?
   If yes, it belongs near the bottom of this scale.

3. Does it merely propose candidates, or does it directly set:
   - `title_identity`
   - `component_nots`
   - `closure_ready`
   - `ready_for_commitment`

If a top-of-scale heuristic directly sets those fields, it deserves extra scrutiny.
