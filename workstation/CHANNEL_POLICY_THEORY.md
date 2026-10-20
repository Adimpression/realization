# Channel Policy Theory And Spec

Implementation choice:

- [CHANNEL_POLICY_IMPLEMENTATION.md](CHANNEL_POLICY_IMPLEMENTATION.md)

## Purpose

This document defines the **channel policy requirement** for Realized.

The goal is to make message ordering, buffering, acknowledgement, and release
behavior a **declared aspect** of the system rather than an accidental property
of one UI, one stream, or one handler.

This matters because Realized is moving toward:

- unary command APIs
- unary snapshot reads
- server-streaming watch APIs
- thin UI shells over a backend projection layer
- concurrent producers and consumers working over the same subject state

Without a separate channel policy layer, the system drifts into ad hoc queue
logic, stale repaint races, and inconsistent behavior across shells.

## Core Claim

API semantics and channel semantics are different concerns.

- The **API** says what can be asked, watched, or changed.
- The **channel policy** says how messages flow between producer and consumer.

Examples:

- `ApplySubjectAction` is an API command.
- `WatchSubjectWorkflow` is an API stream.
- `subject/smart-city-travel/draft` delivered in FIFO order is a channel policy.
- `subject/smart-city-travel/draft` delivered one message at a time after
  acknowledgement is a lock-step channel policy.

These must be modeled separately.

## Problem Statement

Realized already has concurrent behavior where this matters:

- subject workflow watch streams
- local UI selection and shaping changes
- background publication or analysis work
- event bus fan-out
- multiple phase projections over the same subject

If a producer emits newer and older projections without an explicit ordering
policy, or if a consumer applies them without a declared sequencing rule, then:

- stale state can repaint over newer local state
- keyboard interactions can appear frozen or jump unpredictably
- a later background refresh can clobber a more recent local action
- one shell can behave differently from another even when both use the same API

This is not primarily a transport bug. It is a missing channel contract.

## What We Need Precisely

Realized needs a reusable way to declare, for each logical channel:

- how messages are ordered
- whether newer messages may supersede older ones
- whether the consumer may process multiple messages in flight
- whether acknowledgement is required before the next release
- how reconnect/resume works
- how producer and consumer identify the same channel

That requirement must work across:

- in-process Python callers
- Textual
- future native clients
- future browser clients
- future mobile clients

It must not depend on:

- one specific shell
- one specific transport quirk
- one specific event loop implementation
- hidden assumptions in widget handlers

## What A Channel Policy Is

A channel policy is the declared behavior for one message stream, keyed by a
stable logical channel such as:

- `subject/{subject_id}`
- `subject/{subject_id}/gather`
- `subject/{subject_id}/itemize`
- `subject/{subject_id}/draft`
- `subject/{subject_id}/review`
- `subject/{subject_id}/publication`
- `activity`
- `operation/{operation_id}`

The policy governs:

- ordering
- acknowledgement
- release
- buffering
- backpressure
- overflow behavior
- barriers and flush points

## Ordering Modes

### 1. Unordered

Messages may arrive and be consumed in any convenient order.

Use when:

- order does not matter
- the newest complete snapshot simply replaces the old one
- stale intermediate states are harmless

Do not use when the consumer performs incremental stateful application.

### 2. FIFO

Messages are delivered in first-in-first-out order for a given channel key.

Use when:

- state transitions must be observed in causal order
- a UI or projection consumer applies messages incrementally
- a later projection must not be applied before an earlier one

FIFO guarantees order, but it does **not** require the consumer to acknowledge
each message before the next one is released.

### 3. Lock-Step

The next message is not released until the prior message is acknowledged.

Use when:

- each message must be fully processed before the next one is applied
- the consumer performs stateful, non-idempotent, or destructive work
- producer and consumer must remain synchronized

Lock-step is stronger than FIFO. It implies FIFO plus acknowledgement-based
release.

## Why FIFO And Lock-Step Are Different

FIFO solves:

- ordering
- causal visibility
- out-of-order repaint

Lock-step additionally solves:

- consumer overrun
- multiple in-flight state applications
- sequencing where each step depends on completed processing of the prior one

So:

- use FIFO when order is enough
- use lock-step when order plus completed consumption is required

## Producer And Consumer Independence

Both the API implementer and the API user should be able to work with channel
policy independently.

### Implementer Side

The producer can:

- emit sequence numbers
- serialize messages by channel key
- apply buffering and overflow policy
- require acknowledgement before release
- declare supported ordering modes

### User Side

The consumer can:

- route a source stream through a FIFO adapter before applying it
- consume one message at a time
- delay visual application until prior work completes
- choose stricter local discipline than the producer requires

### Important Constraint

Consumer-only FIFO can preserve **local application order**.

Producer-only FIFO can preserve **emission order**.

True lock-step requires cooperation from both sides, because the producer must
wait for acknowledgement before releasing the next message.

That means channel mode should be **negotiated or declared**, not assumed.

## Why This Must Be Declarative

If ordering behavior is hidden inside random handlers, then:

- it cannot be reasoned about globally
- it cannot be reused across APIs
- it cannot be tested consistently
- it cannot be switched per channel

Instead, the policy should be declared in one place and applied mechanically.

A policy declaration should be able to say, in effect:

- this channel is FIFO
- this channel is lock-step
- this channel allows one in-flight message
- this channel drops stale snapshots when superseded
- this channel requires explicit acknowledgement

That declaration should work whether the stream is:

- in-process
- server-streaming gRPC
- bridged through an event bus
- consumed by Textual
- consumed by another shell

## Why Realized Needs This

Realized now has the architectural conditions that make channel policy
necessary:

### 1. Thin Shells Over Backend Projections

The UI is becoming a projection consumer rather than the primary owner of
workflow state.

That means the shell must consume projected updates with clear sequencing rules.

### 2. Background Watch Streams

Server-side watch streams can race with local edits and selection changes.

If the consumer receives a delayed older projection after a local action, stale
state can overwrite newer state unless ordering and release policy are explicit.

### 3. Multiple Projections Over The Same Subject

One subject may have concurrent:

- Gather projection
- Itemize projection
- Draft projection
- Review projection
- Publication projection

Those projections need scoped channel keys and clear sequencing rules.

### 4. Incremental Workflows

Decision analysis, review approval, publication build, and source refresh all
create streams of meaningful intermediate state.

These are not just "latest snapshot" problems. Some need ordered progression.

### 5. Browser And Mobile Clients

Future clients will not all share the same event loop or UI toolkit.

So ordering policy cannot live as hidden Textual behavior. It must be expressed
at the API message level so web, native, and mobile clients consume the same
rules.

## Browser Client Implication

Channel policy does **not** solve browser-side structured concurrency by itself.

The browser still needs:

- version-aware reducers/providers
- cancellation of stale async work
- one in-flight apply path per active channel where needed
- latest-wins or FIFO discipline in local projection code

But declared channel policy still matters because it simplifies the client’s
input:

- one ordered source of projection events
- explicit sequence/version semantics
- cleaner reconnect/resume behavior
- less ad hoc producer-side inconsistency

So the channel policy layer solves **server/channel discipline**.
The browser still solves **local projection discipline**.

## Where It Is Needed First

The first high-value use sites are:

### Subject Workflow Watch Streams

Channel keys:

- `subject/{id}`
- `subject/{id}/gather`
- `subject/{id}/itemize`
- `subject/{id}/draft`
- `subject/{id}/review`
- `subject/{id}/publication`

Why:

- prevent stale phase projections from overwriting newer local state
- preserve user-visible movement and toggles in Draft/Review/Publication

Recommended mode:

- FIFO by default
- lock-step only if incremental consumption proves necessary

### Operation Progress

Channel keys:

- `operation/{id}`

Why:

- background analysis, publication build, and import/refresh work produce
  ordered progress events

Recommended mode:

- FIFO

### Activity Feed

Channel key:

- `activity`

Why:

- preserve chronological visibility of system events

Recommended mode:

- FIFO

### Cross-Shell Synchronization

Why:

- Textual and any future shell should consume the same ordered projections with
  the same declared rules

Recommended mode:

- FIFO

## Required Message Concepts

The reusable model must have at least these concepts:

- `channel_key`
- `sequence`
- `snapshot_version`
- `event_kind`
- `replace_vs_patch`
- `causation_id`
- `correlation_id`

If lock-step is later introduced, it must additionally support:

- `ack_mode`
- `max_in_flight`

These should be modeled in protobuf message fields, not hidden in transport
headers or UI code.

## Minimal Modes

- `UNORDERED`
- `FIFO`
- `LOCK_STEP`

## Minimal Overflow Policies

- `BLOCK`
- `DROP_OLDEST`
- `DROP_NEWEST`
- `COALESCE_TO_LATEST`

## Minimal Ack Modes

- `NONE`
- `EXPLICIT`

## Relation To Unary And Streaming APIs

Channel policy is compatible with the recommended API shape:

- unary commands for mutations
- unary reads for snapshots and bundles
- server-side streaming for watches

This means:

- bidi streaming is **not** required to start
- FIFO can be implemented over ordinary server-side streaming
- lock-step can be added later when acknowledgement is required

## Relation To Blend

Blend matters here because UI should remain a projection of meaning and state,
not the hidden owner of ordering policy.

In Blend terms:

- operators define lawful state change
- context defines the situation of the change
- interface is the projection
- channel policy governs how projection updates move between system parts

That makes channel policy a coordination concern, not a widget concern.

It should live beside transport and projection infrastructure, not inside a
single UI pane handler.

## Design Principle

**Ordering policy must be reusable infrastructure, not embedded UI folklore.**

If a consumer needs FIFO, it should be able to declare or route through FIFO.
If a producer requires lock-step, it should be able to declare or enforce it.
If both need stronger guarantees, the effective mode should be explicit.

## Non-Goals

This spec does **not** require:

- JetStream or another broker as the first implementation step
- bidi streaming as the first transport shape
- browser-side automatic concurrency management
- one universal policy for every stream

## Practical Consequence For Realized

The workstation backend should not rely on:

- incidental gRPC stream ordering alone
- incidental event-bus timing
- ad hoc queue suppression in one shell
- random persistence timing to make races disappear

Instead, the backend should expose ordered channels as a first-class capability.

## Short Rule

When ordering matters, use a declared channel policy.

When completed consumption matters, use lock-step.

When only observation matters, FIFO is usually enough.
