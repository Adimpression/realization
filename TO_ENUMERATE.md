# Natural Language Matching Inventory

## Purpose

This document inventories the production Python modules where freeform natural-language surfaces are matched directly in order to drive routing, skill selection, payload derivation, planner control flow, knowledge ranking, or UI behavior.

These are the places where the current codebase is still relying on:

- English verbs and phrases
- human-readable skill titles
- field-name substrings
- prompt-local wording conventions

In the highest-priority cases, those matches should be replaced by declared identifiers, enumerations, or typed metadata. In the lower-priority cases, natural-language parsing is legitimate, but the parser outputs should still become typed enums or structured roles instead of remaining stringly typed.

## Scope

Included:

- production modules in the repository root
- production modules under `workstation/`

Excluded:

- tests
- trial and validation helpers
- generated report copies
- third-party packages under `venv/`
- pure syntax parsing that does not materially drive runtime routing or semantic behavior

## Reading Rule

For each file below:

- `P0` means the file is using natural-language matching in a control-flow path where enums, ids, or declared metadata should replace the match.
- `P1` means the file is an intentional semantic parser, but its outputs should still become typed enums or structured roles.
- `P2` means the file contains smaller UI or compatibility heuristics that should eventually move to metadata, but are not the core architectural risk.

## P0: Highest-Priority Enum / Identifier Replacements

### `workstation/task_contract.py`

- `workstation/task_contract.py:15-35`
  - `_OUTPUT_HINTS` and `_SIDE_EFFECT_HINTS` map words like `summarize`, `describe`, `browser`, `download`, `write`, and `launch` onto normalized task outputs and side effects.
  - This should become declared task-output and side-effect enums rather than word-list matching.
- `workstation/task_contract.py:67-137`
  - `normalize_prompt_to_task_boundary_contract()` infers `read_references`, `write_targets`, `output_values`, `side_effects`, and `completion_conditions` from prompt wording such as `browser`, `download`, `file`, `workspace`, `summarize`, `explain`, and `describe`.
  - This is stringly-typed task-contract synthesis. It should converge on typed task-intent and effect enums.

### `workstation/shell_prompt_routing.py`

- `workstation/shell_prompt_routing.py:9-58`
  - `match_workstation_shell_utility_prompt()` recognizes full English command surfaces such as `import the skill file at ... into this workstation` and `export the skill titled ... to ...`.
  - These routes should be backed by a formal shell-intent enum and structured command grammar, not fixed phrase-prefix matching.

### `workstation/direct_composition.py`

- `workstation/direct_composition.py:34-88`
  - `_mount_candidates_from_prompt()` and `_number_candidates_from_prompt()` extract mounts and numeric values from freeform prompts.
  - These are acceptable as parsers, but they should feed typed input roles rather than ad hoc name-matching downstream.
- `workstation/direct_composition.py:91-123`
  - `_browser_name_from_prompt()` matches a fixed list of browser names from the prompt.
  - This should resolve to a typed application enum or declared application id set.
- `workstation/direct_composition.py:126-153`
  - `prompt_explicitly_requests_skill()` decides whether a user explicitly requested a skill based on English verbs like `use`, `invoke`, and `run`.
  - This should produce a typed prompt-intent enum instead of a bare boolean derived from one regex.
- `workstation/direct_composition.py:156-375`
  - `_skill_action_bonus()` and `_skill_action_penalty()` rerank skills by matching prompt tokens and human-readable skill-title tokens such as `copy`, `move`, `download`, `json`, `csv`, `template`, `screenshot`, and many title substrings like `write text file` or `launch browser at specific url`.
  - This is one of the main stringly-typed routing surfaces in the workstation. It should move to declared `SkillAction`, `SkillFamily`, and capability tags on skills.
- `workstation/direct_composition.py:410-734`
  - `_value_for_worker_name()` derives payload fields from both prompt wording and raw input names such as `source_mount`, `destination_mount`, `root`, `symbol`, `module`, `query`, `table`, `status_field`, `token`, `api_key`, and `max_tokens`.
  - This should be driven by declared input-role enums or canonical input semantics, not field-name substrings and prompt phrasing.
- `workstation/direct_composition.py:737-848`
  - `_derive_payload_execution_input()` switches on human-readable skill-title substrings like `launch browser at specific url`, `open system settings pane`, `capture screenshot to file`, `write text file`, and `append text file`.
  - This should be replaced by explicit skill-family or operation enums in skill metadata.
- `workstation/direct_composition.py:879-1067`
  - `_derive_workstation_invocation_payload_from_prompt()` merges literal extraction, title-derived payload inference, and input-name heuristics to build invocation payloads.
  - This entire path is currently stringly typed and should be re-based on typed input roles.
- `workstation/direct_composition.py:1137-1185`
  - `preferred_workstation_skill_invocation_plan()` depends on the natural-language scoring above to choose a direct skill.
  - This should eventually score primarily from typed skill metadata, with prompt parsing only filling structured fields.

### `workstation/skill_composition_planning.py`

- `workstation/skill_composition_planning.py:26-35`
  - `_PIPELINE_PATTERN`, `_PIPELINE_SPLIT_PATTERN`, and `_PIPELINE_ACTIONS` encode English pipeline phrases like `and then`, `after that`, `using the output`, and action verbs like `read`, `write`, `render`, `extract`, `download`.
  - These should become typed planner control markers and action enums.
- `workstation/skill_composition_planning.py:58-107`
  - `_PLANNER_ACTION_SYNONYMS`, `_prompt_implies_skill_pipeline()`, `_planner_primary_action()`, and `_planner_clause_skill_bonus()` convert prompt words into planner action classes.
  - This is a core composition-planning surface and should be typed explicitly.
- `workstation/skill_composition_planning.py:110-135`
  - `_split_prompt_pipeline_clauses()` infers step boundaries from English conjunctions and verb presence.
  - Clause segmentation should survive as parsing, but the resulting clause kinds should become typed planner objects.
- `workstation/skill_composition_planning.py:340-423`
  - `_split_clause_condition()`, `_split_clause_iteration()`, and `_split_clause_else_branch()` parse English control forms like `if ... exists`, `until ... equals`, and `otherwise`.
  - These should become formal planner control enums such as condition operators and branch kinds.
- `workstation/skill_composition_planning.py:450-491`
  - `_resolved_candidates_for_clause()` keeps clause-to-skill selection dependent on clause text and title-based skill scoring.
  - Candidate selection should be driven by operator or capability ids rather than title words.
- `workstation/skill_composition_planning.py:826-923`
  - `preferred_workstation_skill_composition_plan()` depends on the natural-language pipeline detection and clause parsing above.
  - This is a primary location where prompt wording still determines workflow structure.

### `workstation/skill_invocation.py`

- `workstation/skill_invocation.py:30-50`
  - `_normalized_skill_title_key()` normalizes human-readable titles for fuzzy resolution.
  - Stable skill ids or slugs should replace title-based matching.
- `workstation/skill_invocation.py:164-229`
  - `resolve_workstation_skill()` falls back from exact title matching to normalized-title and prefix-title matching.
  - This is a major enum/id migration target. Invocation should resolve by canonical skill identifier, not by display title.
- `workstation/skill_invocation.py:261-287`
  - `_required_skill_input_names()` infers requiredness by searching for the word `required` in input descriptions.
  - Requiredness should be structured schema metadata, never text-description parsing.

### `workstation/skill_management.py`

- `workstation/skill_management.py:91-120`
  - `_skill_semantic_bonus()` boosts scores using prompt tokens and skill-title phrases like `browser`, `settings pane`, `clipboard`, `screenshot`, and `search the web`.
  - This should be replaced by declared skill categories and capability tags.
- `workstation/skill_management.py:165-179`
  - `workstation_skill_catalog_payload()` filters by token presence over title/kind/framework/source text.
  - Query behavior is acceptable, but the searchable facets should be structured fields, not only string haystacks.
- `workstation/skill_management.py:255-295`
  - `workstation_prompt_skill_shortlist_payload()` ranks skills by token overlap and title substrings like `repo search`, `find`, `search`, `symbol`, `implemented`.
  - This is one of the main skill-discovery heuristics that should move to typed metadata and ids.

### `workstation/capabilities.py`

- `workstation/capabilities.py:309-372`
  - `_heuristic_repo_search_pattern()` derives search patterns from English prompt forms like `find where ... is implemented` or `search for ... in this workspace`.
  - This is a fallback parser. It should be bounded behind a typed repo-search intent rather than special-case phrase matching.
- `workstation/capabilities.py:532-543`
  - Delegation and mutation detection special-case the title substring `move file`.
  - Mutation semantics should come from declared operation metadata, not title text.
- `workstation/capabilities.py:2478-2489`
  - `_skill_invoke()` special-cases builtin behavior when `skill_title == "Workstation Repo Search"`.
  - This should be an explicit builtin skill id, not a title comparison.

### `workstation/workstation_core.py`

- `workstation/workstation_core.py:720-733`
  - `_field_widget_hint()` derives widget type from field-name substrings like `path`, `file`, `directory`, and `url`.
  - Widget hints should live in explicit field metadata or enums.
- `workstation/workstation_core.py:760-800`
  - `_field_constraints()` infers `path_like`, `secret_like`, and other constraints from field-name substrings such as `relative_path`, `token`, `password`, `secret`, and `key`.
  - These should be declared in the interface schema.
- `workstation/workstation_core.py:803-855`
  - `_field_section()` and `_field_placeholder()` decide UI grouping and placeholder text from names like `mount`, `method`, `header`, `query`, `json`, `csv`, `text`, `symbol`, and `pattern`.
  - This should be explicit UI/schema metadata rather than field-name matching.

### `main.py`

- `main.py:2580-2692`
  - Invocation payload filling matches contract key names like `source_mount`, `destination_mount`, `relative_path`, `suffix`, `text`, `query`, `url`, `browser`, and `application` against prompt-derived literals.
  - This is a root-level controller hotspot. It should migrate to canonical input-role enums and typed contract semantics.
- `main.py:4798-4825`
  - Knowledge-reuse penalty scoring inspects phrases like `example`, `summary`, `relation`, `how do you calculate`, and `from <focus> ... to`.
  - This should consume typed knowledge-directive classifications rather than repeatedly matching English substrings.

## P1: Intentional Semantic Parsers That Still Need Typed Outputs

### `semantic_prompt_posture.py`

- `semantic_prompt_posture.py:14-57`
  - `semantic_prompt_action_posture()` classifies prompts using verbs such as `write`, `append`, `copy`, `move`, `delete`, `open`, `launch`, `download`, `calculate`, `compute`, `find`, and guidance phrases like `what should` or `should i`.
  - Natural-language parsing is valid here, but the output should be a formal posture enum, not ad hoc string values.
- `semantic_prompt_posture.py:100-130`
  - `semantic_unit_allows_default_invocation_payload()` uses prompt phrases like `calculate`, `compute`, `what is`, `explain`, `define`, and `summarize`.
  - This should depend on a typed prompt-posture classification surface.

### `prompt_directives.py`

- `prompt_directives.py:35-266`
  - `semantic_prompt_directive_profile()` uses English forms such as `state`, `write`, `construct`, `derive`, `distinguish`, `difference between`, `identify the reusable substrate`, `explain`, and `describe` to determine directive kind.
  - This is a legitimate parser, but the directive kind and requirement flags should be formal enums rather than plain strings.
- `prompt_directives.py:269-301`
  - `semantic_question_focus_text()` extracts focus phrases from forms like `what is`, `what are`, `define`, `explain`, `describe`, and `summarize`.
  - The parsing is legitimate; the extracted result should feed typed directive structures.
- `prompt_directives.py:304-369`
  - Uncertainty, confirmation, and absence signals come from textual markers and alternative wording.
  - These should converge on explicit signal enums.
- `prompt_directives.py:372-416`
  - `prompt_directive_support_markers()` maps directive kinds to textual support-marker families.
  - This is effectively an enum table already, but the `kind` surface should become a true enum.

### `semantic_text.py`

- `semantic_text.py:346-424`
  - `semantic_named_input_keys()`, `semantic_requested_output_keys()`, and `semantic_requested_output_phrases()` parse prompts for named inputs and requested outputs using forms like `calculate`, `compute`, `find`, `solve`, `what is`, and `... is ...`.
  - Freeform parsing is correct here, but the outputs should map into typed literal and role categories.
- `semantic_text.py:463-771`
  - URL literals, backticked literals, mount mentions, source/destination mounts, relative paths, suffixes, and application mentions are extracted from prompt text and fixed application-name sets.
  - This module should remain a parser, but the destinations should be typed as `SemanticLiteralKind`, input-role ids, or application ids rather than loose strings.

### `retrieval_ranking.py`

- `retrieval_ranking.py:62-79`
  - `primary_action_surface_marker()` maps English request surfaces and polite prefixes to canonical actions.
  - This is close to a real enum boundary already; the returned action should become a formal action enum.
- `retrieval_ranking.py:146-171`
  - `action_surface_markers()` extracts action families from prompt text through marker dictionaries.
  - The canonical action family should be typed.
- `retrieval_ranking.py:256-291`
  - `ordinal_focus_markers()` maps `first`, `1st`, `second`, `2nd`, and similar ordinal variants.
  - This should return an ordinal enum rather than raw strings.

### `fallback_not_semantics.py`

- `fallback_not_semantics.py:102-173`
  - The fallback non-achievedness builder looks for givens, uncertainty, guidance questions, confirmation, absence, and condition wording using English phrases like `i have`, `there is`, `what should`, `should i`, and `if`.
  - This parser is legitimate, but it should consume typed prompt-signal enums instead of re-matching phrase surfaces independently.
- `fallback_not_semantics.py:201-300`
  - Success criteria and misalignment construction depend on prompt wording and directive-kind strings.
  - The directive-kind and signal surfaces should be formal enums.

### `governed_prior_learning_reuse.py`

- `governed_prior_learning_reuse.py:257-340`
  - Query-variant expansion depends on directive kinds and English patterns like `formula that relates ... to ...` and `derive ... compute ... from ...`.
  - This should be built from typed directive and relation-shape classifications rather than raw regex reuse.

### `direct_knowledge_reuse.py`

- `direct_knowledge_reuse.py:108-126`
  - Direct-knowledge answer composition branches on directive-kind strings such as `derive`, `construct`, `distinguish`, and `identify_reusable_substrate`.
  - These should be true directive enums.
- `direct_knowledge_reuse.py:163-166`
  - Primary and secondary marker matches are string-based support signals.
  - This should depend on typed support-marker families.
- `direct_knowledge_reuse.py:240-330`
  - Distinguish, derive, construct, and substrate behavior uses textual markers like `therefore`, `thus`, `then`, `next`, `using`, `from`, and `substrate`.
  - The parser is valid, but the control branching should be typed.

## P2: Lower-Priority UI / Compatibility Heuristics

### `execution_frameworks.py`

- `execution_frameworks.py:448-490`
  - `normalize_ability_runtime_content()` special-cases screenshot behavior if the title contains `screenshot` and the shell script contains `screencapture`.
  - This should be driven by explicit executor capability metadata and broker declarations, not title/script text inspection.

### `workstation/chat_ui.py`

- `workstation/chat_ui.py:622-647`
  - Suggestion generation looks for skill-title substrings like `Python Commands 02` and `Python Commands 03`.
  - Suggestions should target skill ids or capability families, not display-title fragments.
- `workstation/chat_ui.py:675-720`
  - Completion logic recognizes yes/no text, slash command prefixes, and title-prefix matching for command arguments.
  - Slash command completion is acceptable, but title completion should eventually use stable skill ids or indexed catalog metadata.

## What This Inventory Implies

The dominant problems are not in one place. They repeat across four layers:

- prompt classification
- skill discovery and invocation
- composition planning
- UI/schema projection

The strongest recurring migration targets are:

1. Stable skill identifiers instead of title matching.
2. Declared `SkillAction` / `SkillFamily` / capability tags instead of prompt-token versus title-token reranking.
3. Declared input-role metadata instead of field-name substring heuristics.
4. Formal prompt directive and posture enums instead of plain-string classifier outputs.
5. Explicit UI field metadata instead of deriving widget, section, and placeholder behavior from names.

## Immediate Refactor Targets

If this is going to be cleaned incrementally, the best first cuts are:

1. `workstation/skill_invocation.py`
   - introduce stable skill ids and stop resolving by display title.
2. `workstation/direct_composition.py`
   - replace title-substring routing with declared skill-family and input-role metadata.
3. `workstation/skill_composition_planning.py`
   - formalize planner action, control, and condition enums.
4. `workstation/workstation_core.py`
   - move field widget/section/placeholder behavior into explicit schema metadata.
5. `prompt_directives.py` and `semantic_prompt_posture.py`
   - turn current classifier outputs into formal enums and have downstream code depend on those enums instead of re-matching prompt text.
