# Channel Policy Implementation

Spec:

- [CHANNEL_POLICY_THEORY.md](CHANNEL_POLICY_THEORY.md)

## Decision

Realized will implement channel policy first with:

- unary commands
- unary snapshot reads
- server-side streaming watch APIs
- protobuf event envelopes that carry channel semantics in the message body

Realized will **not** introduce JetStream as the first implementation step.

Realized will **not** require bidi streaming as the first transport step.

## Why This Choice

This is the smallest implementation that satisfies the current product need.

What we need right now is:

- ordered subject workflow watch delivery
- versioned projection updates
- browser-compatible streaming
- an API contract that is not coupled to Textual
- a clear place to add lock-step later if we actually need it

This choice gives that without forcing:

- broker infrastructure
- multi-consumer durable replay machinery
- a session-channel protocol before it is needed

## What We Considered

### 1. Connect + JetStream

This remains a strong later option when durable replay and independent consumer
positions become necessary.

Why it is not first:

- it adds infrastructure before the current workstation problem requires it
- the current pain is projection ordering and stale repaint, not broker absence
- the browser still needs local projection discipline either way

### 2. Bidi Streaming

Why it is not first:

- the current workstation shape is mostly unary commands plus watch streams
- web support is simpler with unary plus server-streaming
- lock-step can be added later with explicit ack APIs if needed

## What This Means In Practice

### API Shape

Keep:

- unary commands for mutations
- unary reads for snapshots and bundles
- server-side streaming for watches

Examples:

- `ApplySubjectAction`
- `GetSubjectPhaseView`
- `GetSubjectControlBundle`
- `GetSubjectPaneBundle`
- `WatchSubjectWorkflow`
- `WatchActivity`
- `WatchOperation`

### Message Shape

Channel semantics must live in the protobuf message payload, not in gRPC
headers or trailers.

Each streamed message should carry at least:

- `channel_key`
- `sequence`
- `snapshot_version`
- `event_kind`
- `replace_vs_patch`
- `causation_id`
- `correlation_id`

If lock-step is later added, then also:

- `ack_mode`
- `max_in_flight`

## Why Not Use gRPC Metadata For This

Transport metadata is not the right place for per-event channel semantics.

Headers and trailers are transport-level.
Channel policy is message-level.

So:

- ordering and version semantics belong in protobuf fields
- clients should be able to inspect them from generated code directly
- tests should assert them at the message level

## Browser / Native / Mobile Implication

This choice is meant to work across:

- in-process Python callers
- Textual
- future native clients
- future browser clients
- future mobile clients

For browsers specifically:

- the server stream provides ordered projection events
- the client still owns local structured concurrency
- the client can use snapshot version and sequence to drop stale work

So this implementation helps the browser by making the input disciplined, but
it does not replace client-side provider/reducer/cancellation logic.

## First Use Sites

### 1. Subject Workflow Watch Streams

Priority:

- highest

Why:

- this is where stale repaints and delayed cursor/toggle behavior already hurt
  the workstation

Mode:

- FIFO

### 2. Operation Progress

Why:

- background analysis, builds, imports, and refreshes have meaningful event
  order

Mode:

- FIFO

### 3. Activity Feed

Why:

- activity should preserve chronological visibility

Mode:

- FIFO

## Lock-Step Posture

Lock-step is supported by the theory, but it is **deferred** in the first
implementation.

Reason:

- most current workstation channels need ordered observation, not one-at-a-time
  acknowledgement gating
- explicit ack adds protocol complexity
- we should only add it where a real consumer requires completed processing
  before next release

If later needed, lock-step should be implemented as:

- explicit ack-capable streamed messages
- explicit ack API from consumer to producer
- producer-side release discipline based on ack

## Where This Lives

Channel policy implementation belongs beside:

- transport
- projection backends
- watch stream infrastructure
- stream client adapters

It must not be hidden inside:

- Textual pane handlers
- ad hoc UI queue suppression
- widget-specific timers
- transport headers only

## Rollout

### Phase 1

- keep current unary commands
- keep current unary reads
- keep current watch streams
- stamp watch messages with explicit channel/event envelope fields
- enforce FIFO semantics per logical channel in the service layer

### Phase 2

- make stream clients consume by `channel_key` and `sequence`
- discard stale versions deterministically
- keep local projection apply keyed by version

### Phase 3

- add `WatchActivity`
- add `WatchOperation`
- apply the same envelope discipline there

### Phase 4

- add explicit ack only where lock-step becomes necessary

### Phase 5

- evaluate JetStream or another broker only if we truly need:
  - durable replay across restarts
  - offline/mobile catch-up
  - multiple independent consumer positions
  - cross-service fan-out beyond the current in-process/server model

## Short Implementation Rule

For now:

- use unary commands
- use unary reads
- use server-streaming watches
- carry channel semantics in protobuf message fields
- treat FIFO as the default ordered mode

Do not add broker infrastructure or bidi transport until the product need
actually demands it.
