# Business Continuity and Versioning

## Status

This document records the continuity and versioning behavior implemented by the
current repository. It was reconciled with the codebase on 2026-10-20.

Statements under **Current behavior** describe implemented behavior. Statements
under **Required hardening** describe gaps or proposed work and must not be read
as current guarantees.

Business continuity in this repository is not one database or one directory. It
is the ability to recover the related durable stores required by a particular
journey, restore their identity relationships, and resume through the same
governed interfaces.

## Terms

- **Durable** means material is written to a filesystem or SQLite and can
  survive a normal process restart. It does not imply atomicity, replication,
  backup, immutability, or disaster recovery.
- **Resumable** means enough state exists to continue a specific workflow. A
  durable record can be useful for audit without being sufficient for resume.
- **Canonical** identifies the owning store for a kind of truth. Derived
  projections and indexes are not canonical merely because they are durable.
- **Version** means an explicitly identified historical state that can be
  selected and recovered. A current file with a content hash is not by itself a
  first-class version history.
- **Release** means an explicitly recorded publication decision. A successful
  build is not automatically a release.

## Current Continuity Model

The repository currently has seven distinct continuity domains:

1. Workstation session
2. Core governed execution
3. Subject corpus and workflow
4. Chat transcript
5. Publication lineage
6. Skill and governance home
7. Blend world and workflow

They are connected, but they are not interchangeable. A backup of one domain
does not necessarily permit another domain to resume.

| Domain | Canonical durable root | Normal restart position | Principal gap |
| --- | --- | --- | --- |
| Workstation session | A workstation session root | Session material can be reopened | Pure client-view state is process-local |
| Core execution | Saved `SystemState` JSON plus the configured SQLite database | A run can resume only when state was explicitly saved | No single atomic checkpoint across state, SQLite, configuration, and host realizers |
| Subject corpus | `corpus/<subject_id>/` | Subject workflow gates and editor state can resume | No immutable named subject versions or global work queues |
| Chat transcript | Session `MESSAGES.jsonl` | Conversation history can be inspected | No stable message identity and incomplete backlinks from admitted subject material |
| Publication | `corpus/<subject_id>/publications/<publication_id>/` | Builds and compositions can be inspected and rebuilt | No first-class release record or release pointer |
| Skill/governance home | Workstation skill home and its SQLite store | Admitted and installed abilities survive restart | No repository-wide backup/migration contract with the other stores |
| Blend world/workflow | Session/world JSON and workflow plan/run files | Durable plans and runs can be reopened | No atomic checkpoint with session, subject, or core state |

## 1. Workstation Session

### Current behavior

The workstation session is the host-owned operational shell. Its persistence is
implemented by
[session.py](workstation/runtime_core/src/workstation/runtime/core/session.py).

A session can contain:

- `SESSION.json`
- `TASK.md`
- `TASK_CONTRACT.json`
- `ATTACHMENTS.json`
- `TOOLS.json`
- `MESSAGES.jsonl`
- `receipts/events.jsonl`
- `LAST_RESPONSE.json`
- `README.md`
- `WORKSTATION.toml`
- `BLEND_CONTEXT.json`
- `BLEND_SESSION.json`
- optional `BLEND_WORLD.json`
- `BLEND_WORKFLOWS.json`
- `workflows/plans/*.json`
- `workflows/runs/*.json`
- configured skill catalog and shortlist projections

The session root is durable operational material. It is not the canonical home
of subject truth, core reduction state, skill admission state, or publication
truth.

The canonical event bus in
[event_bus.py](workstation/foundation_events/src/workstation/foundation/events/event_bus.py)
is process-local. The workstation persists an event receipt before publishing
the live event where the receipt-producing helper is used. Live subscriptions
must therefore be reconstructed after restart; the event bus itself is not a
continuity store.

The subject service maintains per-client view state in
[client_sessions.py](workstation/subject_service/src/workstation/subject/service/client_sessions.py).
Changes that are purely client-view concerns are intentionally not written to
the subject corpus. A process restart can consequently lose transient cursor or
selection state even though the underlying subject workflow remains durable.

### Required hardening

- Define which session files are authoritative versus reproducible projections.
- Add a tested session export/restore contract.
- Record compatibility metadata for the application and schemas needed to
  reopen a session.
- Preserve the intentional separation between client-view state and governed
  workflow state.

## 2. Core Governed Execution

### Current behavior

The independently packaged core is split across:

- [core engine API](core_engine/src/realized_core_engine/api.py)
- [core CLI](core_app/src/realized_core/cli.py)
- [CLI configuration](core_engine/src/realized_core_engine/cli_support.py)
- [system state](system_state.py)

`run` creates a `SystemState`. `resume` and `inspect` load a serialized
`SystemState` JSON document. The CLI exposes the corresponding `--state-out`,
`--state-in`, and `--sqlite` options.

Two durable resources have different responsibilities:

1. The serialized `SystemState` contains the in-flight governed execution
   graph, ledger, trace, inlets, outlets, claims, evidence, artifacts, grants,
   and effect traces needed by the reduction lifecycle.
2. SQLite stores durable artifacts and indexes used by the engine. It is not a
   serialization of the complete in-flight `SystemState`.

Saving the state JSON is optional. A run that was not given a state output path
does not acquire a resumable state checkpoint merely because SQLite was
enabled.

A faithful resume also depends on compatible runtime configuration, code and
schema versions, and the same declared host realizers for any operation that
may be invoked. The persisted state and SQLite store do not manufacture missing
host capabilities.

### Recovery rule

For a resumable core run, preserve together:

- the saved `SystemState` JSON
- the exact SQLite database used by the run, when configured
- runtime and package version information
- non-secret configuration needed to reconstruct the run
- identities and versions of required ability bundles and host realizers
- relevant authority and effect receipts

The state JSON and SQLite database are complementary. Neither should be
described as a complete substitute for the other.

### Required hardening

- Introduce a checkpoint manifest binding state hash, database identity,
  runtime version, configuration fingerprint, abilities, and host realizers.
- Make checkpoint writes atomic and verify them before reporting success.
- Add restore qualification that proves a stopped run can resume from an
  exported checkpoint.
- Define schema migration and backward-compatibility policy for saved state and
  SQLite.

## 3. Subject Corpus and Workflow

### Current behavior

The subject corpus is canonical durable subject memory. Its current path model
is defined by
[learning_context_paths.py](learning_context_paths.py), with subject persistence
in [learning_context.py](learning_context.py).

The durable subject tree can contain:

```text
corpus/
  <subject_id>/
    context.json
    subject.md
    subject.typ
    sources/
    deltas/
    imports/
    indexes/
      aliases.json
      units.json
      imports.json
    derived/
      skills/
      exports/
    receipts/
      workflow_progress.json
    gather/
      sources/
      revisions/
      bundles/
      collections/
      indexes/
    itemization/
      session.json
      items/
      receipts/
    review_composition/
      composition.json
      items/
      receipts/
    decision_review/
      frame.json
      items/
    publications/
```

The exact directories present depend on which workflow stages have run.

Subject workflow persistence is implemented by
[subject_workflow.py](workstation/subject_core/src/workstation/subject/core/subject_workflow.py)
and
[subject_workflow_repository.py](workstation/subject_core/src/workstation/subject/core/subject_workflow_repository.py).
The service boundary is
[subject_workflow_api.py](workstation/subject_service/src/workstation/subject/service/subject_workflow_api.py).

`receipts/workflow_progress.json` persists governed workflow progress,
including review and publication gates, release-review progress, editor state,
pending research capture, comparison state, timeline material, and relevant
selection cursors. Therefore `SubjectProgress` is not merely in-memory state.

Pure client-view updates remain process-local by design, as described in the
workstation-session section. That distinction prevents UI state from silently
becoming subject truth.

`context.json`, `subject.md`, and `subject.typ` represent the maintained current
head. Source and delta records use record-per-ID files, but the filesystem does
not enforce append-only immutability if a caller writes the same ID again. The
current context content hash provides a snapshot identity token; it does not
create an immutable, named, recoverable subject version object.

`list_learning_contexts()` discovers subjects by scanning the corpus. There is
no implemented global last-worked-subject pointer, review queue, publication
queue, or recent-subject index.

### Continuity verdict

- The subject corpus is the canonical home of admitted subject truth.
- Governed per-subject workflow progress survives normal restart.
- The workflow does not depend solely on host memory.
- The repository can identify a current subject snapshot by content hash.
- The repository does not yet provide first-class subject version history or
  global operational resume indexes.

### Required hardening

- Create immutable `subject_version_id` records with explicit parentage.
- Record the exact ordered sources, deltas, projections, and review state in
  each subject version.
- Add rebuildable global indexes for recent work, review, and publication
  queues.
- Add an integrity checker capable of reconstructing indexes and projections
  from canonical records.
- Define atomic write behavior for current-head and workflow-progress updates.

## 4. Chat Transcript

### Current behavior

`MESSAGES.jsonl` is session-scoped and is appended by the workstation during
normal operation. It is durable provenance and user-facing history, but it is
not canonical subject truth.

Movement from chat into the subject corpus occurs through explicit research or
learning capture. The canonical host-side capture implementation is
[learning_capture.py](workstation/foundation_host/src/workstation/foundation/host/learning_capture.py).
Captured source and delta records can retain useful origin metadata such as a
session ID and prompt.

The linkage is not complete in every path. Assistant-markdown research capture
can use a timestamped `chat://` source reference without a stable message ID or
transcript position. The transcript itself does not currently assign a stable,
globally addressable identity to every message.

### Continuity verdict

- Chat history survives when the session root survives.
- Losing chat does not necessarily destroy already admitted subject truth.
- Chat cannot currently provide a complete, stable backlink for every admitted
  unit.
- Chat must remain separate from the subject corpus; admission is the governed
  boundary between conversation and subject truth.

### Required hardening

- Assign stable message IDs and transcript sequence positions.
- Persist capture references that identify the exact source messages or spans.
- Add a provenance query from an admitted unit back to its session and message
  material without making the transcript the owner of subject truth.

## 5. Publication Lineage

### Current behavior

Publication persistence is implemented by
[publication.py](publication.py), with projection, rendering, and validation in
[publication_projection.py](publication_projection.py),
[publication_render.py](publication_render.py), and
[publication_validation.py](publication_validation.py).

The durable publication tree is rooted at:

```text
corpus/<subject_id>/publications/<publication_id>/
```

It can contain:

```text
publication.json
compositions/
composition_revisions/
sections/
blocks/
claims/
sources/
entities/
xrefs/
reviews/
builds/<build_id>.json
outputs/<build_id>/...
```

The implementation provides:

- a stable deterministic `publication_id`
- a deterministic `build_id`
- `publication_snapshot_hash`
- `learning_context_snapshot_hash`
- renderer and template identifiers and versions
- build status and validation material
- archived composition revisions when a composition changes
- output roots associated with build IDs

This is reproducible build identity, not a complete release-management model.
Publication records under stable IDs can be rewritten. Repeating the same
deterministic build can reuse and overwrite its build record and output path,
so builds are not an immutable per-invocation history.

The workflow persists release-review booleans and gates in the subject's
`workflow_progress.json`. There is no separate typed release record, release
status, or `latest-release` reference. The current latest-publication lookup is
derived by scanning publication and build directories and comparing recorded
timestamps or filesystem modification time.

A build identifies the learning-context snapshot by hash. It does not point to
a first-class `subject_version_id`, because that object does not yet exist.

### Continuity verdict

- Publication material is durably and correctly rooted under its subject.
- Builds are reproducibly identified and can be inspected after restart.
- Composition history is better preserved than subject-head history.
- A successful build must not be represented as a recorded release.
- Release lineage and resumable release pointers are not yet first-class.

### Required hardening

- Link every build to an immutable subject version.
- Separate immutable build attempts from deterministic content identity if both
  concepts are needed.
- Introduce a typed release record with actor, approval, timestamp, build,
  validation result, and subject version.
- Add validated `latest-build`, `latest-success`, and `latest-release` refs.
- Prove that a historical released output can be reconstructed byte-for-byte or
  preserve the released bytes as immutable material.

## 6. Skill and Governance Home

### Current behavior

The workstation's admitted ability inventory is durable outside ordinary
session roots. Its location is resolved by
[skill_home.py](workstation/skills_planning/src/workstation/skills/planning/skill_home.py).

The default home is:

```text
$HOME/.workstation/workstation/skills/
```

`WORKSTATION_HOME` or an explicit SQLite path can relocate it. The home can
contain:

- `store.sqlite3`
- `exports/`
- `imports/`

This store is operationally important. Subject projections can mechanically
link skills into scope, but those links do not replace the admitted ability
records, governance decisions, and package material in the skill home.

Losing the skill home can therefore leave a subject with skill identifiers that
cannot be resolved or executed, even while the subject corpus and session roots
remain intact.

### Required hardening

- Include the skill home in documented backup and restore procedures.
- Record ability-package and schema compatibility in checkpoint manifests.
- Add restore tests that prove admitted abilities, governance state, and exports
  remain usable after migration to a clean host.
- Keep secret credentials and invocation-scoped authority outside portable
  public exports unless explicitly protected.

## 7. Blend World and Workflow

### Current behavior

Blend persistence is implemented in
[blend_world_store.py](blend_world_store.py) and
[blend_workflow_store.py](blend_workflow_store.py).

It can persist:

- `BLEND_WORLD.json`
- world `scratch/`
- world `output/`
- `BLEND_WORKFLOWS.json`
- `workflows/plans/*.json`
- `workflows/runs/*.json`
- session `BLEND_CONTEXT.json`
- session `BLEND_SESSION.json`

This permits world material, workflow plans, and run records to survive normal
process restart. It does not create an atomic checkpoint with workstation
session files, core state, a subject corpus, or publication material.

### Required hardening

- Document ownership and portability of world roots versus session roots.
- Add compatibility metadata and integrity verification to exported worlds and
  workflow runs.
- Define how a Blend workflow checkpoint references any associated core state,
  subject snapshot, skill inventory, and host realization set.

## Connection Rules

### Subject corpus and publication

This is a strong, intentional relationship. Publication is a governed derived
layer over selected subject truth. Publication must identify the exact subject
snapshot it used without becoming the owner of that subject truth.

### Workstation and all durable domains

The workstation coordinates sessions, clients, host operations, and workflow
views. It must not become the canonical store for core execution, subject,
publication, or ability admission simply because it can display them.

### Core execution and host realization

The core owns governed reduction state. A host owns available operation
realizers. An admitted ability can refer mechanically to a host operation, but
persisting the ability or core state does not guarantee that a future host
provides that operation. Recovery must verify compatibility before resume.

### Chat and subject admission

Chat is source material and provenance. Only explicit governed capture admits
material into subject truth. Recovery must preserve this distinction.

### Skills and subject scope

Subject-linked skill IDs place admitted abilities into subject reasoning scope.
The skill home remains the canonical home of the admitted ability inventory.
Both sides are needed to recover scoped behavior.

## Restart and Recovery Matrix

| Failure or restart | What survives | What is needed to resume correctly |
| --- | --- | --- |
| UI/client reconnect | Durable session and subject material | Reconstruct client session and selection state from authoritative projections |
| Workstation process restart | Session files, corpus, publications, skill home, Blend files | Reopen the same roots and rebuild live subscriptions and client views |
| Core process restart | SQLite and any explicitly saved state JSON | Load the matching state JSON and SQLite with compatible runtime, abilities, and realizers |
| Loss of state JSON | SQLite artifacts may remain | The exact in-flight reduction run is not guaranteed resumable |
| Loss of core SQLite | Saved state JSON may remain | Artifact/index records can be missing; exact resume is not guaranteed |
| Loss of session root | Subject and publication truth can remain | Transcript, session receipts, attachments, and task context are lost unless backed up elsewhere |
| Loss of subject corpus | Session/chat/core material can remain | Canonical subject and publication truth is lost |
| Loss of skill home | Subject skill links can remain | Admitted abilities and governance state may be unavailable |
| Partial filesystem write | Earlier files may remain readable | No repository-wide transactional recovery guarantee currently exists |
| Move to a new host | Portable files may survive | Paths, versions, schemas, configuration, abilities, and host realizers must be revalidated |

## Backup Sets

### Subject and publication backup

Preserve the complete corpus root, not only current `context.json` files. The
publication tree, source/delta records, workflow progress, indexes, and derived
material are all colocated under it.

Some indexes and projections are conceptually derivable, but the repository does
not currently provide one universal repair command that proves every derived
file can be rebuilt. Until such qualification exists, back up the complete tree.

### Core-run checkpoint

Preserve the state JSON and matching SQLite database together with a manifest
of runtime, configuration, ability, and host-realizer identities. Without that
bundle, describe retained material as audit evidence, not necessarily a
resumable run.

### Full workstation recovery

Depending on enabled features, preserve:

- all relevant workstation session roots
- the complete subject corpus root
- the workstation skill/governance home
- all core-run checkpoint bundles
- all external Blend world roots
- configuration needed to locate these roots
- protected secrets through an appropriate secret-management backup process,
  not by copying them into public session exports

These resources are not updated in one transaction. A backup taken while work
is actively mutating multiple stores can contain a cross-store inconsistent
point in time.

## Current Versioning Position

### Core execution

The core supports explicit state snapshots. It does not currently expose a
first-class parented run-checkpoint lineage tying state and SQLite together.

### Subject corpus

The subject has a maintained current head and content hashes. Source and delta
records support reconstruction and provenance, but immutable named subject
versions with parentage do not yet exist.

### Chat transcript

The transcript is an application-appended log. It lacks stable message IDs and
first-class version or branch semantics.

### Publication

Publication has stable content-derived identities, composition revisions, build
records, and outputs. It lacks immutable release records and explicit release
refs. It is closer to a versioned model than the subject head, but it is not a
complete release ledger.

### Skill/governance home

The inventory is durable in SQLite and import/export material. There is no
documented repository-wide version lineage or coordinated migration checkpoint
with subject and runtime stores.

### Blend

Plans and runs have durable identities. They are not transactionally versioned
with their session, world, subject, skill, or core dependencies.

## Operational Invariants

The following statements should remain true as continuity is hardened:

1. Session state does not silently become canonical subject truth.
2. Chat enters subject truth only through explicit governed admission.
3. Pure client-view state does not mutate subject workflow truth.
4. SQLite persistence does not imply that an unsaved core run can resume.
5. A content hash does not imply that an immutable subject version exists.
6. A successful publication build does not imply that a release was recorded.
7. An admitted ability does not imply that every future host supplies its
   declared operation realizer.
8. Derived indexes and projections never replace their canonical records.
9. A live event bus never substitutes for persisted receipts or state.
10. Backup success is not recovery success until restore is tested.

## Required Hardening Sequence

Continuity work should be additive and preserve existing file formats until
compatibility tests prove migration safety.

1. Freeze the current persistence contracts with fixture and restore tests.
2. Introduce a shared atomic-write utility for JSON and receipt updates where
   atomic replacement is appropriate.
3. Add core checkpoint manifests binding state JSON, SQLite, runtime,
   configuration, abilities, and host realizers.
4. Introduce immutable subject-version records while retaining the current-head
   files as compatibility projections.
5. Make publication builds refer to subject-version IDs in addition to current
   snapshot hashes.
6. Add typed release records and validated release refs without changing the
   meaning of existing successful builds.
7. Add rebuildable global subject indexes and work queues derived from canonical
   subject and publication material.
8. Add stable chat message IDs and exact capture backlinks.
9. Define and test skill-home and Blend export/restore contracts.
10. Qualify clean-host restoration across all enabled domains and enforce it in
    release gates.

## Bottom Line

The current codebase has substantial durable continuity, but not one unified
continuity store:

- the workstation persists operational sessions
- the core resumes only from explicitly saved state plus its compatible SQLite
  and execution environment
- the subject corpus persists governed subject workflow truth
- chat persists separate conversational provenance
- publication persists reproducible compositions, builds, and outputs, but not
  first-class releases
- the skill home persists admitted ability and governance material
- Blend persists worlds, plans, and runs

Normal process restart is supported across many journeys when the correct roots
are retained. Disaster recovery, immutable subject/release lineage, atomic
cross-store checkpoints, and clean-host restore qualification remain hardening
work. Those gaps must be stated explicitly rather than inferred as guarantees
from the presence of durable files.
