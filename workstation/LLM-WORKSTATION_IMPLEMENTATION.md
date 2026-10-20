# LLM Workstation Implementation

Vertical-slice tracker for the first workstation implementation.

Scope rule:
- build one end-to-end slice first
- do not implement all permutations yet
- keep workstation logic inside `workstation/`
- do not disturb the outer 6-layer BSSC architecture except for thin CLI entry wiring

## Vertical Slice Target

One real workstation session should support:
- launching a workstation root against one attached workspace
- generating workstation discovery files
- normalizing a user prompt into a boundary-complete task contract
- running one host-owned LLM turn
- running an interactive host-owned chat loop over the same session
- exposing a small workstation capability surface
- recording messages and receipts

## First Slice Capabilities

Initial workstation capability subset:
- `ws.repo.tree`
- `ws.repo.search`
- `ws.fs.read`
- `ws.process.run`

This is enough to prove:
- attachment discovery
- tool mediation
- host-owned LLM driving
- receipt generation

These are first-slice capabilities, not the intended final kernel boundary.

Target direction:
- keep a small workstation capability kernel for primitive host effects
- move higher-level user-facing behaviors toward skills
- add `ws.skill.invoke`
- require explicit delegated rights from workstation to skill invocation

## Status

- [x] workstation spec written in `LLM-WORKSTATION.md`
- [x] boundary-complete prompt model added to the spec
- [x] workstation package scaffolded
- [x] workstation launcher implemented
- [x] boundary-complete task contract implemented
- [x] workstation capability server implemented
- [x] host-owned OpenAI-backed session driver implemented
- [x] CLI commands wired
- [x] workstation tests added
- [x] end-to-end workstation slice validated
- [x] workstation chat REPL implemented
- [x] live OpenAI-backed workstation smoke completed
- [x] workstation spec updated to distinguish kernel capabilities from skills
- [x] workstation spec updated to require explicit delegated rights for skill invocation
- [x] workstation spec updated to distinguish declared authority, invocation-time narrowing, and escalation approval
- [x] add `ws.skill.invoke`
- [x] add workstation skill-store discovery catalog
- [x] add first invocation-time delegated-rights check for workstation skill calls
- [x] make delegated workstation filesystem rights flow into the nested skill runtime as ephemeral governed mounts
- [x] migrate repository search toward a real workstation skill when a skill store is attached
- [x] demonstrate one end-to-end workstation -> skill -> Wasm path
- [x] derive bounded repo-search skill inputs and read delegation from the task semantic unit when the model omits a structured payload
- [x] retry transient OpenAI provider failures in the host-owned workstation driver
- [x] workstation spec updated with persistent workstation skill-home model
- [x] workstation spec updated to treat import/export as first-class workstation skill lifecycle operations
- [x] workstation spec updated to defer skill enhancement for now
- [x] workstation spec updated to prefer direct skill composition over plugging in the controller by default
- [x] make workstation skill-home governance stable for many imported trial bundles by filtering transient bundle-local policies
- [x] recompute current admission/lifecycle for imported workstation workers at invocation time
- [x] add prompt-local direct composition so the shell can prefer one shortlisted trial worker before broader tool use
- [x] make workstation skill resolution tolerant of shortened natural-language titles when there is one unique match
- [x] harden workstation path and attachment normalization for trial-style absolute paths and mount aliases

## Next Workstation Integration Cuts

- [x] promote workstation skill lifecycle operations to first-class CLI commands:
  - `workstation-skill-catalog`
  - `workstation-skill-import`
  - `workstation-skill-export`
- [x] add a standard persistent workstation skill-home resolver and default attachment path
- [x] add `ws.skill.catalog`
- [x] add `ws.skill.import`
- [x] add `ws.skill.export`
- [x] define the workstation kernel capability set explicitly in code
- [x] continue migrating transitional high-level workstation capabilities toward skills beyond repo search
- [x] remove transitional repo tree/search from the default shell capability set while keeping them available as explicit opt-ins
- [x] remove workflow list/get from the default shell capability set and stop auto-granting workflow surfaces on every skill-store session
- [x] add escalation prompts when a skill invocation exceeds the current workstation session grant
- [x] add delegated-rights receipts for workstation-to-skill invocation
- [x] enforce skill-first workstation chat behavior:
  - implicit natural-language asks should prefer a suitable skill family when one exists
  - explicit `use the <skill>` asks should not silently fall back to generic host tools
  - permission insufficiency on the skill path should trigger escalation prompting and continuation
- [x] keep skill enhancement deferred until create/import/export flows are stable and the syntax surface is understood better
- [x] add a separate enhanced workstation chat frontend layer with:
  - ANSI-styled interactive banner/prompt rendering
  - context suggestions
  - tab completion for skills, paths, slash commands, and approval responses
  - safe fallback to the plain non-interactive chat loop
- [x] add direct workstation chat slash commands for deterministic skill lifecycle and skill inspection:
  - `/list-skills`
  - `/describe-skill`
  - `/permissions`
  - `/import-skill`
  - `/export-skill`
- [x] format assistant and shell output in preformatted blocks and preserve multiline rendering in chat
- [x] drive live chat activity from formatted receipts instead of ad hoc transient status strings
- [x] define a shared host interaction substrate that workstation and governed runtime can both consume
- [x] extract the first shared attachment/root helpers below the workstation shell
- [x] extract shared delegated-rights helpers below the workstation shell:
  - requested-delegation normalization
  - escalation splitting
  - ephemeral delegated-mount projection
- [x] extract shared receipt helpers below the workstation shell:
  - canonical receipt log path resolution
  - append-only JSONL event emission
  - shared receipt payload builders for prompt, capability, assistant, and escalation events
- [x] extract the first shared host action helpers below the workstation shell:
  - attachment-scoped repo tree
  - attachment-scoped text read result shaping
  - attachment-scoped process execution
- [x] extract shared non-skill host-action dispatch below the workstation shell:
  - shared capability membership for the current non-skill action surface
  - shared dispatch for tree, search, read, and process actions
  - injected read-resolution seam for workstation discovery-file fallback
- [x] let governed runtime consume that substrate through injection rather than importing workstation code for backend identity and the first child-worker filesystem seam
- [ ] reassess whether controller integration is needed after the shared host interaction substrate exists
- [x] run a workstation-oriented audit across the trial domains and capture the first compatibility report through `workstation-trial-validate`
- [x] use that audit as the acceptance gate across the current portable trial domains
- [x] keep that acceptance gate green across the current portable trial domains while controller-side validators and shared substrate work continue to change
- [x] wire the live `LearningContext` / `Publication` subject workflow into the workstation shells so maintained subject projections, imports, report plans, and report builds are backed by the real corpus rather than the mock-only workflow
- [x] add first URL learning ingress into workstation research with browser-backed capture and source-bundle preservation
- [x] rename the current intake workflow phase/tab from `Research` to `Gather`, while restoring the later approval/sign-off phase to the user-facing `Review` label
- [x] move the workflow phase-status panes to the bottom of each subject tab and give each pane an explicit title; this now applies across `Gather`, `Itemize`, `Draft`, `Review`, and `Publication`
- [x] remove the always-visible journal/workspace panes from the main subject tabs and replace them with an explicit journal-view action that unhides and maximizes the hidden pane on demand
- [x] synchronize preview-pane titles with row selection in supporting panels so up/down navigation updates the companion panel title to the selected item title
- [ ] add governed preview/confirmation before URL admission and keep extending Flutter parity with the deeper Textual subject-workflow interactions
- [x] land the first explicit `Gather <-> Chat` source prompt target:
  - the selected staged source in `Gather` can now seed a source-layer chat curation turn
  - this stays source-only and does not auto-import into corpus
- [x] land the first apply-back path from gather-scoped chat into staged sources:
  - `@llm` now starts pending source curation for the selected staged source
  - `Apply LLM Curation` now writes a new staged `SourceRevision`
  - `Discard LLM Curation` now drops the pending proposal without admitting anything into corpus
- [x] widen explicit `Gather <-> Chat` prompt-target routing for staged source work through the first selected source-set cut:
  - the selected source set in `Gather` can now seed a source-layer chat curation turn
  - the selected source set can now also be curated manually through `=`
  - both paths update `SourceCollection` metadata only and do not auto-import into corpus
- [ ] widen explicit `Gather <-> Chat` prompt-target routing for staged source work beyond the current selected-source and selected-source-set cuts:
  - this is now the second immediate product step, after the broader `Gather` knowledgebase widening lands
  - keep general chat as a broad workstation/skill surface
  - the first selected source-set discovery target is now live:
    - `Find Sources In Chat` seeds a gather-scoped discovery turn from the selected source set's saved query/topic
    - `Apply Discovered Sources` stages newly discovered source records or links existing ones back into that source set
  - widen beyond the current discovery/curation paths into richer apply-back flows and source sync
  - widen from the first selected source-set path into broader topic/query collections and multi-source targets
- [ ] add skill-first source work in gather-scoped chat without weakening non-research chat:
  - prefer source-discovery/source-capture/source-curation skills when available
  - fall back to host/web capability paths when no suitable source skill exists
  - do not let gather-oriented heuristics override unrelated explicit skill requests in general chat

## Notes

- Existing controller, governance, markdown-learning, and skill-runtime machinery remain separate.
- The workstation may reuse host mediation ideas and receipt concepts, but it is not the controller.
- Live OpenAI workstation validation now exists for the builtin Wasm worker and for the repo-search worker receipt path.
- The current planned direction is direct skill composition first; controller integration remains optional and deferred.
- The next convergence move is a shared host interaction substrate, not `runtime -> workstation`.
- The first real shared-runtime seam is now live in host mediation, where child worker `workspace_root` and attachment-backed `virtual_mounts` derive from the injected host backend rather than ambient cwd.
- Workstation delegated-rights normalization and ephemeral mount projection now also run through root-level shared host-interaction helpers instead of workstation-local logic.
- Workstation session and CLI receipt emission now also run through root-level shared host-interaction receipt helpers instead of workstation-local JSONL append logic.
- Workstation capability execution for `ws.repo.tree`, `ws.fs.read`, and `ws.process.run` now runs through root-level shared host-interaction action helpers instead of workstation-local implementations.
- Workstation capability execution for the current non-skill surface now runs through root-level shared host-interaction dispatch:
  - `ws.repo.tree`
  - `ws.repo.search`
  - `ws.fs.read`
  - `ws.process.run`
- The next source-workbench move must keep this rule:
  - `Chat` remains a general surface
  - gather-scoped source work is an explicit prompt-target/workflow mode, not a replacement for general chat

## Validation

- workstation unit slice:
  - `tests/test_workstation.py`
- milestone regressions:
  - `trials/LEARNED_FUNCTION_VALIDATION.py`
  - `TRIAL_DOMAIN_VALIDATION.py --domains chemistry`

Current state:
- workstation vertical slice is green
- outer runtime regression gates remain green
- workstation chat REPL is live through `workstation-chat`
- the current capability set is intentionally transitional
- the spec now records that higher-level workstation behaviors should move toward skills built on a smaller kernel
- workstation can now invoke one installed governed skill from a session-bound skill store through `ws.skill.invoke`
- workstation skill discovery is materialized in `SKILLS.json`
- delegated workstation filesystem rights now flow into the nested skill runtime as invocation-scoped virtual mounts
- when a skill store is attached, repository search migrates from the direct high-level capability toward the builtin repo-search worker skill
- when a skill store is attached, repository tree also migrates from the direct high-level capability toward the builtin repo-tree worker skill by default
- repo tree and repo search no longer live in `DEFAULT_WORKSTATION_CAPABILITIES`; they remain explicit opt-in transitional capabilities
- workflow list/get/run no longer arrive ambiently with every attached skill store; they are explicit opt-in workflow surfaces layered above the smaller shell default
- repo-search skill invocation can now derive bounded search inputs from the task semantic unit when the model omits explicit payload fields
- host-owned workstation prompting now retries bounded transient OpenAI failures instead of failing immediately on the first 5xx
- the first builtin workstation Wasm worker now proves the workstation -> skill -> Wasmtime path
- workstation now attaches a persistent skill home by default under the resolved `WORKSTATION_HOME`
- workstation skill lifecycle operations now exist as first-class kernel capabilities:
  - `ws.skill.catalog`
  - `ws.skill.import`
  - `ws.skill.export`
- workstation skill lifecycle is now promoted to first-class CLI commands:
  - `workstation-skill-catalog`
  - `workstation-skill-import`
  - `workstation-skill-export`
- the workstation kernel capability set is now explicit in code, separate from transitional high-level capabilities
- workstation skill import now stages portable bundles through the persistent imports path, persists them through governed import logic, refreshes `SKILLS.json`, and writes canonical exports into the persistent exports path
- workstation chat can now prompt for one-invocation delegated-rights escalation, record approval or denial receipts, and replay the skill invocation with the approved delegated subset
- capability-call receipts now project workstation-to-skill delegated rights into a stable top-level `delegation` field, including requested, approved, escalated, granted, missing, unsupported, scope, and status data
- workstation skill enhancement is explicitly deferred until the governed skill syntax is handled better
- workstation skill-home governance now ignores transient bundle-local policies so many imported trial bundles can coexist in one persistent workstation skill store
- workstation invocation now recomputes imported worker admission/lifecycle against the current workstation governance snapshot instead of trusting stale import-time state
- workstation direct composition now derives obvious prompt payloads for shortlisted trial workers, including bare `symbol NAME` prompts and path-bearing asks
- workstation skill resolution now accepts one unique shortened natural-language title match instead of requiring the model to reproduce the full canonical stored title
- workstation skill invocation now derives prompt-local payloads for explicit imported-skill requests and closes with bounded failure instead of silent generic fallback when invocation still cannot proceed
- workstation skill invocation now accepts top-level declared worker inputs from model tool calls, not just nested `invocation_payload`
- workstation skill invocation now infers mount-based delegated rights from the normalized worker payload so read skills can proceed directly and write skills surface as approval-required instead of failing inside the nested runtime
- workstation file-skill prompting now derives plain workspace-relative paths like `src/demo.py` for the imported Python read/write family
- workstation skill export now resolves shortened unique titles and can project exports directly into the attached workspace when chat asks for paths like `exports/foo.yaml`
- workstation nested worker answer text, nested effect traces, and nested grant payloads are now bounded before they are persisted into chat history or receipts, so the full trial sweep stays within disk budget even for large search prompts
- workstation trial validation is green again across all current portable domains after the bounded nested-worker artifact changes
- workstation receipt append now normalizes legacy concatenated JSON receipt streams into real JSONL before writing new events
- workstation chat now has a separate enhanced interactive frontend layer for real TTY use:
  - uses `prompt_toolkit` when installed
  - styled startup banner and prompt
  - context suggestions from workspace paths and visible skills
  - tab completion for skill titles, workspace paths, import/export prompts, and yes/no escalation responses
  - unchanged plain fallback path for tests, scripting, and non-interactive streams
- workstation chat now also has direct slash-command utilities for deterministic in-chat workstation operations:
  - `/list-skills`
  - `/describe-skill`
  - `/permissions`
  - `/import-skill`
  - `/export-skill`
- workstation chat now renders assistant output and direct shell-command output in preformatted blocks instead of collapsing multiline text
- workstation chat now shows live formatted activity lines derived from new and existing receipts rather than raw JSON or ad hoc shell-local status strings
- intended UX split:
  - CLI for deterministic lifecycle operations
  - chat for conversational use of the same lifecycle operations
  - direct Python capability calls for tests and internal validation only
- intended workstation chat rule:
  - prefer skills in nearly all cases when a suitable skill exists
  - let permissions constrain that behavior through escalation prompts
  - do not silently replace an explicit skill request with unrelated generic tool use
