# DI Open Governance Declaration

**Draft Specification**
**Status:** Draft
**Audience:** Builders, operators, auditors, publishers, adopters, and governors of Deterministic Intelligence systems

---

## Abstract

This document defines the minimum constitutional governance for an open Deterministic Intelligence ecosystem.

It assumes a simple architecture:

* a **core**
* a set of installable **skills**
* a **policy system** that governs skill admission and use
* a **runtime** that enforces policy
* a **trace system** that records what happened
* a **review and revocation system** that preserves accountability over time

This document is written for long-term use. It aims to express only the essential structure required for open, governed, extensible intelligence.

---

## 1. Purpose

The purpose of this declaration is to ensure that an open DI ecosystem remains:

* explicit in authority
* bounded in behavior
* inspectable before trust
* enforced during execution
* traceable after execution
* reviewable over time
* revocable when compromised
* accountable in all material actions

This declaration is not a product guide.
It is a constitutional minimum.

---

## 2. Scope

This declaration applies to:

* DI cores
* DI runtimes
* DI skills
* DI policies
* DI registries
* DI execution traces
* DI approvals
* DI audit records
* DI incident procedures

---

## 3. Definitions

### 3.1 Core

The minimal DI substrate with little or no default ability.

### 3.2 Skill

An installable, governed unit of behavior that extends the core.

### 3.3 Policy

A machine-interpretable rule set that governs installation, invocation, composition, data access, side effects, and approval.

### 3.4 Authority

Any granted power to read, write, execute, communicate, persist, invoke, approve, modify, export, or affect the outside world.

### 3.5 Invocation

A request to run a skill or cause a skill to participate in a chain of execution.

### 3.6 Composition

Any arrangement in which one skill invokes, delegates to, bundles with, or depends on another skill.

### 3.7 Trace

A structured record of what was requested, what policy applied, what was executed, what approvals occurred, and what effects resulted.

### 3.8 Replay

The ability to reconstruct and re-evaluate a past execution using preserved artifacts and preserved context.

### 3.9 Approval

A deliberate authorization step by a permitted authority.

### 3.10 Registry

A publication or distribution mechanism for skills and related governed artifacts.

### 3.11 Publisher

An entity that releases an artifact into the ecosystem.

### 3.12 Operator

An entity that installs, runs, supervises, or manages a DI system.

### 3.13 Auditor

An entity that reviews declarations, traces, approvals, incidents, or replay results.

---

## 4. Constitutional Principles

A conforming DI ecosystem MUST uphold the following principles.

### 4.1 Deny by default

No skill possesses authority unless that authority is explicitly declared and granted.

### 4.2 No hidden skill behavior

A skill shall not perform material undeclared behavior.

### 4.3 No hidden authority

A skill shall not use undeclared authority, whether directly, indirectly, or through composition.

### 4.4 No action without trace

Every material action shall produce trace evidence.

### 4.5 No trust without declaration

No skill shall be trusted without explicit declaration of intent, authority, side effects, and composition boundaries.

### 4.6 No extension without policy

No skill shall be installed, activated, invoked, or composed outside policy evaluation.

### 4.7 No silent escalation

Authority shall not expand through chaining, delegation, bundling, inheritance, or runtime drift without explicit policy approval.

### 4.8 Human accountability remains sovereign

High-impact actions shall remain attributable to a human, organization, or formally designated governing authority.

---

## 5. System Constitution

A DI system governed by this declaration SHALL be understood as a closed constitutional loop, not as a one-way pipeline.

```text
                           +----------------------+
                           |   HUMAN AUTHORITIES  |
                           | publisher / operator |
                           | approver / auditor   |
                           +----------+-----------+
                                      |
                                      v
+-------------+      +----------------+----------------+      +-------------+
|   REGISTRY  |----->| DECLARATIONS / POLICIES / RULES |<-----| INCIDENTS   |
|  + history  |      +----------------+----------------+      | + sanctions |
+------+------+                       |                       +------+------+ 
       |                              |                              ^
       |                              v                              |
       |                    +---------+---------+                    |
       |                    |   ADMISSION AND   |                    |
       |                    | ACTIVATION CHECK  |                    |
       |                    +---------+---------+                    |
       |                              |                              |
       v                              v                              |
+------+-------------------------------+----------------------+      |
|                        DI RUNTIME                           |      |
|                                                             |      |
|  +-------------+   +-------------+   +------------------+   |      |
|  |   SKILL A   |   |   SKILL B   |   |    SKILL N       |   |      |
|  +------+------+   +------+------+   +---------+--------+   |      |
|         \                 |                      /          |      |
|          \                |                     /           |      |
|           +---------------+--------------------+            |      |
|                           v                                 |      |
|                  EXECUTION MEDIATION                        |      |
|            (policy check before material effect)            |      |
+--------------------------+----------------------------------+      |
                           |                                         |
                           v                                         |
                  +--------+--------+                                |
                  | MATERIAL EFFECT |--------------------------------+
                  +--------+--------+
                           |
                           v
                  +--------+--------+
                  | TRACE / RECORD  |
                  +--------+--------+
                           |
                           v
                  +--------+--------+
                  | REVIEW / REPLAY |
                  +-----------------+
```

This loop is the essence:

* skills are declared
* declarations are governed
* governance is enforced
* enforcement produces trace
* trace enables review
* review enables sanction, correction, and revocation
* sanction and correction reshape future admission and activation

Nothing material lies outside this loop.

---

## 6. Governed Artifact Types

The ecosystem SHALL treat the following as governed artifacts:

* core artifacts
* skill artifacts
* policy artifacts
* approval artifacts
* trace artifacts
* replay artifacts
* registry records
* incident records

Every governed artifact MUST be:

* identifiable
* attributable
* integrity-protected
* versioned
* reviewable
* revocable where applicable

---

## 7. Skill Declaration

A skill SHALL NOT be admitted into a governed ecosystem unless it declares, at minimum:

* identity
* intent
* inputs
* outputs
* authorities requested
* data classes touched
* side effects
* persistence behavior
* invocation rights
* composition rights
* escalation rights
* approval requirements
* risk tier

A skill that cannot declare these properties is not governable.

### 7.1 Canonical skill declaration model

```text
+--------------------------------------------------+
|                    SKILL                         |
+--------------------------------------------------+
| Identity                                         |
| Intent                                           |
| Inputs                                           |
| Outputs                                          |
| Requested Authorities                            |
| Data Classes                                     |
| Side Effects                                     |
| Persistence Behavior                             |
| Invocation Rights                                |
| Composition Rights                               |
| Escalation Rights                                |
| Approval Requirements                            |
| Risk Tier                                        |
+--------------------------------------------------+
```

Readable implementation is useful.
Declared behavior is mandatory.

---

## 8. Authority Model

Authority SHALL be explicit, granular, bounded, and deny-by-default.

At minimum, authority SHALL distinguish among:

* read
* write
* execute
* communicate
* persist
* invoke
* approve
* modify
* export
* escalate

Each authority grant SHALL also specify its bounds:

* scope
* target
* context
* duration
* triggering conditions
* approval class

### 8.1 Authority evaluation loop

```text
             +----------------------+
             |  REQUESTED ACTION    |
             +----------+-----------+
                        |
                        v
             +----------+-----------+
             | DECLARED BY SKILL ?  |
             +----+-------------+---+
                  |             |
                 no            yes
                  |             |
                  v             v
                DENY   +--------+--------+
                       | ALLOWED BY      |
                       | POLICY ?        |
                       +----+--------+---+
                            |        |
                           no       yes
                            |        |
                            v        v
                          DENY  +----+----------------+
                                | REQUIRES APPROVAL ? |
                                +----+-----------+----+
                                     |           |
                                    yes         no
                                     |           |
                                     v           v
                           +---------+--+     ENFORCE
                           | APPROVED ? |        |
                           +----+---+---+        v
                                |   |         TRACE
                               no  yes
                                |   |
                                v   v
                              HOLD ENFORCE
                                     |
                                     v
                                   TRACE
```

A skill does not become powerful because it exists.
It becomes powerful only through declared and granted authority.

---

## 9. Admission and Activation

Admission and activation are distinct.

A skill may be:

* published
* reviewed
* admitted
* installed
* activated
* invoked

Each step is governed.

### 9.1 Admission loop

```text
PUBLISH
   |
   v
REVIEW
   |
   +------> REJECT
   |
   v
ADMIT
   |
   +------> QUARANTINE
   |
   v
INSTALL
   |
   +------> HOLD
   |
   v
ACTIVATE
   |
   v
INVOKE
```

A skill SHALL NOT move from one stage to the next without the required checks for that stage.

At minimum, admission SHALL consider:

* complete declaration
* integrity
* dependencies
* risk tier
* policy compatibility
* review status

At minimum, activation SHALL consider:

* current policy state
* current approval state
* current trust state
* current incident state
* current operator intent

---

## 10. Runtime Mediation

A governed DI runtime MUST mediate all material skill execution.

No skill SHALL directly convert existence into effect.

Runtime mediation MUST include:

* authority checks
* policy checks
* approval checks
* composition checks
* data-boundary checks
* side-effect checks
* trace generation
* ability to deny, pause, or stop execution

### 10.1 Runtime mediation model

```text
+---------+      +-----------+      +-----------+      +---------+
|  SKILL  |----->| MEDIATOR  |----->|  EFFECT   |----->| TRACE   |
+----+----+      +-----+-----+      +-----+-----+      +----+----+
     ^                 |                  |                  |
     |                 v                  v                  |
     |             POLICY LOOP        RUNTIME LOOP           |
     |                 |                  |                  |
     +-----------------+------------------+------------------+
```

The runtime is not merely an executor.
It is the enforcing edge of the constitution.

---

## 11. Skill Composition Governance

A DI ecosystem MUST govern compositions, not just isolated skills.

Composition governance SHALL consider:

* which skills may invoke which other skills
* whether authority grows when skills are chained
* whether a chain causes hidden side effects
* whether a bundle becomes more powerful than its members appear alone
* whether cycles or recursion create drift
* whether delegation bypasses approval or policy

### 11.1 Composition loop

```text
          +---------+       invokes       +---------+
          | SKILL A |-------------------->| SKILL B |
          +----+----+                     +----+----+
               ^                               |
               |                               |
               |                               v
               |                         +-----+----+
               |                         | SKILL C  |
               |                         +-----+----+
               |                               |
               +----------- feedback ----------+
```

A conforming system MUST ask:

* is each skill allowed alone?
* is the chain allowed as a whole?
* does the chain create new authority?
* does the loop create persistence, escalation, or drift?

If the system cannot answer these questions, composition is not governed.

---

## 12. Data Governance

Every governed DI system SHALL classify data and bind skills to those classes.

At minimum, the ecosystem SHOULD distinguish among:

* public
* internal
* sensitive
* regulated
* secret
* audit-only
* derived

Every skill SHALL declare:

* which data classes it may access
* for what purpose
* under what conditions
* for how long
* whether export is permitted
* whether transformation is permitted
* whether persistence is permitted

### 12.1 Data governance loop

```text
DATA REQUEST
    |
    v
DATA CLASS IDENTIFIED
    |
    v
SKILL DECLARATION CHECK
    |
    v
POLICY CHECK
    |
    v
APPROVAL CHECK IF REQUIRED
    |
    v
ALLOW OR DENY
    |
    v
TRACE
```

No skill may touch undeclared or disallowed data classes.

---

## 13. Approval Governance

Some actions SHALL require explicit approval.

A conforming ecosystem MUST define approval classes.
A practical model MAY include:

* automatic
* operator-approved
* multi-party approved
* organization-approved
* emergency-approved
* prohibited

The following SHOULD NOT default to automatic:

* policy change
* high-risk skill install
* high-risk skill activation
* sensitive export
* external human contact
* resource commitment
* self-extension
* authority escalation
* critical-system interaction

### 13.1 Approval loop

```text
REQUEST
   |
   v
CLASSIFY ACTION
   |
   +----> automatic ----------+
   |                          |
   +----> operator ---------- |
   |                          |
   +----> multi-party ------  |
   |                          |
   +----> prohibited -------> DENY
   |
   v
APPROVAL RESOLVED
   |
   v
ENFORCE OR HOLD
   |
   v
TRACE
```

Approval is not a side note.
Approval is a constitutional gate.

---

## 14. Trace Constitution

Every material event SHALL produce structured trace evidence.

A trace MUST answer:

* who initiated
* what was requested
* which skill acted
* what declaration was in force
* what policy was in force
* what authority was requested
* what authority was granted
* what approvals occurred
* what data classes were touched
* what side effects occurred
* what composition chain occurred
* what result was produced

### 14.1 Trace loop

```text
REQUEST
  |
  v
DECISION
  |
  v
EXECUTION
  |
  v
EFFECT
  |
  v
TRACE
  |
  v
REVIEW
  |
  +------> SANCTION / REVOKE / CORRECT
  |
  +------> ACCEPT / LEARN / IMPROVE
```

A trace is not merely a log.
It is constitutional evidence.

---

## 15. Replay Constitution

A governed DI system MUST support replay for meaningful review.

Replay SHALL make it possible to reconstruct:

* the request
* the skill version
* the declaration state
* the policy state
* the approval state
* the data classification state
* the composition path
* the observed outcome

### 15.1 Replay model

```text
PAST EXECUTION
   |
   +--> request
   +--> declarations
   +--> policy state
   +--> approvals
   +--> skill versions
   +--> chain structure
   +--> outcome
   |
   v
REPLAYABLE REVIEW
```

Replay exists so that review is real, not rhetorical.

---

## 16. Risk Tiers

Every skill SHALL be assigned a risk tier.

A practical tier model MAY be:

### Tier 0 — Passive

No external effect. Read-only or interpretation-only behavior.

### Tier 1 — Bounded Transform

Transforms declared local input into declared local output.

### Tier 2 — Connected

Communicates externally within narrow bounds.

### Tier 3 — Sensitive

Touches sensitive data, credentials, or live systems.

### Tier 4 — Agentic

Performs multi-step, delegated, persistent, or chained behavior.

### Tier 5 — Sovereign

May alter policy, alter skill power, commit resources, or affect critical institutions or systems.

### 16.1 Risk ladder

```text
Tier 0 -> Tier 1 -> Tier 2 -> Tier 3 -> Tier 4 -> Tier 5
  low                                                     high
 risk                                                    impact
```

Higher tiers SHALL imply stricter:

* review
* admission
* activation
* approval
* runtime constraint
* trace retention
* incident response

---

## 17. Registry Governance

If a registry exists, it is part of the trust boundary.

A governed registry SHALL support:

* publisher identity
* artifact history
* declaration visibility
* risk visibility
* review state visibility
* quarantine
* withdrawal
* incident signaling

### 17.1 Registry loop

```text
PUBLISHER --> REGISTRY --> OPERATOR --> RUNTIME --> TRACE --> REVIEW
                  ^                                         |
                  |                                         |
                  +----------- INCIDENT / WITHDRAWAL -------+
```

A registry is not merely a marketplace.
It is a constitutional surface.

---

## 18. Incident Governance

A conforming ecosystem MUST assume compromise, misuse, failure, and drift are possible.

It MUST support:

* incident detection
* incident classification
* containment
* skill disablement
* approval suspension
* trust suspension
* forensic preservation
* review
* remediation
* restoration or revocation

### 18.1 Incident loop

```text
DETECT
  |
  v
CLASSIFY
  |
  v
CONTAIN
  |
  v
PRESERVE EVIDENCE
  |
  v
REVIEW
  |
  +----> REMEDIATE --> RESTORE
  |
  +----> REVOKE ----> BLOCK
```

An open ecosystem without incident governance is not mature enough for public trust.

---

## 19. Human Roles

A conforming ecosystem MUST distinguish among roles.

At minimum:

* author
* publisher
* reviewer
* operator
* approver
* auditor
* responder

The ecosystem MUST make it clear which role is accountable for:

* publication
* admission
* activation
* operation
* approval
* review
* incident response

### 19.1 Human accountability loop

```text
AUTHOR -> PUBLISHER -> REVIEWER -> OPERATOR -> APPROVER -> AUDITOR -> RESPONDER
   ^                                                                   |
   +--------------------------- governance feedback -------------------+
```

Human accountability is not replaced by DI.
It is made more explicit by DI.

---

## 20. Minimal Conformance

A system SHALL NOT claim conformance unless it provides all of the following:

1. governed skill identity
2. explicit skill declaration
3. deny-by-default authority model
4. policy evaluation before admission and execution
5. runtime mediation
6. structured trace emission
7. replayable review path
8. risk-tier handling
9. revocation capability
10. incident procedures

These are the minimum constitutional conditions.

---

## 21. Minimal Adoption Profile

For rapid adoption, a minimal governed DI profile SHOULD implement:

* skill declaration
* deny-by-default authority
* admission review
* runtime mediation
* trace emission
* replay
* risk tiers
* revocation
* incident response

### 21.1 Minimal adoption profile diagram

```text
+------------------------------------------------------+
|              MINIMAL GOVERNED DI PROFILE             |
+------------------------------------------------------+
| Skill Declaration                                    |
| Authority Boundaries                                 |
| Policy Before Admission                              |
| Policy Before Execution                              |
| Runtime Mediation                                    |
| Trace Evidence                                       |
| Replayable Review                                    |
| Risk Tiers                                           |
| Revocation                                           |
| Incident Response                                    |
+------------------------------------------------------+
```

This profile is intentionally small enough to adopt and strong enough to matter.

---

## 22. Long-Term Constitutional Chain

A DI ecosystem intended for long life SHOULD obey this chain:

```text
SKILL
  |
  v
DECLARATION
  |
  v
GOVERNANCE
  |
  v
ENFORCEMENT
  |
  v
TRACE
  |
  v
REVIEW
  |
  v
REVOCATION
  |
  v
FUTURE ADMISSION
```

And because the system is living, not static, the true structure is a loop:

```text
+-------------+
|    SKILL    |
+------+------+ 
       |
       v
+------+------+
| DECLARATION |
+------+------+ 
       |
       v
+------+------+
| GOVERNANCE  |
+------+------+ 
       |
       v
+------+------+
| ENFORCEMENT |
+------+------+ 
       |
       v
+------+------+
|   TRACE     |
+------+------+ 
       |
       v
+------+------+
|   REVIEW    |
+------+------+ 
       |
       v
+------+------+
| REVOCATION  |
| / CORRECTION|
+------+------+ 
       |
       v
+------+------+
| FUTURE      |
| ADMISSION   |
+-------------+
```

If this loop is broken, governance becomes symbolic rather than real.

---

## 23. Final Declaration

We declare that open Deterministic Intelligence SHALL be governed by:

* explicit skill declaration
* bounded authority
* policy before effect
* runtime enforcement
* structured trace
* replayable review
* revocable trust
* enduring accountability

We reject:

* hidden skill behavior
* silent authority
* unguided extension
* unreviewable execution
* irreversible trust

We affirm:

* openness requires constitution
* skills require declaration
* declaration requires governance
* governance requires enforcement
* enforcement requires trace
* trace requires review
* review requires revocation
* revocation must influence future trust

Therefore, any open DI ecosystem intended for broad public trust SHOULD adopt this declaration, or a stricter compatible successor, as its constitutional foundation.~~
