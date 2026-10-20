# High-Risk Operational Systems as Terminal Encoding of Cross-Domain Design Mediation

High-risk operational systems are not ordinary interfaces with higher visual seriousness. They are systems in which **state awareness, constraint, confirmation, recoverability, and accountability** must be encoded under consequence. Their terminal vocabulary consists of control surfaces, alarms, interlocks, procedures, overrides, logs, and supervisory authorization structures.

---

# I. Mapping Form

The correct derivation is:

[
O \rightarrow I \rightarrow T \rightarrow V \rightarrow G \rightarrow E_{HR}
]

Where:

* (O) = operator objective
* (I) = operational intent
* (T) = task morphology
* (V) = interaction invariant
* (G) = operational obligation
* (E_{HR}) = high-risk operational embodiment

Operational controls are therefore **not selected directly from the operator objective**.

They are selected from **obligations derived under risk and constraint**.

---

# II. High-Risk Artifact Families as Encodings

## 1. State Display Artifacts

State display artifacts include overview panels, dedicated gauges, trend traces, condition tables, and equipment status boards.

### Upstream derivation

[
\text{Objective} \rightarrow \text{detect / monitor / verify} \rightarrow \text{state-awareness obligation} \rightarrow \text{state display artifact}
]

### Use when the required obligation is:

* show current system condition
* distinguish normal from abnormal state
* expose whether preconditions hold
* preserve awareness over time
* support supervisory scanning

### Artifact mapping

| Interaction obligation         | High-risk artifact             |
| ------------------------------ | ------------------------------ |
| Show current operating state   | Primary status panel           |
| Show variable magnitude        | Gauge / meter / trend trace    |
| Show equipment readiness       | Readiness board / state table  |
| Preserve temporal context      | Trend history                  |
| Distinguish safe from unsafe   | Condition state coding         |

### Theory condition

Use state display artifacts when:

[
I \in {\text{detect}, \text{monitor}, \text{verify}}
]

and safe action depends on accurate state interpretation.

---

## 2. Alarm and Salience Artifacts

Alarm and salience artifacts include warning channels, annunciators, escalation indicators, alarm summaries, and consequence-graded alert structures.

### Upstream derivation

[
\text{Objective} \rightarrow \text{detect / interrupt / prioritize} \rightarrow \text{salience obligation} \rightarrow \text{alarm artifact}
]

### Use when the required obligation is:

* interrupt attention appropriately
* distinguish severity levels
* surface changed risk state
* prevent silent hazardous drift
* prioritize response under load

### Artifact mapping

| Interaction obligation     | High-risk artifact          |
| -------------------------- | --------------------------- |
| Signal abnormal condition  | Alarm annunciator           |
| Signal severity            | Consequence-graded alert    |
| Preserve alarm queue       | Alarm summary list          |
| Escalate unresolved issue  | Escalation indicator        |
| Distinguish transient vs sustained hazard | persistent alarm state |

### Theory condition

Use alarm and salience artifacts when:

[
V \in {\text{salience}, \text{prioritization}, \text{state_awareness}}
]

and the cost of missed detection is high.

---

## 3. Command and Actuation Artifacts

Command and actuation artifacts include start/stop controls, setpoint controls, guarded switches, mode selectors, and explicitly separated action channels.

### Upstream derivation

[
\text{Objective} \rightarrow \text{trigger / modify / commit} \rightarrow \text{actuation obligation} \rightarrow \text{command artifact}
]

### Use when the required obligation is:

* initiate an operation
* stop an unsafe progression
* adjust an operating state
* separate safe from unsafe commands
* preserve deliberate commitment

### Artifact mapping

| Interaction obligation       | High-risk artifact       |
| ---------------------------- | ------------------------ |
| Start or stop operation      | Dedicated start/stop control |
| Prevent accidental trigger   | Guarded control          |
| Choose operating mode        | Mode selector            |
| Change controlled value      | Setpoint control         |
| Emergency interruption       | Emergency stop channel   |

### Theory condition

Use command artifacts when:

[
I \in {\text{trigger}, \text{modify}, \text{confirm}}
]

and the system must distinguish observation from commitment.

---

## 4. Confirmation and Interlock Artifacts

Confirmation and interlock artifacts include permit checks, enable conditions, dual confirmation, supervisory cosign, lockouts, and consequence-aware confirmation sequences.

### Upstream derivation

[
\text{Objective} \rightarrow \text{verify / confirm / constrain} \rightarrow \text{interlock obligation} \rightarrow \text{confirmation artifact}
]

### Use when the required obligation is:

* prevent unsafe execution
* require precondition satisfaction
* require deliberate commitment
* require role-specific approval
* distinguish authorized override from ordinary action

### Artifact mapping

| Interaction obligation           | High-risk artifact        |
| -------------------------------- | ------------------------- |
| Require readiness preconditions  | Enable interlock          |
| Require explicit consequence review | confirmation step      |
| Require second role approval     | supervisory cosign        |
| Prevent disallowed actuation     | lockout                   |
| Permit exceptional override      | controlled override path  |

### Theory condition

Use confirmation and interlock artifacts when:

[
V \in {\text{constraint}, \text{recoverability}, \text{trustworthiness}}
]

and action must be constrained before execution, not only judged afterward.

---

## 5. Procedure and Checklist Artifacts

Procedure and checklist artifacts include startup sequences, shutdown sequences, verification checklists, exception procedures, and handoff check records.

### Upstream derivation

[
\text{Objective} \rightarrow \text{sequence / verify / recover} \rightarrow \text{procedural obligation} \rightarrow \text{procedure artifact}
]

### Use when the required obligation is:

* preserve correct order
* reduce omission under pressure
* externalize memory burden
* standardize coordination
* support recovery after interruption

### Artifact mapping

| Interaction obligation        | High-risk artifact         |
| ----------------------------- | -------------------------- |
| Enforce ordered progression   | Checklist / procedure      |
| Preserve restart point        | Step-tracked procedure     |
| Verify readiness              | pre-operation checklist    |
| Standardize emergency action  | emergency procedure card   |
| Preserve shift continuity     | handoff checklist          |

### Theory condition

Use procedure artifacts when:

[
T \in {\text{sequential}, \text{interrupt_driven}, \text{emergency}, \text{supervisory}}
]

and order or omission burden is safety-relevant.

---

## 6. Recovery and Audit Artifacts

Recovery and audit artifacts include reversal controls, rollback states, event logs, action histories, override justifications, and post-event review records.

### Upstream derivation

[
\text{Objective} \rightarrow \text{recover / explain / review} \rightarrow \text{recoverability and trace obligation} \rightarrow \text{audit artifact}
]

### Use when the required obligation is:

* support safe correction
* preserve action traceability
* explain why a command was accepted or blocked
* support post-event review
* maintain trust in the control regime

### Artifact mapping

| Interaction obligation      | High-risk artifact       |
| --------------------------- | ------------------------ |
| Reverse safe action         | rollback control         |
| Preserve operator trace     | action log               |
| Preserve override rationale | justification record     |
| Support post-event review   | event timeline           |
| Explain block state         | block reason display     |

### Theory condition

Use recovery and audit artifacts when:

[
I \in {\text{recover}, \text{verify}, \text{learn}}
]

and the consequences of error require reconstruction and accountability.

---

# III. Reverse Index: From Intent to High-Risk Embodiment

## Intent: Detect

| Obligation                | Artifact                  |
| ------------------------- | ------------------------- |
| Notice abnormal condition | Alarm / annunciator       |
| Notice readiness failure  | readiness state display   |
| Notice drift over time    | trend trace               |

---

## Intent: Verify

| Obligation                  | Artifact                  |
| --------------------------- | ------------------------- |
| Check preconditions         | checklist / enable state  |
| Check current operating mode| mode display              |
| Check consequence boundary  | interlock summary         |

---

## Intent: Trigger

| Obligation              | Artifact                    |
| ----------------------- | --------------------------- |
| Start operation         | dedicated command control   |
| Stop operation          | stop control / E-stop       |
| Trigger risky act       | guarded actuation           |

---

## Intent: Confirm

| Obligation                | Artifact                    |
| ------------------------- | --------------------------- |
| Require deliberate commit | confirmation step           |
| Require second authority  | supervisory cosign          |
| Permit override           | explicit override channel   |

---

## Intent: Recover

| Obligation                    | Artifact                   |
| ----------------------------- | -------------------------- |
| Reverse or stabilize state    | rollback / safe-state path |
| Explain what happened         | event log                  |
| Resume after interruption     | step-tracked procedure     |

---

# IV. Reverse Index: From Task Morphology to Operational Structure

## Continuous supervisory task

Use:

* persistent state display
* prioritized alarms
* trend views
* stable control locations

Use when:

[
T = \text{continuous} \lor T = \text{supervisory}
]

and awareness must be maintained over time.

---

## Sequential high-consequence task

Use:

* ordered checklist
* explicit precondition verification
* guarded actuation
* completion confirmation

Use when:

[
T = \text{sequential}
]

and omission risk is high.

---

## Interrupt-driven alarm response

Use:

* salience-graded alarms
* acknowledgment state
* drill-down path to cause
* guided recovery procedure

Use when:

[
T = \text{interrupt_driven}
]

and the system initiates attention demand.

---

## Emergency task

Use:

* unmistakable stop path
* simplified action grammar
* constrained alternative set
* explicit state confirmation

Avoid:

* hidden actions
* mode ambiguity
* delayed or indirect feedback

---

# V. Artifact Choice Rules

## Rule 1: Soft warning vs hard interlock

Use a **soft warning** when the operator should remain free to proceed under judgment.

Use a **hard interlock** when proceeding without changed facts is unacceptable.

Formal condition:

[
\text{HardInterlock} \iff ConsequenceSeverity=\text{high} \land OperatorDiscretion=\text{insufficient}
]

---

## Rule 2: Single confirmation vs supervisory cosign

Use **single confirmation** when one role can legitimately bear the decision.

Use **supervisory cosign** when authority or accountability must be shared.

Formal condition:

[
\text{SupervisoryCosign} \iff Authority=\text{distributed} \lor Consequence=\text{escalated}
]

---

## Rule 3: Trend view vs snapshot view

Use a **snapshot view** when only the current condition matters.

Use a **trend view** when safe judgment depends on direction, stability, or drift.

Formal condition:

[
\text{TrendView} \iff StateInterpretation=\text{temporal}
]

---

## Rule 4: Checklist vs direct action

Use **direct action** when the task is simple, infrequent omission is harmless, and the preconditions are already obvious.

Use a **checklist** when order, omission, or interruption can create hazard.

Formal condition:

[
\text{Checklist} \iff OmissionRisk=\text{material} \lor RestartNeed=\text{likely}
]

---

## Rule 5: Override path vs ordinary action path

An **override path** must never be indistinguishable from the ordinary action path.

Formal condition:

[
\text{Override} \Rightarrow \text{separate grammar} \land \text{traceability} \land \text{extra constraint}
]

---

# VI. General Decision Procedure

For any high-risk operational objective:

## Step 1: Decompose the objective into intents

Example:

[
O=\text{start chemical transfer safely}
]

becomes:

[
I={\text{detect}, \text{verify}, \text{trigger}, \text{confirm}, \text{monitor}, \text{recover}}
]

---

## Step 2: Determine task morphology

[
T={\text{sequential}, \text{continuous}, \text{interrupt_driven}, \text{high-risk}}
]

---

## Step 3: Derive invariants

[
V={\text{salience}, \text{feedback}, \text{constraint}, \text{recoverability}, \text{state_awareness}, \text{trustworthiness}}
]

---

## Step 4: Convert invariants into obligations

* readiness must be visible before actuation
* unsafe commands must be blocked before execution
* alarms must be severity-graded
* operators must be able to reconstruct what happened
* emergency interruption must remain available and legible

---

## Step 5: Select high-risk artifacts

* state display
* readiness interlocks
* guarded start command
* consequence-aware confirmation
* alarm summary
* recovery procedure
* audit log

---

# VII. Canonical Derivation Example

## Example: “Operator must initiate a hazardous process without violating readiness conditions”

[
O=\text{initiate process safely}
]

[
I={\text{detect}, \text{verify}, \text{trigger}, \text{confirm}, \text{monitor}, \text{recover}}
]

[
T=\text{sequential + continuous + interrupt_driven}
]

[
V={\text{state_awareness}, \text{constraint}, \text{feedback}, \text{salience}, \text{recoverability}}
]

Operational encoding:

* readiness panel
* guarded command control
* pre-actuation checklist
* hard interlock on unsafe conditions
* alarm summary
* event log
* emergency stop path

---

# VIII. The High-Risk “Compiler” Rule

A high-risk operational artifact should be chosen only when the following chain is valid:

[
\text{Artifact} \Leftarrow \text{Embodiment} \Leftarrow \text{Obligation} \Leftarrow \text{Invariant} \Leftarrow \text{Task Morphology} \Leftarrow \text{Intent} \Leftarrow \text{Objective}
]

So the design question is never:

> “Should we add another confirmation dialog?”

It is:

> “Does this action require an additional commitment constraint because consequence severity exceeds what one-step actuation can safely support?”

If yes, add the confirmation or interlock structure.

---

# IX. Final Statement

High-risk operational artifacts are the **constraint and control embodiment vocabulary** of the theory.

The theory does not say:

[
\text{Operator wants X} \rightarrow \text{Use artifact Y}
]

It says:

[
\text{Operational objective}
\rightarrow
\text{operational intent}
\rightarrow
\text{task morphology}
\rightarrow
\text{interaction invariant}
\rightarrow
\text{operational obligation}
\rightarrow
\text{high-risk operational artifact}
]

This is the proper bridge from safe coordinated action to concrete control-system form.
