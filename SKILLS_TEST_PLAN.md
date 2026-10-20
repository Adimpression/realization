# Skills Test Plan

Test-first plan for the theory-backed skill system described in [SKILLS.md](SKILLS.md) and [SKILLS_IMPLEMENTATION.md](SKILLS_IMPLEMENTATION.md).

## Purpose

This file defines how the skill compiler, normalization layer, and composition layer should be tested before and during implementation.

The central rule is:

- do not rely on prompt-level success as the primary proof of skill composition correctness
- prove the binding path directly at the canonical leaf level
- keep the tests explicit enough that we can tell exactly how a mapping succeeded, failed, or required a mapper

The system we want to test is:

- learning input
- compiled hosted skill
- canonical leaf ledger
- composition planner
- invocation plan
- governed execution surface

## Core Testing Principle

Every composition test should answer these questions explicitly:

1. What were the source leaves?
2. What were the target leaves?
3. Which mappings were exact?
4. Which mappings required an explicit mapper?
5. Which mappings were blocked?
6. Which inputs remained user-supplied or constant-bound?
7. What permissions were required per step and for the whole plan?

If a test cannot answer those, it is too high-level.

## Test Layers

### Layer 1: Normalization Invariants

These tests prove the leaf substrate itself.

Required coverage:

- canonical path determinism
- region preservation across `a, a', b, b', c, c', d, d'`
- value vs reference preservation
- primitive kind vs repeated primitive kind preservation
- null and opaque handling through leaf class
- reconstructibility for reconstructible bodies
- stable ordering for maps and collections

Primary target files:

- [skill_path_notation.py](skill_path_notation.py)
- [skill_boundary_normalization.py](skill_boundary_normalization.py)
- [skill_leaf_types.py](skill_leaf_types.py)

Primary tests:

- [tests/test_skill_boundary_normalization.py](tests/test_skill_boundary_normalization.py)
- new path-ledger fixtures as needed

### Layer 2: Learning To Hosted Skill

These tests prove the compiler path:

- learning input or portable bundle
- compiled hosted artifact
- canonical IR
- compiler summary

Required coverage:

- community input survives import
- legacy and v2 bundle import remain backward compatible
- compiled IR includes normalization, family, aliases, hosting metadata
- compiler warnings are stable and bounded
- compiler emits enough metadata to support later composition analysis

Primary target files:

- [skill_compiler.py](skill_compiler.py)
- [skill_ir.py](skill_ir.py)
- [skill_schema_io.py](skill_schema_io.py)
- [governed_skill_installation.py](governed_skill_installation.py)

### Layer 3: Leaf Mapping

These tests prove that skill-to-skill compatibility is evaluated mechanically.

Required coverage:

- value-to-value mapping
- reference-to-reference mapping
- repeated-to-repeated mapping
- exact semantic-label match
- path-segment match
- mapper-required match
- blocked match
- user-input-required target
- constant-bound target

The output should not just be true or false.
It should classify:

- `exact`
- `mapper_required`
- `blocked`
- `unbound`

Primary new target file:

- `skill_composition.py`

Primary new tests:

- `tests/test_skill_composition.py`

### Layer 4: Composition Shapes

These tests prove that mappings can be assembled into actual plans.

Required coverage:

- step-wise linear composition
- iterative composition
- conditional composition
- branching and fan-out
- branch merge / fan-in

Each test should verify:

- step graph
- leaf bindings
- unresolved bindings
- per-step permission envelope
- whole-plan upper-bound permission envelope

#### Step-Wise

Example shape:

- step 1 produces a file reference
- step 2 consumes that file reference

Proof target:

- source leaf path
- target leaf path
- compatibility class

#### Iterative

Example shape:

- step 1 outputs `next_page`
- the same skill is reinvoked until `has_more = false`

Proof target:

- loop-carried leaves
- stop predicate leaves
- iteration-local permission stability

#### Conditional

Example shape:

- step 1 outputs `status`
- if `status == ok` branch to step 2
- else branch to step 3

Proof target:

- branch guard leaf
- branch-local binding resolution
- branch-local permission envelope

#### Branching

Example shape:

- one producer output fans out to two consumers
- or two producers converge into one downstream consumer

Proof target:

- source leaf reuse accounting
- fan-out legality
- merge ambiguity detection

### Layer 5: Trial-Backed Learning Suites

These tests prove the system against real learned/community-style bundles under `trials/`.

This is where we stop trusting toy fixtures alone.

Required domains for partial runs:

- `python`
- `ansible`
- `symbolsearch`
- `apiclient`

Secondary domains:

- `sdkuser`
- `deviceuser`
- `bash`

Two kinds of trial-backed tests are needed.

#### Trial Surface Readiness

Compile real trial skills and classify whether their declarations are composition-ready.

Expected outputs:

- exact mapping ready
- mapper-required
- insufficient declaration richness

This is important because current trial bundles often use generic outputs like `result`.
Those should be diagnosed explicitly rather than silently treated as exact composition matches.

#### Trial Plan Tests

Construct explicit plans over real trial skills and verify:

- exact bound leaves
- mapper-required leaves
- required constants
- permission union
- expected unresolved leaves

This gives us a realistic “learning input -> hosted skill -> composed plan” proof path.

## Mapper Model

The composition layer should think like an API gateway mapper, but over canonical skill leaves.

That means the tests should explicitly distinguish:

- identity mapping
- rename mapping
- constant injection
- projection or extraction mapping
- aggregation mapping
- branch-guard mapping

The first implementation cut only needs:

- identity
- rename
- constant
- blocked

But the test plan should reserve space for:

- structural projection
- repeated-item expansion
- join or reduce
- conditional projection

## Permissions In Tests

Every composition test should also assert permissions.

At minimum:

- per-step authorities
- plan-wide upper-bound authorities
- whether a branch increases permissions
- whether a mapper changes the effective surface

For workstation-backed tests, also assert:

- required session capabilities
- required delegated mounts
- expected escalation points

## Test Data Strategy

The suite should use three data classes of fixtures.

### Class A: Minimal Synthetic Skills

Use these to prove exact mechanics:

- exact value mapping
- repeated mapping
- branch guards
- iteration state

These should be small and deterministic.

### Class B: Trial-Derived Real Skills

Use compiled skills from:

- [trials/python/skill.yaml](trials/python/skill.yaml)
- [trials/ansible/skill.yaml](trials/ansible/skill.yaml)
- [trials/symbolsearch/skill.yaml](trials/symbolsearch/skill.yaml)
- [trials/apiclient/skill.yaml](trials/apiclient/skill.yaml)

Use these to prove real compatibility signals and real limitations.

### Class C: Regression Reports

Use saved report artifacts under [reports](reports) only as validation references, not as the primary source of truth.

## Execution Plan

### Phase 1

Implement and test:

- leaf compatibility classification
- explicit two-skill binding analysis
- sequence-plan validation

Run:

- focused unit suites
- [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)
- partial workstation trial validation for `python` and `ansible`

### Phase 2

Implement and test:

- conditional guards
- branching plans
- iteration plans
- permission envelope aggregation

Run:

- focused unit suites
- partial workstation trial validation for `python`, `ansible`, `symbolsearch`, `apiclient`

### Phase 3

Integrate learning-surface outputs through the same composition analysis.

Run:

- compiler suites
- workstation suite
- broader trial sweep

## Exit Conditions

This plan is not complete until:

- leaf-level mappings are explicit and inspectable
- trial-backed compositions can be classified as exact vs mapper-required vs blocked
- step-wise, iterative, conditional, and branching plans all have tests
- permission envelopes are asserted in those tests
- partial and full trial reruns stay green
