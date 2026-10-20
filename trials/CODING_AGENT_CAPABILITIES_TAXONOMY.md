# Comprehensive Capability Taxonomy for Advanced Code Agents

This document is a product-agnostic breakdown of the capabilities that strong coding agents can possess. It focuses on the capability surface itself, not on any specific tool or vendor.

The organizing principle is simple: a serious code agent is not merely a code generator. It is a system that can maintain correspondence between **intent**, **repository state**, **execution state**, **tool state**, and **human trust**.

---

# 1. Intent understanding and task framing

## 1.1 Natural language intent parsing
- Interpret ambiguous user requests into actionable engineering tasks.
- Separate the visible request from the implied technical objective.
- Infer whether the user wants:
  - explanation,
  - diagnosis,
  - implementation,
  - refactoring,
  - migration,
  - review,
  - automation,
  - debugging,
  - documentation,
  - verification.
- Detect hidden constraints embedded in phrasing, such as:
  - minimal change,
  - production-ready,
  - backward compatibility,
  - low latency,
  - open source preference,
  - language or framework restrictions,
  - security sensitivity.

## 1.2 Goal extraction
- Convert user language into concrete success criteria.
- Distinguish primary objectives from secondary preferences.
- Translate vague outcomes into measurable deliverables.
- Infer the difference between:
  - “make it work,”
  - “make it robust,”
  - “make it elegant,”
  - “make it fast,”
  - “make it safe,”
  - “make it maintainable.”

## 1.3 Constraint identification
- Identify explicit constraints from the prompt.
- Infer implicit constraints from the environment or codebase.
- Detect:
  - runtime constraints,
  - deployment constraints,
  - compatibility constraints,
  - organizational constraints,
  - regulatory constraints,
  - resource constraints.
- Determine whether the task is bounded by:
  - token budget,
  - compute budget,
  - filesystem permissions,
  - network access,
  - secret availability,
  - test environment access.

## 1.4 Problem decomposition
- Split large tasks into dependency-ordered subproblems.
- Separate investigation from execution.
- Separate reversible from irreversible actions.
- Identify tasks suitable for parallel work.
- Identify tasks that require human review before proceeding.

## 1.5 Task type classification
- Classify whether the task is:
  - local edit,
  - repo-wide refactor,
  - issue triage,
  - defect localization,
  - environment repair,
  - dependency upgrade,
  - incident investigation,
  - architecture exploration,
  - integration task,
  - documentation task,
  - CI/CD task.
- Choose distinct strategies per class.

## 1.6 Ambiguity handling
- Detect when terms are overloaded.
- Infer likely meanings from repository context.
- Narrow possible interpretations based on conventions.
- Proceed with best-effort assumptions when uncertainty is acceptable.
- Escalate when ambiguity would risk destructive or misleading action.

## 1.7 Requirement stabilization
- Reformulate unstable informal requests into stable engineering targets.
- Turn examples into specifications.
- Turn observed bugs into reproducible invariants.
- Turn style preferences into editing policies.

---

# 2. Context acquisition and repository grounding

## 2.1 Repository discovery
- Detect repository root.
- Detect monorepo vs polyrepo structure.
- Identify modules, packages, services, apps, libraries, and shared infrastructure.
- Distinguish first-party code from vendored or generated code.

## 2.2 File system awareness
- Traverse directories selectively.
- Identify relevant files by role:
  - source,
  - tests,
  - docs,
  - configs,
  - scripts,
  - schemas,
  - infrastructure,
  - build outputs.
- Respect ignore rules and skip irrelevant artifacts.

## 2.3 Build-system understanding
- Detect package/build ecosystem:
  - npm/pnpm/yarn,
  - cargo,
  - pip/poetry,
  - maven/gradle,
  - bazel,
  - make,
  - cmake,
  - go modules,
  - etc.
- Infer how code becomes executable or deployable.
- Locate build scripts, targets, and entrypoints.

## 2.4 Dependency graph reconstruction
- Infer internal module relationships.
- Infer external package dependencies.
- Identify critical dependency bottlenecks.
- Trace where abstractions depend on each other.
- Understand impact radius of changes.

## 2.5 Symbol graph construction
- Detect classes, functions, methods, interfaces, types, constants, schemas, routes, commands, and templates.
- Link definitions to references.
- Link public APIs to internal implementations.
- Link tests to code under test.

## 2.6 Semantic retrieval
- Retrieve relevant code by meaning, not just literal string match.
- Use surrounding context to disambiguate similar symbols.
- Find examples of a pattern elsewhere in the codebase.
- Retrieve related docs, comments, and historical usage.

## 2.7 Structural retrieval
- Search by syntax or AST structure.
- Find all nodes matching a language construct.
- Identify specific anti-patterns or migration patterns.

## 2.8 Historical grounding
- Read commit history.
- Use blame to identify why lines changed.
- Infer design intent from prior edits.
- Connect regressions to likely source commits.

## 2.9 Documentation grounding
- Read README, design docs, ADRs, inline comments, schemas, issue discussions, and migration notes.
- Distinguish current docs from stale docs.
- Use docs as hints rather than unquestioned truth.

## 2.10 Configuration grounding
- Read config files to infer runtime behavior.
- Identify feature flags, environment variables, service endpoints, logging settings, test runners, lints, and deployment knobs.

## 2.11 Runtime artifact grounding
- Use logs, stack traces, crash dumps, snapshots, network traces, and profiling reports as evidence.
- Link runtime artifacts back to source structure.

## 2.12 Context compression
- Summarize a large repository into a compact working model.
- Preserve the parts needed for the active task.
- Drop distractors without dropping invariants.

---

# 3. Architectural understanding

## 3.1 Layer identification
- Detect presentation, application, domain, data, infra, and utility layers.
- Identify layering violations.
- Understand intended dependency direction.

## 3.2 Boundary detection
- Detect module boundaries and service boundaries.
- Infer ownership zones.
- Infer public vs private APIs.
- Identify unstable seams suitable for intervention.

## 3.3 Control-flow understanding
- Trace how execution moves through functions, methods, callbacks, async boundaries, queues, and services.
- Understand startup and shutdown flows.
- Follow event-driven and reactive pipelines.

## 3.4 Data-flow understanding
- Track how data enters, transforms, persists, and leaves the system.
- Identify validation points, serialization boundaries, and mutation hotspots.
- Trace tainted or untrusted inputs.

## 3.5 State model understanding
- Identify where state lives:
  - memory,
  - database,
  - cache,
  - files,
  - browser,
  - session,
  - message queues.
- Understand consistency and lifecycle of state.

## 3.6 Protocol understanding
- Understand HTTP, RPC, GraphQL, WebSocket, CLI, batch, message bus, file-based, and internal protocol contracts.
- Detect where schema evolution matters.

## 3.7 Invariant discovery
- Infer assumptions the system relies on.
- Detect:
  - type invariants,
  - ordering invariants,
  - temporal invariants,
  - authorization invariants,
  - idempotency invariants,
  - transactional invariants.
- Preserve these during changes.

## 3.8 Non-functional architecture understanding
- Understand architecture as it relates to:
  - performance,
  - resilience,
  - observability,
  - security,
  - operability,
  - scalability.

---

# 4. Code navigation and retrieval operations

## 4.1 Lexical search
- Search text exactly.
- Use regex when necessary.
- Search with include/exclude filters.
- Pivot between file-level and repo-level scope.

## 4.2 Symbol-aware navigation
- Jump to definition.
- Jump to references.
- Find implementations.
- Find interface inheritance and overrides.
- Understand call graph neighborhoods.

## 4.3 Cross-language navigation
- Follow links across:
  - frontend/backend,
  - schema/client,
  - protobuf/generated code,
  - SQL/application,
  - infrastructure/runtime configs.

## 4.4 Example mining
- Find canonical examples already in the repository.
- Reuse established patterns instead of inventing new ones.
- Identify style precedents.

## 4.5 Test-to-code mapping
- Find which tests cover which code.
- Find code with no tests.
- Find similar failures in historical test files.

## 4.6 Error-to-code mapping
- Map stack traces and diagnostics to likely root files and symbols.
- Resolve minified, transpiled, or generated traces where possible.

## 4.7 Search strategy selection
- Choose between:
  - lexical search,
  - semantic search,
  - structural search,
  - blame/history search,
  - doc search,
  - runtime evidence search.
- Switch strategy when the first fails.

---

# 5. Editing and transformation capabilities

## 5.1 Local text editing
- Insert, replace, delete, move text.
- Preserve formatting and indentation.
- Avoid collateral damage.

## 5.2 Syntax-aware editing
- Edit while preserving parse validity.
- Maintain imports, braces, indentation, quoting, and delimiters.
- Avoid breaking the file structure.

## 5.3 AST-aware transformation
- Rewrite code at the syntax tree level.
- Apply safe structural changes across many files.
- Enable robust refactors beyond string replacement.

## 5.4 Type-aware editing
- Respect static type constraints.
- Update type annotations alongside implementation.
- Anticipate type ripple effects.

## 5.5 Multi-file coordinated edits
- Update implementation, interface, tests, docs, and config together.
- Preserve consistency across all touched surfaces.
- Ensure renamed concepts are fully propagated.

## 5.6 Signature changes
- Change function/method signatures.
- Update all call sites.
- Update overloads, interfaces, mocks, tests, wrappers, and adapters.

## 5.7 Import and dependency hygiene
- Add imports,
- remove dead imports,
- sort imports if needed,
- avoid unused dependencies,
- prevent circular import mistakes.

## 5.8 Refactoring operations
- Rename.
- Extract method/function/class/module.
- Inline.
- Move symbol across files.
- Split modules.
- Consolidate duplicates.
- Normalize patterns.
- Introduce abstractions only where justified.

## 5.9 API migration edits
- Migrate old APIs to new APIs.
- Handle deprecated parameters and changed semantics.
- Preserve behavior during transition.
- Stage migrations when necessary.

## 5.10 Generated code awareness
- Avoid editing generated files unless intended.
- Edit source-of-generation instead.
- Regenerate artifacts when needed.

## 5.11 Config and infra editing
- Modify YAML, JSON, TOML, XML, Dockerfiles, CI configs, Terraform, Helm, SQL, and shell scripts safely.
- Understand schema expectations and operational implications.

## 5.12 Style preservation
- Match local naming, spacing, comment style, error handling, logging patterns, and architectural idioms.
- Avoid introducing foreign style.

## 5.13 Minimal-diff discipline
- Prefer the smallest change that satisfies the objective.
- Reduce review burden.
- Preserve blame readability.

## 5.14 Broad rewrite capability
- When necessary, perform non-minimal rewrites to eliminate deeper structural problems.
- Justify when broad rewrites dominate incremental edits.

---

# 6. Code generation capabilities

## 6.1 Greenfield generation
- Create new modules, services, classes, functions, scripts, tests, and configs from scratch.
- Generate scaffolding that is immediately usable.

## 6.2 In-place completion
- Fill TODOs and partial implementations.
- Complete stubs and interface implementations.
- Continue patterns from surrounding code.

## 6.3 Pattern-constrained generation
- Generate code in the style of the existing codebase.
- Reuse local abstractions.
- Honor project conventions.

## 6.4 Template generation
- Produce boilerplate with the right wiring.
- Generate handlers, DTOs, schemas, migrations, tests, docs, and configs in coordinated fashion.

## 6.5 Spec-driven generation
- Generate code from:
  - user stories,
  - API specs,
  - schemas,
  - examples,
  - expected I/O behavior,
  - test cases.

## 6.6 Transformation generation
- Generate migration shims, adapters, wrappers, and compatibility layers.
- Generate codemods or scripts to apply changes at scale.

## 6.7 Documentation generation
- Generate README sections, API docs, upgrade notes, architecture summaries, and changelog entries.

## 6.8 Test generation
- Generate unit tests, integration tests, regression tests, fixtures, mocks, and test data.

---

# 7. Execution and environment interaction

## 7.1 Command execution
- Run shell commands.
- Chain commands.
- Capture stdout/stderr and exit codes.
- Detect shell/environment failures.

## 7.2 Build execution
- Run build tools.
- Interpret compile output.
- Distinguish syntax failure, dependency failure, config failure, and environment failure.

## 7.3 Test execution
- Run targeted tests and full suites.
- Run with filters, seeds, verbosity, or debug flags.
- Re-run only affected tests where possible.

## 7.4 Lint and format execution
- Run formatters and linters.
- Interpret rule violations.
- Distinguish stylistic warnings from correctness problems.

## 7.5 Type-check execution
- Run static type systems.
- Interpret mismatch reports.
- Use diagnostics to guide edits.

## 7.6 Script and task runner execution
- Run project-specific scripts, make targets, npm scripts, CI wrappers, migrations, and bootstrapping commands.

## 7.7 Process management
- Start servers.
- Stop or restart processes.
- Track ports and PIDs.
- Detect hung or zombie processes.

## 7.8 Environment setup
- Create or use venvs, containers, workspaces, node versions, package caches, local databases, and supporting services.
- Detect missing dependencies and unmet prerequisites.

## 7.9 Filesystem side effects
- Create, move, rename, delete files and directories.
- Manage temp files, logs, build outputs, and caches safely.

## 7.10 Permission awareness
- Detect when the environment blocks an action.
- Respect sandbox boundaries.
- Escalate or degrade gracefully.

## 7.11 Resource awareness
- Monitor timeouts, memory pressure, CPU-heavy steps, and long-running tasks.
- Adapt execution strategy to resource limits.

---

# 8. Closed-loop verification

## 8.1 Observation after change
- Verify that edits compile or parse.
- Verify that tests pass.
- Verify no new diagnostics were introduced.

## 8.2 Behavioral verification
- Verify expected runtime behavior, not just syntactic validity.
- Check return values, outputs, logs, state transitions, side effects, and UI behavior.

## 8.3 Regression detection
- Compare before/after behavior.
- Detect broken dependent paths.
- Detect shifted semantics masked by passing tests.

## 8.4 Incremental verification
- Verify the smallest affected surface first.
- Expand outward if failures persist.
- Use staged confidence-building.

## 8.5 Negative verification
- Confirm that forbidden behavior does not occur.
- Check for absent side effects, absent exceptions, absent leaks, absent authorization bypasses.

## 8.6 Invariant verification
- Check preserved contracts.
- Confirm schema compatibility, API shape compatibility, and state consistency.

## 8.7 Deployment-surface verification
- Verify packaging, containerization, environment config, startup, migrations, and service health.

## 8.8 Human-verifiable evidence production
- Produce diffs, logs, test output summaries, screenshots, and rationale so humans can inspect the result.

---

# 9. Debugging and fault localization

## 9.1 Reproduction
- Reproduce bugs deterministically.
- Infer minimal reproduction from issue descriptions.
- Narrow environmental variables affecting reproduction.

## 9.2 Symptom triage
- Separate symptom from cause.
- Distinguish user-facing failure from underlying defect.
- Determine whether the failure is code, config, data, infra, or dependency related.

## 9.3 Hypothesis generation
- Form likely explanations based on evidence.
- Rank hypotheses by plausibility and cost to test.
- Revise hypotheses as evidence changes.

## 9.4 Fault localization
- Identify likely defective file, function, condition, or integration point.
- Reduce search space quickly.

## 9.5 Stack-trace interpretation
- Parse call stacks, nested exceptions, chained causes, and framework wrappers.
- Trace from framework internals back to user code.

## 9.6 Diagnostic instrumentation
- Add logs, assertions, temporary checks, counters, traces, or probes.
- Remove or clean them afterward when appropriate.

## 9.7 Differential debugging
- Compare passing and failing cases.
- Compare old and new behavior.
- Compare environments.
- Compare branch or commit states.

## 9.8 Concurrency and timing debugging
- Diagnose races, deadlocks, ordering bugs, async hazards, retries, and eventual consistency issues.

## 9.9 Data-dependent debugging
- Detect malformed, missing, stale, or unexpected data as causal factors.
- Inspect serialized forms and boundary transformations.

## 9.10 Root-cause vs patch distinction
- Decide whether to treat the symptom, patch the cause, or redesign the subsystem.

---

# 10. Testing intelligence

## 10.1 Test discovery
- Find test frameworks and conventions.
- Identify test entrypoints and fixtures.
- Detect snapshot, property, integration, and end-to-end tests.

## 10.2 Test selection
- Choose the smallest useful test scope.
- Run a focused test before running the whole suite.
- Expand scope when needed.

## 10.3 Test authoring
- Write targeted tests that exercise the changed behavior.
- Use clear names and arrange-act-assert structure where appropriate.
- Generate realistic fixtures.

## 10.4 Regression test creation
- Encode the failing scenario so it cannot silently reappear.
- Preserve the historical lesson of the bug.

## 10.5 Mocking and fixture design
- Create mocks that are faithful enough to catch important behavior.
- Avoid over-mocking.
- Use factories, builders, or fixtures appropriately.

## 10.6 Property and fuzz testing awareness
- Recognize when invariants can be tested over ranges rather than examples.
- Suggest or generate property-style tests.

## 10.7 Flaky test handling
- Detect nondeterminism.
- Distinguish infrastructure flakiness from product defects.
- Reduce timing sensitivity.

## 10.8 Coverage reasoning
- Infer what paths are covered or uncovered.
- Understand that coverage quantity is not the same as test adequacy.

## 10.9 Test maintenance
- Update tests intentionally when behavior changes.
- Avoid blindly rewriting tests to satisfy new output.

## 10.10 Oracle quality
- Ensure tests check the right thing.
- Avoid false confidence from weak assertions.

---

# 11. Static analysis and formal signals

## 11.1 Parser diagnostics
- Use syntax errors to localize malformed edits.
- Recover quickly from parse breakage.

## 11.2 Type-system diagnostics
- Interpret missing types, mismatches, generic constraints, nullability issues, variance problems, and overload resolution failures.

## 11.3 Linter diagnostics
- Distinguish style issues from bug predictors.
- Learn codebase-specific lint priorities.

## 11.4 Security scanner diagnostics
- Interpret SAST findings.
- Separate real risk from noise.
- Prioritize exploitable patterns.

## 11.5 Schema validation signals
- Use JSON schema, OpenAPI, protobuf, database schema, GraphQL schema, or config schema feedback.

## 11.6 Formal or semi-formal invariants
- Respect contracts expressed in assertions, types, preconditions, postconditions, or domain rules.

## 11.7 Diagnostic clustering
- Group related warnings into root themes.
- Fix causes rather than each symptom individually.

---

# 12. Semantic reasoning over code

## 12.1 Behavior inference
- Infer what code does beyond literal syntax.
- Understand domain semantics.

## 12.2 Intent inference from structure
- Deduce why code is written a certain way.
- Distinguish accidental complexity from deliberate constraint handling.

## 12.3 Side-effect reasoning
- Predict filesystem, network, database, cache, and UI side effects.
- Recognize hidden stateful consequences.

## 12.4 Ripple-effect prediction
- Predict what else breaks when a symbol, schema, or protocol changes.
- Anticipate downstream impacts before running everything.

## 12.5 Equivalence reasoning
- Judge whether two implementations are functionally equivalent.
- Detect subtle changes in semantics.

## 12.6 Counterfactual reasoning
- Compare alternate designs or patches.
- Estimate cost, risk, and future maintenance burden.

## 12.7 Abstraction judgment
- Recognize when to introduce a reusable abstraction and when not to.
- Avoid premature generalization.

---

# 13. Version control intelligence

## 13.1 Diff understanding
- Read and summarize diffs.
- Separate mechanical from semantic changes.
- Highlight high-risk hunks.

## 13.2 Commit analysis
- Read commit history for intent.
- Detect regressions, migrations, refactors, and hotfix patterns.

## 13.3 Blame analysis
- Find who changed a line and when.
- Use commit messages to infer rationale.

## 13.4 Branch awareness
- Compare branches.
- Understand cherry-picks, rebases, merges, and divergence.

## 13.5 Change packaging
- Group edits into coherent logical units.
- Produce atomic commits.
- Avoid mixing unrelated changes.

## 13.6 Reversible workflow support
- Create changes that are easy to inspect, revert, or bisect.
- Preserve clean commit narratives.

## 13.7 Conflict reasoning
- Understand merge conflicts.
- Resolve conflicts semantically rather than mechanically.

## 13.8 Release-awareness
- Understand tags, release branches, hotfix flow, and backport constraints.

---

# 14. Documentation intelligence

## 14.1 Documentation reading
- Read existing docs and use them as context.
- Detect contradictions between docs and code.

## 14.2 Documentation synthesis
- Summarize architecture, workflows, APIs, and change impacts for humans.

## 14.3 Inline explanation generation
- Add comments only where they improve local understanding.
- Avoid redundant comments that restate obvious code.

## 14.4 Change communication
- Produce PR descriptions, migration notes, release notes, and operator instructions.

## 14.5 Knowledge externalization
- Write down assumptions, tradeoffs, and evidence.
- Reduce dependence on hidden model state.

## 14.6 Example creation
- Generate examples that clarify new APIs or behaviors.

---

# 15. User interaction and collaboration

## 15.1 Clarification strategy
- Know when clarification is necessary and when best-effort action is better.
- Ask high-value questions only when uncertainty blocks progress.

## 15.2 Progress explanation
- Explain what was found, changed, verified, and not verified.
- Communicate with evidence, not bluff.

## 15.3 Assumption declaration
- Make key assumptions legible.
- Separate fact from inference.

## 15.4 Option presentation
- Offer alternative solutions when tradeoffs matter.
- Compare options by risk, cost, speed, and maintainability.

## 15.5 Reviewability
- Present changes so a human can inspect them efficiently.
- Use concise, structured summaries.

## 15.6 Collaboration with human developers
- Yield control at the right time.
- Accept corrections.
- Incorporate human architectural preferences.

## 15.7 Confidence calibration
- Signal uncertainty proportionally.
- Avoid false certainty when evidence is weak.

---

# 16. Tool orchestration

## 16.1 Tool selection
- Choose the best tool for search, edit, run, inspect, or verify.
- Avoid using heavy tools for light tasks.

## 16.2 Tool chaining
- Use outputs of one tool as inputs to the next.
- Form coherent workflows rather than isolated calls.

## 16.3 Parallel tool usage
- Run independent searches or checks in parallel.
- Merge results coherently.

## 16.4 Fallback strategies
- Switch tools when one fails.
- Use approximate evidence when precise tooling is unavailable.

## 16.5 Tool-state awareness
- Track what tool actions changed the environment.
- Avoid stale assumptions after commands or edits.

## 16.6 Cost-awareness
- Trade off speed, depth, token use, and computational expense.
- Use cheap retrieval before expensive synthesis when appropriate.

---

# 17. Browser, UI, and human-surface verification

## 17.1 Browser control
- Open pages, click, type, navigate, and inspect output.
- Verify flows end-to-end.

## 17.2 DOM and frontend state inspection
- Inspect rendered state, DOM structure, console errors, and network calls.
- Link frontend failures to source code.

## 17.3 Screenshot and visual inspection
- Capture visual evidence.
- Compare expected and actual UI states.

## 17.4 Form and workflow testing
- Test user paths through forms, auth, search, checkout, dashboards, settings, etc.

## 17.5 Accessibility checks
- Detect obvious accessibility issues:
  - labels,
  - focus,
  - keyboard flow,
  - contrast metadata where available,
  - semantic roles.

## 17.6 Client-server integration verification
- Confirm that frontend and backend contracts align in practice.

---

# 18. Runtime and systems intelligence

## 18.1 Network awareness
- Understand requests, responses, retries, timeouts, status codes, headers, caching, and protocol misuse.

## 18.2 Storage awareness
- Reason about databases, object storage, caches, queues, and local files.

## 18.3 Process and concurrency awareness
- Reason about processes, threads, event loops, workers, scheduling, and locks.

## 18.4 Deployment awareness
- Understand containers, services, environment variables, orchestration, and boot sequences.

## 18.5 Observability awareness
- Read metrics, logs, traces, health checks, and alerts.
- Use them to guide diagnosis.

## 18.6 Resilience reasoning
- Detect retry storms, failure amplification, lack of backpressure, poor circuit breaking, and weak error handling.

## 18.7 Scalability reasoning
- Identify throughput bottlenecks, fan-out issues, serialization hotspots, and stateful constraints.

---

# 19. Security capabilities

## 19.1 Secret handling
- Avoid exposing secrets in code, logs, commits, or outputs.
- Respect secret boundaries in environment and config.

## 19.2 Input validation reasoning
- Detect unsafe handling of untrusted input.
- Enforce validation and sanitization at boundaries.

## 19.3 Injection risk detection
- Detect SQL injection, command injection, template injection, path traversal, and related issues.

## 19.4 Auth and authorization reasoning
- Distinguish authentication from authorization.
- Identify bypasses, missing checks, and inconsistent policy enforcement.

## 19.5 Dependency risk awareness
- Notice vulnerable packages or risky upgrade paths.
- Reason about supply-chain exposure.

## 19.6 Serialization/deserialization safety
- Detect unsafe parsing, object injection, and schema mismatch risks.

## 19.7 Data exposure reasoning
- Detect accidental logging of sensitive data.
- Detect insecure defaults in APIs and UIs.

## 19.8 Security patching
- Apply focused changes that actually reduce exploitability without breaking product behavior.

## 19.9 Principle-of-least-privilege reasoning
- Avoid granting more access, scope, or visibility than necessary.

---

# 20. Performance capabilities

## 20.1 Complexity reasoning
- Estimate algorithmic cost.
- Detect quadratic or worse patterns where they matter.

## 20.2 Profiling interpretation
- Read profiler outputs and flame graphs.
- Separate CPU, memory, IO, and lock contention issues.

## 20.3 Database/query performance
- Detect N+1 queries, missing indexes, excessive round trips, and poor query shapes.

## 20.4 Caching reasoning
- Understand cache locality, invalidation, staleness, hit rate, and consistency tradeoffs.

## 20.5 Allocation and memory reasoning
- Detect leaks, large transient allocations, and wasteful object churn.

## 20.6 Latency decomposition
- Break end-to-end latency into constituent steps.
- Target the dominant terms first.

## 20.7 Throughput reasoning
- Understand concurrency limits, worker models, batching, and backpressure.

## 20.8 Benchmark-aware change making
- Use measurement to validate performance claims where possible.

---

# 21. Data and schema intelligence

## 21.1 Schema comprehension
- Understand relational schemas, document schemas, event schemas, API schemas, and config schemas.

## 21.2 Migration reasoning
- Create safe schema migrations.
- Handle forward/backward compatibility.
- Preserve existing data.

## 21.3 Serialization boundary handling
- Map data correctly across wire formats, storage formats, and in-memory structures.

## 21.4 Validation and normalization
- Identify where inputs should be normalized and validated.
- Avoid duplicate or inconsistent validation logic.

## 21.5 Data integrity reasoning
- Preserve uniqueness, referential integrity, transaction safety, and idempotency.

## 21.6 Historical data awareness
- Consider old records, partial records, corrupt records, and migration leftovers.

---

# 22. Multi-language and polyglot competence

## 22.1 Language-specific syntax and idioms
- Respect idiomatic patterns in each language.
- Avoid translating patterns mechanically across ecosystems.

## 22.2 Cross-language interface tracing
- Track how TypeScript talks to Go, how Python talks to SQL, how protobuf drives generated clients, etc.

## 22.3 Build and package differences
- Understand language-specific toolchains and dependency resolution behaviors.

## 22.4 Interop edge-case awareness
- Detect encoding, serialization, type narrowing, and async boundary mismatches across language edges.

## 22.5 Generated-client awareness
- Understand code generated from schemas or protocols and how source-of-truth changes propagate.

---

# 23. Planning, strategy, and search policies

## 23.1 Plan generation
- Produce a sane sequence of actions.
- Keep planning proportional to task complexity.

## 23.2 Investigation-first strategy
- Gather evidence before editing when the problem is poorly localized.

## 23.3 Edit-first strategy
- Make direct small changes when the task is obvious and low risk.

## 23.4 Breadth-first vs depth-first search
- Search broadly for architecture.
- Dive deeply for localized bugs.
- Switch modes intentionally.

## 23.5 Risk-aware sequencing
- Do reversible actions first.
- Delay disruptive actions until confidence rises.

## 23.6 Checkpointing
- Preserve intermediate states so recovery is possible after failed attempts.

## 23.7 Stop-condition reasoning
- Know when enough evidence is sufficient.
- Avoid endless exploration when the answer is already established.

---

# 24. Memory and continuity

## 24.1 Session memory
- Remember user constraints and goals during a session.
- Avoid repeated rediscovery.

## 24.2 Task-state tracking
- Track what files were inspected, what commands were run, what failed, and what remains.

## 24.3 Decision memory
- Preserve why a given path was chosen over alternatives.

## 24.4 Project convention memory
- Remember naming, layering, test style, and preferred patterns over repeated interactions.

## 24.5 Open-loop avoidance
- Avoid forgetting partially completed work or implicit commitments.

---

# 25. Preference, policy, and rule following

## 25.1 Project rules
- Follow repository-specific instructions.
- Honor local guardrails and contribution patterns.

## 25.2 User preference adaptation
- Adapt to preferred libraries, style, verbosity, safety level, and workflow.

## 25.3 Organizational policy compliance
- Respect rules around secrets, approvals, branch protection, licensing, compliance, and review.

## 25.4 Tool permission policy compliance
- Respect allowed/disallowed tools and action boundaries.

## 25.5 Conflict resolution among rules
- Resolve clashes between user request, project policy, and system constraints sensibly.

---

# 26. Reliability, robustness, and failure recovery

## 26.1 Error handling in the agent workflow
- Recover from failed commands, failed parses, missing files, and transient runtime problems.

## 26.2 Retry strategy
- Retry only when the failure mode suggests retry could work.
- Avoid mindless repetition.

## 26.3 Partial progress preservation
- Keep useful results even when the whole task cannot be completed.

## 26.4 Degradation strategy
- Fall back to narrower scope or lower-fidelity methods when ideal tools are unavailable.

## 26.5 Contradiction detection
- Detect when evidence sources disagree.
- Reconcile or surface the conflict.

## 26.6 Hallucination resistance
- Avoid inventing files, symbols, outputs, commits, tests, or environment state.
- Ground claims in visible evidence.

## 26.7 Completion honesty
- Distinguish:
  - edited,
  - suggested,
  - verified,
  - partially verified,
  - not verified.

---

# 27. Scale handling

## 27.1 Large-repository navigation
- Work in monorepos and high-file-count projects without losing coherence.

## 27.2 Context-window economy
- Retrieve only what is needed for the current subproblem.

## 27.3 Hierarchical summarization
- Build summaries of subsystems, then summaries of summaries.

## 27.4 Sharding tasks
- Break large migrations or analyses into manageable units.

## 27.5 Incremental rollout reasoning
- Plan staged adoption and migration across large codebases.

---

# 28. Automation and headless operation

## 28.1 Scriptable operation
- Work from CLI or automation runners.
- Accept machine-readable inputs and produce machine-readable outputs.

## 28.2 CI/CD integration
- Run in pipelines.
- Analyze build/test failures in automated environments.
- Propose or apply repairs.

## 28.3 Scheduled or recurring maintenance
- Support repetitive tasks such as dependency refreshes, lint fixes, or report generation.

## 28.4 Non-interactive safety
- Operate safely when no human is present to approve every step.

## 28.5 Artifact emission
- Output logs, patches, summaries, JSON reports, or markdown reports for downstream systems.

---

# 29. Multi-agent and delegation capabilities

## 29.1 Work partitioning
- Split a large task into subtasks suitable for separate agents.

## 29.2 Specialist delegation
- Delegate testing, search, architecture analysis, code editing, or documentation to specialized subagents.

## 29.3 Parallel investigation
- Search multiple hypotheses or subsystems simultaneously.

## 29.4 Result aggregation
- Merge subagent findings into one coherent answer or patch.

## 29.5 Conflict arbitration
- Resolve inconsistent findings between subagents.

## 29.6 Shared-state management
- Keep subagents coordinated around a common task state.

---

# 30. Artifact production and trust surfaces

## 30.1 Patch generation
- Produce diffs and edits in a reviewable form.

## 30.2 Evidence summaries
- Summarize what commands were run and what they showed.

## 30.3 Design notes
- Explain why an approach was chosen.

## 30.4 Verification reports
- State what was verified and by which mechanism.

## 30.5 Migration guides
- Help humans adopt or review broad changes.

## 30.6 Auditability
- Leave behind enough trace that another engineer can reconstruct the work.

---

# 31. Meta-capabilities: judgment and taste

## 31.1 Materiality judgment
- Know which details matter and which do not.

## 31.2 Proportionality
- Match solution complexity to problem complexity.

## 31.3 Elegance under constraint
- Improve clarity without over-engineering.

## 31.4 Maintainability judgment
- Prefer changes future developers can understand and extend.

## 31.5 Reuse judgment
- Know when to reuse an existing abstraction versus adding a new one.

## 31.6 Local-vs-global optimization judgment
- Recognize when a local fix creates broader future cost.

## 31.7 Trust preservation
- Operate in ways that make human trust more rational, not less.

---

# 32. Capability maturity levels

A useful way to think about maturity:

## 32.1 Basic
- Can search files.
- Can edit local code.
- Can answer questions about code.
- Can generate snippets.

## 32.2 Intermediate
- Can coordinate multi-file edits.
- Can run tests and fix failures.
- Can work with repository context.
- Can explain diffs and produce docs.

## 32.3 Advanced
- Can debug, refactor, verify, and operate across tools.
- Can reason about architecture and ripple effects.
- Can work with browser, terminal, and external systems.

## 32.4 Frontier
- Can sustain closed-loop autonomous work with robust grounding.
- Can manage long-horizon tasks.
- Can delegate, verify deeply, and produce trustworthy artifacts.
- Can remain useful under ambiguity, scale, and operational friction.

---

# 33. Canonical capability clusters

These clusters often matter more than isolated features:

## 33.1 Repository comprehension cluster
- discovery,
- indexing,
- symbol graph,
- dependency graph,
- context compression,
- architecture inference.

## 33.2 Action cluster
- editing,
- generation,
- command execution,
- process control,
- config changes,
- filesystem manipulation.

## 33.3 Verification cluster
- tests,
- builds,
- types,
- runtime inspection,
- browser verification,
- regression detection.

## 33.4 Reliability cluster
- recovery,
- checkpointing,
- uncertainty detection,
- evidence grounding,
- honest reporting.

## 33.5 Collaboration cluster
- explanation,
- reviewability,
- policy following,
- change summaries,
- human handoff.

## 33.6 Operational intelligence cluster
- security,
- performance,
- deployment,
- observability,
- data integrity,
- incident-style reasoning.

---

# 34. The deepest distinction

The highest-order distinction among code-agent capability sets is this:

A weak system primarily performs **token-level continuation over code**.

A strong system can maintain a stable mapping across:
- user intent,
- repository structure,
- execution evidence,
- tool outputs,
- environment constraints,
- and human review.

Everything above is, in one sense, a decomposition of that single faculty.

When “nothing is left untouched,” what remains after decomposition are these enduring axes:
- understanding,
- retrieval,
- transformation,
- execution,
- verification,
- judgment,
- trust.

That is the full terrain.
