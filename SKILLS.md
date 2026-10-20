# Skills

## Purpose

This document defines the product model and implementation plan for skills in BSSC.

The goal is not just to support importable executable artifacts. The goal is to make skills:

- reusable
- governable
- composable
- community-compatible
- intuitive in chat, CLI, and runtime use
- safe enough to host and share

This document assumes the current architecture and interfaces described in:

- [THEORY.md](THEORY.md)
- [SKILL_INTERFACE.md](SKILL_INTERFACE.md)
- [workstation/LLM-WORKSTATION.md](workstation/LLM-WORKSTATION.md)
- [6-LAYER_ARCHITECTURE.md](6-LAYER_ARCHITECTURE.md)

## Current State

The current system already has important foundations:

- governed skill import and export
- a portable skill schema with `bssc_skill.v1` and `bssc_skill.v2`
- declaration-first governance in v2
- executor support for `wasm_wasi`, `python3`, `bash`, and `ansible`
- workstation skill catalog, import, export, and invoke
- session-scoped permissions and invocation-time delegation
- receipts, replay, and skill home persistence

This is a strong substrate, but it is still incomplete as a general skill platform.

The main gaps are:

- the system still mixes multiple notions of “skill”
  - Codex-style `SKILL.md` instruction skills
  - governed executable skills
  - ad hoc reusable workstation capabilities
- the learning path for third-party skills is not yet explicit
- community formats are not first-class ingestion inputs
- composition is still mostly implicit
- permission semantics are split across declaration, session grant, and invocation grant, but the product surface is not yet fully intuitive
- only `wasm_wasi` is strongly sandboxed today
- `python3` and `bash` skills are governed but still host-backed

## Theoretical Grounding

Section 4.6 of [THEORY.md](THEORY.md) adds the missing formal layer for skills.

Boundary classes alone are not enough.

It is not sufficient to know that a skill:

- accepts values vs references
- reads vs writes
- emits values vs references

Composition cannot become mechanical until each interaction body is reduced into a canonical enumerable field space.

The key transformation is:

`semantic body -> typed path ledger`

That means the real skill object is not just a declaration plus an executor. It is also a boundary-normalized interaction form over the eight regions:

- `a`
  - input values
- `a'`
  - input references
- `b`
  - read values
- `b'`
  - read references
- `c`
  - write values
- `c'`
  - write references
- `d`
  - output values
- `d'`
  - output references

Each structured region body should flatten into a finite set of leaves:

`x -> {(p_i, t_i, s_i, v_i)}`

The fuller leaf form should be treated as:

`ℓ = <r, π, κ, τ, σ, ν>`

where:

- `r`
  - region
- `π`
  - canonical path
- `κ`
  - carrier kind: value or reference
- `τ`
  - declared type
- `σ`
  - semantic label
- `ν`
  - actual value or reference token

This is the missing bridge from theory to engineering.

Without it, composition remains heuristic.

With it, composition can be defined as:

- path matching
- semantic compatibility
- carrier adaptation

## Core Product Model

The correct long-term model is:

- community skills are learning inputs
- learning compiles them into canonical governed skills
- hosted governed skills are what the runtime actually installs, admits, invokes, traces, and exports

This means “skill” has three distinct forms:

1. Learning input
- instruction packs
- tool manifests
- community plugins
- MCP servers and prompts
- OpenAI tool definitions
- LangChain tools
- Semantic Kernel plugins
- Claude/Codex-style task skills and subagents

2. Canonical skill IR
- a normalized intermediate representation
- executor-independent where possible
- declaration-first
- typed inputs and outputs
- boundary-normalized into a canonical path ledger
- authority and data-bound aware
- suitable for policy, static analysis, test generation, and export

3. Hosted governed skill
- admitted
- versioned
- activation-scoped
- trust-scoped
- runtime-packaged
- observable
- exportable

The hosted governed skill is the only form that should be treated as executable truth inside the platform.

## Canonical Boundary Normal Form

Every hosted skill should have a canonical interaction normal form derived from its boundary regions.

The normalization function should be formalized as:

`Φ_r(x) = {ℓ_1, ..., ℓ_n}`

where:

- `r`
  - one of `a, a', b, b', c, c', d, d'`
- `x`
  - the structured body for that region
- `Φ_r(x)`
  - the flattened path-typed leaf set for that region

The total interaction normal form of a skill call is:

`N(f) = Φ_a(a) ∪ Φ_a'(a') ∪ Φ_b(b) ∪ Φ_b'(b') ∪ Φ_c(c) ∪ Φ_c'(c') ∪ Φ_d(d) ∪ Φ_d'(d')`

This normal form should satisfy the invariants from theory:

- total
  - every semantically relevant leaf is represented
- stable
  - equivalent bodies produce the same path structure
- typed
  - each leaf has a declared type
- polarity-preserving
  - value vs reference survives flattening
- region-preserving
  - input, read, write, and output remain distinct
- multiplicity-preserving
  - repeated elements remain distinguishable
- reconstructible
  - the original body can be rebuilt from the ledger

The notation should be canonical path notation, not tied to XML or JSON specifically.

Examples:

- `/a/query`
- `/a/options/roots/0`
- `/a'/source_file`
- `/c'/artifacts/report`
- `/d/summary/text`

## Skill Families

Skills should be treated as one of these families:

- instruction skills
  - prompt-only reusable procedures
  - no executable runtime body
- knowledge skills
  - reusable factual or domain packages
  - may answer or guide but do not execute
- executable skills
  - abilities with a runtime body
  - `wasm_wasi`, `python3`, `bash`, `ansible`, and future runtimes
- composition skills
  - orchestrate or combine other skills
  - planner, reducer, router, pipeline, retry, validation
- hosted service skills
  - remote or broker-backed capabilities exposed through the skill model
- compatibility adapter skills
  - wrappers generated from community formats
  - intended first as learning inputs and migration bridges

## Skill Learning As Compilation

Skill learning should be treated explicitly as a compiler pipeline.

The model should be:

`community input -> normalize -> analyze -> compile -> admit -> host -> observe -> improve -> share`

The learning/compiler stages should be:

1. Ingest
- accept skill inputs from local bundles, remote registries, and supported community formats

2. Normalize
- convert source formats into a canonical internal skill representation

3. Enrich
- infer or synthesize:
  - intent
  - input and output schemas
  - boundary-region classification
  - canonical leaf inventory
  - semantic labels on leaves
  - authority requests
  - data classes touched
  - side effects
  - composition role
  - suggested aliases and family names

4. Analyze
- static validation
- dependency checks
- runtime compatibility checks
- authority and risk analysis
- canonical path normalization checks
- reconstructibility checks
- portability checks

5. Compile
- produce hosted governed artifacts
- emit canonical `bssc_skill.v2`
- emit canonical boundary normal form
- generate tests, fixtures, and provenance metadata

6. Admit
- apply policy
- evaluate approvals
- set lifecycle state

7. Host
- package for execution
- index in persistent skill home
- expose in workstation/runtime surfaces

8. Observe
- gather receipts, outcome quality, performance, escalations, and failure data

9. Improve
- learn from traces
- produce refined canonical versions

10. Share
- export canonical BSSC skill
- optionally re-export into community-compatible adapter forms

This is the right place to put community skills.

Community skills should not be treated as direct trusted runtime truth. They should be treated as source inputs for compilation.

## Hosted Canonical Skill Model

The platform should converge on one canonical governed skill model with these properties:

- stable title identity
- declaration-first semantics
- lifecycle separate from declaration
- runtime package separate from declaration
- typed inputs and outputs
- canonical boundary normal form
- region-aware canonical path notation
- explicit composition metadata
- explicit authority and data classes
- provenance and trust metadata
- replay and receipt correlation

The current `bssc_skill.v2` model is the right base, but it needs extension in four areas:

1. Composition metadata
- role in pipeline
- accepted boundary regions
- emitted boundary regions
- canonical leaf inventory
- source and sink semantics
- output ports
- streamability
- retry/fallback semantics
- idempotence hints

2. Invocation metadata
- aliases
- family names
- common natural-language triggers
- deterministic invocation patterns

3. Hosting metadata
- trust tier
- runtime isolation tier
- compatibility targets
- policy presets

4. Normalization metadata
- canonical path notation version
- leaf classes
- opaque-leaf handling rules
- reconstruction rules

## Runtime And Trust Tiers

The system should stop treating all executable skills as morally equivalent.

The runtime matrix should be explicit:

1. Instruction-only
- no executable body
- safest distribution format
- best for broad community sharing

2. `wasm_wasi`
- preferred hosted executable tier
- strongest isolation model currently supported
- best default for public third-party hosted execution

3. Brokered `python3`
- useful compatibility tier
- governed and traceable
- not equivalent to Wasm isolation

4. Brokered `bash`
- compatibility tier only
- powerful but weakly isolated
- should remain more restricted and more strongly labeled

5. Brokered `ansible`
- specialized operational tier
- high side-effect potential
- should be explicit and policy-heavy

6. Remote or hosted service skill
- network/broker-bound execution
- explicit policy and provenance required

The product rule should be:

- public hosted skills should prefer instruction-only or `wasm_wasi`
- `python3` and `bash` should remain supported for compatibility and learning, not as the default trust story
- the UI and docs must never imply that governed `python3` or `bash` skills are equivalent to Wasm isolation

## Permission Model

The permission model needs to remain split, but it must become more legible.

There are three distinct layers:

1. Declared skill authorities
- what the skill says it needs
- example: `read`, `write`, `communicate`

2. Session capabilities
- what the workstation or runtime session is allowed to expose
- example: `ws.fs.read`, `ws.skill.invoke`, `ws.net.http`

3. Invocation-time delegated grants
- what is actually approved for this invocation
- narrowed by mount, duration, and context

This split is correct and should remain.

The product improvement is not to merge these layers. The improvement is to present them clearly and consistently.

The desired behavior is:

- skills declare authorities
- sessions hold grantable capabilities
- invocations request narrowed rights
- users approve escalation when needed
- receipts record what was requested, granted, denied, and used

The next-stage permission model should add:

- permission presets
  - safe read-only
  - local edit
  - networked tool use
  - operations / automation
- composition-wide permission summaries
- pipeline-wide escalation previews
- stable mapping from declared `communicate` to `ws.net.http`
- clearer direct-path permission failures

## Invocation Model

Skills need one coherent invocation model across:

- controller/runtime
- workstation chat
- workstation CLI
- future APIs

The invocation surface should support both:

1. LLM-routed invocation
- the model infers the right skill or skill family

2. Direct deterministic invocation
- the user or runtime names the exact skill or alias

The system should support both because both are real usage modes.

The desired rules are:

- explicit skill requests stay on the skill path
- implicit asks may resolve to a skill family
- direct deterministic invocation should bypass unnecessary LLM ambiguity
- all invocation paths should converge on one canonical invocation request format
- invocation binding should resolve against canonical boundary regions and path-ledger requirements, not just top-level argument names

That request format should include:

- requested skill or family
- invocation mode
  - direct
  - LLM-selected
  - pipeline
  - iterative
- normalized inputs
- normalized boundary ledger when available
- delegated capability request
- target attachments and mounts
- correlation ids for receipts

## Composition Model

Skills will not be used only one at a time.

The runtime has to support at least four composition modes, but all of them should be grounded in the same three layers from theory:

1. boundary class
- values, references, and their region placement

2. body flattening
- `a, a', b, b', c, c', d, d' -> canonical path ledger`

3. compatibility calculus
- emitted leaves matched to required leaves across steps

Without layer 2, layer 3 stays heuristic.

### Step-Wise

The model or user selects one skill at a time.

Use case:
- interactive chat
- manual approval flows
- exploratory work

### Iterative

The same skill or skill family is invoked repeatedly.

Use case:
- refine until success
- scan until match
- transform many files
- retry under narrowed conditions

### Pipeline

One skill’s output becomes another skill’s input.

Use case:
- read -> parse -> summarize
- search -> filter -> edit
- fetch -> extract -> write

This is the closest analog to Linux pipes.

To support this cleanly, skills should expose not only output form, but the exact emitted leaves and their types, labels, and carrier kinds.

### Algorithmic Composition

Skills are composed as parts of a higher-order procedure.

Use case:

- planner -> executor -> validator
- map -> reduce
- branch -> fallback
- test -> repair -> retest
- inspect -> decide -> act

This composition mode is where the current controller/runtime and workstation need to converge on shared invocation semantics.

## Skill Composition Metadata

To make composition robust, the skill declaration should grow to include composition metadata such as:

- role
  - source
  - transform
  - sink
  - planner
  - validator
  - router
- accepted input forms
  - scalar
  - object
  - stream
  - file
  - resource reference
- accepted required leaves
- emitted leaves
- semantic labels per leaf
- carrier kind per leaf
- region membership per leaf
- output form
- idempotence hint
- retry safety
- statefulness
- partial-result support
- parallelizability
- estimated cost and latency class

Without this, composition stays too dependent on prompt inference alone.

### Leaf Classes

The leaf model should be explicit and small.

At minimum the system should define:

- scalar leaf
- reference leaf
- collection leaf
- null or optional leaf
- opaque leaf

Opaque leaves are important.

Not every body can be safely flattened all the way down, especially for compatibility imports or executor-specific payloads. The model must support partial normalization without pretending that the opaque remainder is semantically resolved.

## Variable Permissions In Composition

Composition needs permission semantics that are stronger than single-invocation semantics.

The model should support:

- step-local permissions
- pipeline-local permissions
- composition-wide upper bounds
- user approval at:
  - first escalation
  - per-step escalation
  - upfront whole-pipeline escalation

The default should remain conservative:

- narrowest grants possible
- shortest duration possible
- most explicit target scoping possible
- narrowest leaf-level binding possible when composition wiring is partially automatic

## Direct Path Resolution

The platform should support skill use that feels closer to shell piping and tool invocation, not only conversational tool choice.

Examples:

- exact skill aliases
- family aliases
- deterministic slash commands
- direct pipeline descriptions
- CLI-native invocation plans

The long-term model should allow:

- LLM to select skills when ambiguity is high
- direct path resolution when the intent and binding are already clear
- deterministic leaf-to-leaf binding when the canonical ledgers already prove compatibility

That means the same skill system should support:

- `Use the symbol search skill to find X`
- `/run-skill symbol-search.find-class symbol=X root=src`
- `symbol-search.find-class | python.read-file | summarize`

The runtime should not need separate parallel implementations for “LLM use” and “deterministic use.”

## Community Compatibility

The system should be deliberately compatible with the ecosystems people already use.

The right approach is not to make BSSC skills identical to every external format. The right approach is:

- import community formats as learning inputs
- normalize them into canonical BSSC skills and canonical boundary ledgers
- optionally export or mirror back into community-compatible shapes

The main compatibility targets should be:

### MCP

MCP already distinguishes:

- tools
- resources
- prompts

This maps well to:

- executable skills
- resource-backed inputs
- instruction or prompt skills

MCP should be treated as a first-class ingestion and export adapter.

### OpenAI Tool Calling

OpenAI tools expose:

- descriptions
- JSON schemas
- multi-step tool call loops

This maps well to executable skills and deterministic invocation schemas.

OpenAI tool definitions should be importable as skill-learning inputs and exportable from compatible BSSC skills.

### Semantic Kernel Plugins

Semantic Kernel plugins are already organized as reusable callable capabilities, including OpenAPI and MCP-backed forms.

These should map cleanly into compatibility adapters and hosted canonical skills.

### LangChain Tools And Toolkits

LangChain distinguishes single tools and grouped toolkits with typed schemas.

This maps naturally to:

- skill
- skill family
- capability bundle

### Claude/Codex Instruction Skills And Subagents

These represent reusable prompt programs and delegated expertise profiles.

They should be treated as:

- instruction-skill learning inputs
- composition-skill learning inputs
- policy and routing hints

They should not be confused with governed executable skills, but they are valuable source material for compiling reusable hosted skills.

The important rule across all of these adapters is:

- community format -> compatibility parser -> canonical boundary normal form -> canonical governed skill

The compatibility parser should not be the hosted runtime model.

## Marketplace And Sharing Model

The platform should support a clean sharing loop:

1. third party creates a community skill
2. the skill is imported as a learning input
3. the compiler produces a canonical hosted governed skill
4. the hosted skill is tested, admitted, and versioned
5. users run the hosted skill
6. receipts and outcomes improve the hosted form
7. the refined form can be shared back out

The hosted registry should track:

- canonical title
- version
- provenance
- source lineage
- trust tier
- runtime tier
- compatibility adapters
- policy approvals
- deprecation and successor guidance

This is the right way to keep community participation without weakening the runtime trust model.

## Observability

Skills should be observable at five levels:

1. learning
- where the skill came from
- what was inferred or synthesized

2. admission
- why the skill was accepted, held, or denied

3. invocation
- who requested it
- how it was resolved
- what permissions were requested and granted
- which leaves were bound automatically vs explicitly

4. execution
- runtime used
- latency
- outputs
- bounded traces
- emitted leaf ledger

5. improvement
- quality
- failure modes
- repeated escalations
- alias and routing effectiveness

Receipts are already the right substrate for this.

The next step is to make skill-level receipts richer and more consistently correlated across:

- import
- compile
- admit
- invoke
- compose
- export

## Product UX Requirements

General-use skills need a cleaner user model than “import a YAML and hope the model guesses right.”

The product should expose:

- discoverable families and aliases
- deterministic slash commands
- direct and conversational invocation
- permission summaries before high-risk execution
- visible executor and trust tier
- visible input and output leaf previews for composition-sensitive skills
- composition previews
- export and share actions

The workstation UX should eventually make the following obvious:

- what the skill is
- where it came from
- what it can do
- what it wants permission to do
- what runtime will execute it
- whether it is trusted, held, or degraded

## Implementation Plan

### Phase 1: Canonical Skill Architecture

- formalize the distinction between:
  - instruction skill
  - learning input
  - canonical hosted governed skill
- extend `bssc_skill.v2` with composition, invocation, and normalization metadata
- formalize the region-aware canonical path ledger
- add canonical aliases and family metadata

### Phase 2: Skill Compiler

- introduce a compiler pipeline from community formats to canonical BSSC skill IR
- emit canonical boundary normal form as part of compilation
- support ingestion adapters for:
  - MCP tools, resources, prompts
  - OpenAI function or tool definitions
  - Semantic Kernel plugins
  - LangChain tools and toolkits
  - `SKILL.md` and subagent-style instruction bundles
- emit canonical hosted governed skill outputs

### Phase 3: Runtime Tiering And Trust Labels

- label all skills with explicit runtime and trust tiers
- make `wasm_wasi` the preferred public hosted executable target
- keep `python3` and `bash` as compatibility tiers with stronger warnings and policy controls

### Phase 4: Unified Invocation Contract

- one invocation request shape for controller, workstation, CLI, and API use
- deterministic and LLM-routed paths converge on the same substrate
- explicit-skill requests never silently degrade to unrelated paths
- invocation resolution uses canonical region-aware leaf matching where possible

### Phase 5: Composition Engine

- add first-class composition metadata and leaf-level compatibility calculus to skills
- support:
  - step-wise
  - iterative
  - pipeline
  - algorithmic composition
- add permission accumulation and narrowing for compositions
- make field-level composition decidable from canonical ledgers rather than prompt heuristics

### Phase 6: Permission Productization

- finish the mapping from declared authorities to grantable session capabilities
- include network and future browser/service capabilities
- add permission presets and per-composition previews

### Phase 7: Registry And Sharing

- canonical hosted registry
- versioning
- provenance
- compatibility exports
- deprecation management

### Phase 8: Learning From Production Use

- use invocation receipts and outcomes as compiler feedback
- improve:
  - aliases
  - input derivation
  - permission prompts
  - runtime recommendations

## Guardrails

The implementation should preserve these constraints:

- do not equate governed `python3` or `bash` with Wasm isolation
- do not let community formats bypass compilation and admission
- do not force everything through conversational invocation
- do not rely only on prompt inference for composition or permissions
- do not treat structured bodies as opaque if the system claims they are composition-compatible
- do not collapse workstation shell concerns into skill runtime concerns
- do not collapse skill declarations into session permission grants

## Success Criteria

The skill system is in good shape when all of the following are true:

- a third party can contribute a community skill in a common format
- the platform can compile it into a canonical hosted governed skill
- the canonical hosted governed skill has a stable boundary normal form
- the hosted skill can run in workstation and runtime surfaces with clear permission semantics
- the same skill can be used conversationally or directly
- pipelines and algorithmic compositions are first-class, not hacks
- composition can bind fields mechanically at leaf level when compatibility is sufficient
- the runtime tier and trust tier are obvious to the user
- receipts explain what happened without raw debugging
- community sharing and hosted sharing reinforce each other rather than fragmenting the ecosystem

## External Ecosystem Signals

The direction above is consistent with current external patterns:

- MCP distinguishes model-controlled tools from user-controlled prompts and resource access, which is a useful separation for skill families and invocation modes: [MCP Tools](https://modelcontextprotocol.io/docs/concepts/tools), [MCP Prompts](https://modelcontextprotocol.io/specification/2024-11-05/server/prompts)
- OpenAI tool calling emphasizes typed tool schemas and multi-step tool-call loops, which aligns with canonical invocation contracts and composition: [OpenAI Using Tools](https://platform.openai.com/docs/guides/tools)
- Semantic Kernel already treats plugins as reusable callable capability bundles and supports OpenAPI and MCP-backed forms: [Semantic Kernel Plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins/)
- Anthropic subagents emphasize separate context, configurable tools, reuse, and flexible permissions, which maps closely to instruction/composition skills and hosted routing: [Claude Code Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- LangChain differentiates tools, toolkits, and shared registries, which is useful for family, bundle, and registry design: [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools), [LangSmith Tool Registry](https://docs.langchain.com/langsmith/use-tools)

These ecosystems are converging on the same underlying ideas:

- typed callable capabilities
- reusable registries
- human-visible permissions
- model-routed and direct invocation
- composition across tools

BSSC should adopt those convergent ideas, but keep one stronger internal rule:

- community formats are inputs
- canonical governed skills are the hosted executable truth
