# Heuristic Deterministic Scale Implementation

Execution tracker for applying [HEURISTIC_DETERMINISTIC_SCALE.md](HEURISTIC_DETERMINISTIC_SCALE.md) to controller work.

## Goal

Prevent local prompt-matching or ranking tweaks from silently dragging the controller away from earlier fixed behavior.

The failure mode to avoid is:
- a new failing prompt appears
- a shared heuristic is nudged until that prompt passes
- older behavior drifts
- the drift is only discovered later in a broader validator

## Operating Rule

When a controller path changes, classify the change first:

1. deterministic structural change
- boundary-shape, title-depth, canonical identity, canonical reconstruction

2. bounded ranking rule
- explicit policy ordering over already-admitted candidates

3. heuristic lexical fallback
- regexes, token overlap, phrase overlap, prompt-surface focus shaping

Required policy:
- prefer `deterministic structural change` first
- use `bounded ranking rule` only when structure is insufficient
- treat `heuristic lexical fallback` as the last resort

## Anti-Drift Mechanism

Every real controller regression should produce a replay sentinel.

See also:
- [CORE_RUNTIME_DETERMINISM_AND_REPLAY_IMPLEMENTATION_PLAN.md](CORE_RUNTIME_DETERMINISM_AND_REPLAY_IMPLEMENTATION_PLAN.md) for the concrete plan to turn replay sentinels into deterministic-mode decision-flow signatures and transcript-backed replays.

A replay sentinel must record:
- prompt
- relevant learned/store context
- expected controller decision

The expected decision should prefer controller-state assertions over prose assertions:
- selected artifact id or title
- match kind
- answer reuse preference
- whether decomposition happened
- whether support remained support-only
- whether direct resolution became commitment-ready

Do not rely only on final answer wording when a more structural controller decision is available.

## Required Validation Order

For a controller fix:

1. add or update the replay sentinel for the real failure
2. rerun the same-seam historical replay pack
3. rerun the affected broader validator

Do not skip directly from a local heuristic tweak to a broad validator rerun.

## Replay Pack Direction

The controller should gain a dedicated drift pack for historically unstable seams, including:
- cross-family direct-knowledge contamination
- title-depth split-result grounding
- support-only residue staying non-closing
- decomposition-required prompts staying decomposed in `llm off`
- skill-first workstation routing not silently falling back to generic tools

## Heuristic Upgrade Direction

The current heuristic layer is not weak because it is handwritten.
It is weak when it is asked to do two jobs at once:
- broad candidate recovery from messy language
- identity or closure decisions that should belong to deterministic structure

The useful direction is therefore not "replace heuristics with AI".
It is:
- strengthen heuristic candidate generation
- narrow heuristic authority
- let deterministic structure decide later

This suggests a staged upgrade path.

### 1. Improve retrieval before improving judgment

The first likely gain is in shortlist quality, not in deeper reasoning.

Several current functions are carrying lexical-retrieval responsibility:
- [selection_signal_tokens() in `retrieval_ranking.py`](retrieval_ranking.py#L230)
- [artifact_focus_alignment_score() in `retrieval_ranking.py`](retrieval_ranking.py#L448)
- [text_alignment_rank() in `retrieval_ranking.py`](retrieval_ranking.py#L549)
- [best_reusable_title_for_phrase() in `main.py`](main.py#L3578)

These are good places to think in terms of:
- a lexical shortlist engine
- followed by bounded reranking
- followed by deterministic adjudication

The insight here is that better shortlist quality may remove pressure to keep nudging downstream controller heuristics.

### 2. Treat SQLite FTS as the likely first improvement, not as a grand rewrite

The repo already treats SQLite as durable infrastructure.
That makes FTS a natural candidate for the "broad lexical recovery" role.

The right use would be:
- phrase and token recovery
- prefix recovery
- stable top-K shortlist generation

The important restraint is:
- do not treat FTS hits as identity
- do not let FTS rank directly set `title_identity`, `component_nots`, `closure_ready`, or commitment

The more useful mental model is:
- FTS proposes
- controller ranking narrows
- deterministic structure decides

This would likely reduce pressure on token-overlap heuristics without changing theory-bearing decision points.

### 3. Use fuzzy matching only as bounded lexical repair

If typo tolerance or alias looseness is the problem, a fuzzy layer can help.
But it is best thought of as a lexical repair mechanism, not a semantic reasoner.

That suggests a role such as:
- rescue near-miss titles from a lexical shortlist
- stabilize minor wording drift in title or alias lookup
- avoid widening controller heuristics that currently compensate for spelling or formatting noise

The key discipline is:
- fuzzy rank should help recover candidates
- it should not outrank deterministic boundary or title-depth evidence later

In other words, it is probably more valuable in [best_reusable_title_for_phrase() in `main.py`](main.py#L3578) than in [answer_candidate_rank() in `main.py`](main.py#L5317).

### 4. Introduce domain lexicons where language is governed, not everywhere

Some prompt surfaces are open-ended language.
Some are actually controlled terminology hiding inside ordinary prose.

Where the repo already has governed or repeated vocabulary, it may be more fruitful to introduce a lexicon-oriented layer than to keep expanding regexes.

Promising cases are:
- subject names
- relation names
- known families
- policy terms
- executor/action vocabulary
- domain aliases that should match on token boundaries

The insight here is:
- use lexical tools when vocabulary is open
- use rule or lexicon tools when vocabulary is governed

That keeps the system from over-learning broad prompt-surface heuristics in places where the real issue is controlled naming.

### 5. Reserve semantic embeddings for fallback, not for authority

If recall remains poor after lexical shortlist and bounded fuzzy recovery, semantic retrieval may help.
But it is most appropriate as:
- a fallback over already narrowed candidates
- a proposal aid for paraphrase-heavy prompts
- a recovery tool for long-form natural language

It is least appropriate as:
- direct identity grounding
- direct decomposition generation
- closure evidence

This is especially important for the seams already called out in [HEURISTIC_DETERMINISTIC_SCALE.md](HEURISTIC_DETERMINISTIC_SCALE.md):
- [shared_reusable_family_title() in `main.py`](main.py#L3315)
- [refine_structured_learning_from_reuse() in `main.py`](main.py#L3423)

If embeddings are used there at all, they should only help generate candidates that are then subjected to stronger structural checks.

### 6. Shift heuristics upward, not downward

The healthy direction is to move heuristics earlier in the pipeline:
- candidate generation
- shortlist ranking
- ambiguity surfacing

And move deterministic machinery later:
- title-depth relation checks
- boundary-shape comparison
- canonical reconstruction

The unhealthy direction is the opposite:
- lexical signals flowing directly into identity
- phrase overlap flowing directly into decomposition structure
- heuristic alignment becoming closure evidence

The practical design question for each change should be:
- "Can this improvement live entirely before deterministic adjudication?"

If yes, it is usually lower risk.

### 7. Prefer seam-specific improvements over global heuristic nudges

The repo has multiple distinct heuristic seams:
- prompt posture
- phrase extraction
- title lookup
- artifact retrieval
- action-family alignment

A broad tweak to shared token logic can easily improve one seam while degrading another.

So when introducing a new tool or approach, the more useful framing is:
- which seam is actually underperforming?
- is the issue recall, ranking, ambiguity handling, or structural overreach?

This should reduce the pattern where one failing prompt causes a shared lexical function to become more permissive everywhere.

### 8. Couple upgrades to replay sentinels, not only to benchmarks

If an improved heuristic tool is introduced, it should not be evaluated only by:
- "did the target prompt pass?"
- "did top-1 improve?"

It should also be evaluated against the drift risks already identified here:
- cross-family contamination
- wrong family lift
- support-only reuse becoming closure
- decomposition-required prompts collapsing back to preserve-parent behavior

The strongest implementation habit would be:
- every heuristic upgrade names the seam it is trying to help
- every heuristic upgrade adds or updates replay sentinels for the historically unstable neighboring seams

### 9. Practical candidate ordering

If the implementer decides to try open-source help, the likely order of usefulness is:

1. SQLite FTS or equivalent lexical shortlist support
- because it fits the current store and improves recall/efficiency without changing theory

2. bounded fuzzy string reranking
- because it repairs lexical brittleness without claiming semantic understanding

3. domain lexicon / phrase matcher support
- because some of the current "natural language" is actually governed terminology

4. semantic embedding reranking over a small shortlist
- because it is helpful, but easiest to over-authorize

This is a suggestion about architectural fit, not a mandate about libraries.

## Status

- [ ] create a dedicated controller drift replay pack
- [ ] convert existing real regressions into replay sentinels with decision-level assertions
- [ ] require same-seam replay reruns before broad validator reruns for heuristic-sensitive changes
- [ ] document which controller files are currently most heuristic-sensitive
- [ ] identify which heuristic seams are primarily retrieval problems versus identity/closure overreach problems
- [ ] prototype shortlist-first retrieval improvements without changing deterministic adjudication
- [ ] evaluate lexical, fuzzy, or semantic helper tools only at candidate-generation or rerank seams first
