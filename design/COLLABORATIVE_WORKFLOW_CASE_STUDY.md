# Collaborative Multi-Actor Workflows as Terminal Encoding of Cross-Domain Design Mediation

Collaborative workflows are not merely single-user flows with comments added. They are systems in which **multiple actors must align on shared state, role ownership, sequencing, handoff, interruption, and accountability**. Their terminal vocabulary consists of assignment structures, shared boards, handoff packets, acknowledgment steps, escalation paths, and decision records.

---

# I. Mapping Form

The correct derivation is:

[
O \rightarrow I \rightarrow T \rightarrow V \rightarrow G \rightarrow E_{CW}
]

Where:

* (O) = joint objective
* (I) = collaborative intent
* (T) = task morphology
* (V) = interaction invariant
* (G) = collaboration obligation
* (E_{CW}) = collaborative-workflow embodiment

Collaborative workflow artifacts are therefore **not selected directly from the joint objective**.

They are selected from **interaction obligations under multiple roles**.

---

# II. Collaborative Artifact Families as Encodings

## 1. Shared State Artifacts

Shared state artifacts include work boards, queues, stage columns, timelines, and unified status surfaces.

### Upstream derivation

[
\text{Objective} \rightarrow \text{monitor / coordinate / verify shared progress} \rightarrow \text{shared-state obligation} \rightarrow \text{shared-state artifact}
]

### Use when the required obligation is:

* expose current collective status
* reveal where work is blocked
* preserve a common reference point
* reduce private state fragmentation
* support supervisory scanning

### Artifact mapping

| Interaction obligation         | Collaborative artifact       |
| ------------------------------ | ---------------------------- |
| Show work stages               | board / stage columns        |
| Show queue order               | ordered work queue           |
| Show temporal progression      | timeline                     |
| Show issue concentration       | grouped status view          |
| Preserve one shared reference  | canonical work surface       |

### Theory condition

Use shared state artifacts when:

[
I \in {\text{monitor}, \text{inspect}, \text{coordinate}}
]

and multiple actors must reason from the same state.

---

## 2. Role and Ownership Artifacts

Role and ownership artifacts include assignee markers, approver fields, watch lists, queue ownership, and authority labels.

### Upstream derivation

[
\text{Objective} \rightarrow \text{assign / verify responsibility} \rightarrow \text{ownership obligation} \rightarrow \text{role artifact}
]

### Use when the required obligation is:

* show who owns a task
* distinguish contributor from approver
* expose who may unblock work
* reduce ambiguity around responsibility
* preserve accountability under collaboration

### Artifact mapping

| Interaction obligation       | Collaborative artifact   |
| ---------------------------- | ------------------------ |
| Show active owner            | assignee field           |
| Show approval authority      | approver field           |
| Show passive visibility      | watcher / follower field |
| Show queue responsibility    | team owner marker        |
| Show escalation authority    | escalation owner field   |

### Theory condition

Use role and ownership artifacts when:

[
I \in {\text{coordinate}, \text{verify}, \text{confirm}}
]

and the workflow requires explicit authority structure.

---

## 3. Handoff Artifacts

Handoff artifacts include handoff packets, checklists, acknowledgments, prerequisite summaries, and restart markers.

### Upstream derivation

[
\text{Objective} \rightarrow \text{transfer / continue / resume} \rightarrow \text{handoff obligation} \rightarrow \text{handoff artifact}
]

### Use when the required obligation is:

* move work between actors safely
* preserve context during transfer
* reduce dropped work
* make acceptance explicit
* support continuation after interruption

### Artifact mapping

| Interaction obligation      | Collaborative artifact     |
| --------------------------- | -------------------------- |
| Transfer context            | handoff packet             |
| Confirm receipt             | acknowledgment step        |
| Preserve prerequisites      | checklist / readiness list |
| Preserve restart point      | resume marker              |
| Preserve supporting record  | attached rationale / notes |

### Theory condition

Use handoff artifacts when:

[
T \in {\text{sequential}, \text{collaborative}, \text{interrupt_driven}}
]

and work continuity crosses role boundaries.

---

## 4. Discussion and Decision Artifacts

Discussion and decision artifacts include comment threads, decision logs, rationale fields, issue markers, and approval records.

### Upstream derivation

[
\text{Objective} \rightarrow \text{compare / decide / justify} \rightarrow \text{decision obligation} \rightarrow \text{discussion artifact}
]

### Use when the required obligation is:

* compare alternatives
* justify a chosen path
* preserve why a decision was made
* distinguish discussion from binding decision
* support later review

### Artifact mapping

| Interaction obligation            | Collaborative artifact |
| --------------------------------- | ---------------------- |
| Open-ended discussion             | comment thread         |
| Binding decision                  | decision record        |
| Preserve rationale                | rationale field        |
| Mark blocking issue               | blocker marker         |
| Record approval                   | approval entry         |

### Theory condition

Use decision artifacts when:

[
I \in {\text{compare}, \text{select}, \text{confirm}, \text{learn}}
]

and collaboration requires durable justification, not just conversation.

---

## 5. Escalation and Interruption Artifacts

Escalation and interruption artifacts include SLA timers, escalation ladders, targeted alerts, blocked-state signals, and supervisor intervention paths.

### Upstream derivation

[
\text{Objective} \rightarrow \text{interrupt / reprioritize / unblock} \rightarrow \text{escalation obligation} \rightarrow \text{escalation artifact}
]

### Use when the required obligation is:

* surface blocked work
* bring attention to time-sensitive issues
* route intervention to the right actor
* distinguish local delay from system escalation
* prevent silent stagnation

### Artifact mapping

| Interaction obligation           | Collaborative artifact  |
| -------------------------------- | ----------------------- |
| Show time pressure               | SLA timer / aging mark  |
| Show blocked state               | blocker badge / flag    |
| Route intervention               | escalation path         |
| Alert the right party            | targeted notification   |
| Expose missed handoff            | overdue acknowledgment  |

### Theory condition

Use escalation artifacts when:

[
T \in {\text{interrupt_driven}, \text{supervisory}, \text{collaborative}}
]

and inaction must become visible before failure compounds.

---

## 6. Audit and History Artifacts

Audit and history artifacts include revision histories, ownership history, timeline logs, and change records.

### Upstream derivation

[
\text{Objective} \rightarrow \text{verify / recover / learn} \rightarrow \text{traceability obligation} \rightarrow \text{history artifact}
]

### Use when the required obligation is:

* reconstruct what changed
* identify responsibility across time
* support dispute resolution
* improve process after failure
* distinguish current truth from historical truth

### Artifact mapping

| Interaction obligation       | Collaborative artifact |
| ---------------------------- | ---------------------- |
| Reconstruct work history     | timeline log           |
| Show who changed ownership   | ownership history      |
| Show what changed            | revision log           |
| Support process learning     | postmortem record      |

### Theory condition

Use history artifacts when:

[
I \in {\text{verify}, \text{recover}, \text{learn}}
]

and the workflow persists across time, people, or disputes.

---

# III. Reverse Index: From Intent to Collaborative Embodiment

## Intent: Coordinate

| Obligation                  | Artifact                |
| --------------------------- | ----------------------- |
| Show shared state           | board / queue           |
| Show responsibility         | assignee / owner field  |
| Transfer work safely        | handoff packet          |
| Escalate blockage           | escalation path         |

---

## Intent: Select

| Obligation                  | Artifact                |
| --------------------------- | ----------------------- |
| Choose one path             | decision record         |
| Compare alternatives        | option set + rationale  |
| Bind a final choice         | approval record         |

---

## Intent: Verify

| Obligation                | Artifact                 |
| ------------------------- | ------------------------ |
| Check current owner       | ownership field          |
| Check current stage       | board status             |
| Check what changed        | revision log             |
| Check handoff acceptance  | acknowledgment marker    |

---

## Intent: Recover

| Obligation                 | Artifact                 |
| -------------------------- | ------------------------ |
| Reconstruct context        | history / rationale log  |
| Resume interrupted work    | restart marker           |
| Correct dropped handoff    | escalation artifact      |

---

# IV. Reverse Index: From Task Morphology to Collaborative Structure

## Sequential handoff task

Use:

* explicit stage flow
* handoff packet
* acknowledgment step
* restart markers

Use when:

[
T = \text{sequential}
]

and responsibility passes from one actor to another.

---

## Branching multi-path workflow

Use:

* queue segmentation
* option labeling
* explicit decision record
* visible blockers

Use when:

[
T = \text{branching}
]

and teams may route work differently under shared objectives.

---

## Supervisory workflow

Use:

* aggregate status board
* escalation ladder
* aging indicators
* approval records

Use when:

[
T = \text{supervisory}
]

and one role must monitor and intervene across many active items.

---

## Interrupt-driven collaborative workflow

Use:

* targeted alerts
* blocker flags
* overdue indicators
* resume-aware handoff records

Use when:

[
T = \text{interrupt_driven}
]

and external events or cross-team delays can reorder work.

---

# V. Artifact Choice Rules

## Rule 1: Comment thread vs decision record

Use a **comment thread** for exploration, clarification, or lightweight coordination.

Use a **decision record** when the outcome must be durable, referenceable, and binding.

Formal condition:

[
\text{DecisionRecord} \iff Commitment=\text{binding} \lor AuditNeed=\text{high}
]

---

## Rule 2: Assignment vs mention

Use a **mention** when visibility is desired without ownership.

Use an **assignment** when responsibility or expected action must be explicit.

Formal condition:

[
\text{Assignment} \iff Responsibility=\text{explicit} \land ExpectedAction=\text{yes}
]

---

## Rule 3: Shared board vs private work list

Use a **shared board** when multiple actors must reason from common state.

Use a **private list** only for actor-local organization that does not affect shared coordination.

Formal condition:

[
\text{SharedBoard} \iff StateDependency=\text{multi-actor}
]

---

## Rule 4: Direct handoff vs queue handoff

Use a **direct handoff** when one specific receiver must accept the work.

Use a **queue handoff** when any qualified actor may take the next item.

Formal condition:

[
\text{DirectHandoff} \iff Receiver=\text{specific}
]

[
\text{QueueHandoff} \iff Receiver=\text{role class}
]

---

## Rule 5: Escalation timer vs passive age display

Use a **passive age display** when lateness is informative but not yet actionable.

Use an **escalation timer** when age crossing a threshold must change attention or authority.

Formal condition:

[
\text{EscalationTimer} \iff TimeThreshold \Rightarrow AttentionShift \lor AuthorityShift
]

---

# VI. General Decision Procedure

For any collaborative objective:

## Step 1: Decompose the objective into intents

Example:

[
O=\text{resolve a service outage across teams}
]

becomes:

[
I={\text{detect}, \text{coordinate}, \text{assign}, \text{inspect}, \text{select}, \text{confirm}, \text{recover}}
]

---

## Step 2: Determine task morphology

[
T={\text{collaborative}, \text{branching}, \text{interrupt_driven}, \text{supervisory}}
]

---

## Step 3: Derive invariants

[
V={\text{state_awareness}, \text{mapping}, \text{feedback}, \text{recoverability}, \text{trustworthiness}, \text{responsiveness}}
]

---

## Step 4: Convert invariants into obligations

* every actor must see the current shared state
* ownership must be explicit
* handoff must preserve context
* blocking issues must become visible quickly
* binding decisions must be distinguishable from discussion

---

## Step 5: Select collaborative artifacts

* shared board
* assignee and approver fields
* handoff packet
* blocker markers
* decision record
* escalation timer
* revision history

---

# VII. Canonical Derivation Example

## Example: “Multiple teams must coordinate a production incident response”

[
O=\text{restore service safely and quickly}
]

[
I={\text{detect}, \text{monitor}, \text{coordinate}, \text{assign}, \text{select}, \text{confirm}, \text{recover}}
]

[
T=\text{collaborative + interrupt_driven + supervisory}
]

[
V={\text{state_awareness}, \text{prioritization}, \text{feedback}, \text{recoverability}, \text{trustworthiness}}
]

Collaborative encoding:

* shared incident board
* explicit owner and approver fields
* targeted escalation path
* blocker markers
* decision record for mitigation choices
* timeline log
* handoff packet for shift changes

---

# VIII. The Collaborative “Compiler” Rule

A collaborative workflow artifact should be chosen only when the following chain is valid:

[
\text{Artifact} \Leftarrow \text{Embodiment} \Leftarrow \text{Obligation} \Leftarrow \text{Invariant} \Leftarrow \text{Task Morphology} \Leftarrow \text{Intent} \Leftarrow \text{Objective}
]

So the design question is never:

> “Should we add comments here?”

It is:

> “Does this objective produce a durable coordination or decision obligation that requires persistent multi-actor traceability?”

If yes, use a decision record, history artifact, or handoff structure rather than relying on ad hoc conversation.

---

# IX. Final Statement

Collaborative workflow artifacts are the **shared-state and coordination embodiment vocabulary** of the theory.

The theory does not say:

[
\text{Team wants X} \rightarrow \text{Use artifact Y}
]

It says:

[
\text{Joint objective}
\rightarrow
\text{collaborative intent}
\rightarrow
\text{task morphology}
\rightarrow
\text{interaction invariant}
\rightarrow
\text{collaboration obligation}
\rightarrow
\text{collaborative-workflow artifact}
]

This is the proper bridge from multi-actor coordination need to concrete workflow form.
