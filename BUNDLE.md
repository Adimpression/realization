# Capability-Mediated Host And Skill Runtime

The governing design is:

**the host owns resources; skills receive only mediated capabilities.**

This is the core pattern. A Rust host backed by SQLite is one possible
realization, but the capability boundary does not depend on that language or
storage implementation.

A Rust/Wasm realization uses:

* **native app sandbox** as the outer boundary on each OS,
* **embedded Wasm runtime** as the inner skill boundary,
* **Rust hostcalls** as the only way skills touch network, files, SQLite, clocks, randomness, or other skills.

This produces a low-bloat, cross-platform model with explicit governance. WebAssembly is designed to execute untrusted code in a sandbox and Wasmtime’s WASI context starts “null” or “empty” by default, with resources added explicitly. That default-empty model provides the required dependency-injection boundary. ([Wasmtime][1])

The symbolic-reasoning literature supports this direction too: formalized symbolic pipelines, executable intermediate forms, and deterministic execution improve verifiability, replayability, and interpretability over free-form reasoning alone. A dependency-injection runtime should treat capability use the same way: explicit symbolic declarations, mediated execution, and replayable traces.

## What to put where

### Outer boundary: the app

The app itself runs inside the platform sandbox:

* Android app sandbox. ([Android Developers][2])
* Apple App Sandbox / entitlements on macOS, and Apple’s sandbox model on iOS-family platforms. ([Apple Developer][3])
* Windows AppContainer / Win32 app isolation. ([Microsoft Learn][4])

### Inner boundary: the skill runtime

Each skill runs inside an embedded Wasm runtime with:

* no ambient filesystem
* no ambient network
* no ambient SQLite handle
* no clock unless injected
* no randomness unless injected
* no direct OS API access

Everything comes through imports/hostcalls you expose.

## The most important design rule

**Do not give skills raw OS resources. Give them DI resources.**

That means:

Bad:

* direct TCP socket access
* direct file paths
* direct SQLite connection
* direct HTTP client
* direct random number generator
* direct system time

Good:

* `di.net.fetch(policy_scoped_request)`
* `di.store.query(prepared_query_id, typed_params)`
* `di.fs.read(file_capability, relative_path)`
* `di.time.now(time_capability)`
* `di.rand.bytes(seed_capability, n)`

In other words, capabilities should be **logical handles**, not native handles.

## Recommended capability model

Define capabilities as signed, structured objects attached to the execution context.

Each capability should include:

* capability type
* allowed operations
* scope
* resource identifier
* constraints
* expiry
* issuer
* audit tag
* approval class

Example:

```yaml
capability:
  type: network
  id: cap_net_01
  operations: [http_get]
  allow_hosts: ["api.example.com"]
  allow_methods: ["GET"]
  max_requests: 20
  max_response_bytes: 1048576
  expires_at: "2026-04-01T00:00:00Z"
  issued_by: "policy://org/default"
  approval: "auto"
```

The skill does not “have networking.”
It has **this** network capability.

## Network capability

Do not expose raw sockets first.

Start with a **policy-controlled HTTP client** hostcall.

Expose something like:

* `fetch`
* `dns_resolve` only if necessary
* maybe `webhook_post` later
* avoid raw TCP/UDP in the first version

Why:
raw sockets dramatically widen the attack surface. HTTP mediation lets you enforce:

* allowed domains
* allowed methods
* header allowlist
* body size limits
* response size limits
* request rate limits
* timeout
* redirect policy
* TLS requirements
* audit logging

At the OS level, native sandboxes also govern network differently across platforms, especially Apple and Windows. Keeping network access inside your Rust mediation layer makes your DI policy portable even when the OS semantics differ. ([Apple Developer][5])

So the hostcall should look more like:

* `di.net.http(request_descriptor) -> response_descriptor`

not:

* `socket()`

## Filesystem capability

Never let skills see arbitrary paths.

Use **virtual mounts**:

* `/skill_tmp`
* `/skill_input`
* `/skill_output`
* `/shared_readonly/curriculum`
* `/user_docs_selected/...`

Map these to real OS locations in the host.

Grant access by mount capability, not by path string alone.

Operations:

* read
* write
* list
* create temp
* append
* no rename across mounts unless explicit
* no symlink traversal unless deliberately supported

Apple’s sandbox and Android’s storage model already push you toward mediated, app-scoped storage instead of broad filesystem freedom. ([Apple Developer][6])

## SQLite capability

SQLite should stay in the **trusted host**, not in skills.

Do not give a skill the DB file.
Do not give a skill arbitrary SQL.

Instead give one of three safer patterns:

### Pattern A: named queries

Best for safety.

Skills can call only pre-registered queries/mutations.

Example:

* `student_lookup_by_id`
* `list_recent_actions`
* `append_audit_event`

The skill sends typed params; host runs prepared statements.

### Pattern B: table/view capability + query subset

More flexible.

Allow a restricted query DSL against specific views.
No arbitrary joins, no PRAGMA, no ATTACH, no raw schema mutation.

### Pattern C: per-skill logical KV/document store

Simplest for many skills.

Skills get namespaced storage:

* `skill://notes`
* `skill://cache`
* `skill://state`

Host maps that to SQLite tables under the hood.

The default dependency-injection policy is:

* **named queries for sensitive/core data**
* **namespaced KV/doc for skill-local state**

That keeps SQLite as the trusted substrate while letting skills persist state safely.

On Android, SQLite is a standard local structured-data choice, and Android recommends WAL for performance in many cases. ([Android Developers][7])
SQLite itself also supports in-memory databases for ephemeral execution state or replay environments. ([SQLite][8])

## Time and randomness

These are often ignored, but they matter for determinism.

Default:

* no wall clock
* no monotonic clock
* no randomness

Then allow them explicitly:

* `time.read_now`
* `time.deadline`
* `rand.seeded_stream`
* `rand.nonce`

For reproducibility:

* inject recorded time values in replay mode
* inject seeded PRNG streams in replay mode

If you do this, the same skill run can be replayed much more faithfully.

## Process / external tool capability

Avoid exposing arbitrary subprocess execution cross-platform.

Instead:

* expose **named tools** as host-mediated services
* each tool has manifest, version, risk tier, and policy
* the skill calls `di.tool.invoke("pdf_extract", args)` rather than launching a binary

This keeps behavior portable across Windows/macOS/Linux/mobile, where process semantics differ sharply.

## Inter-skill capability

Do not let skills directly call each other arbitrarily.

Use:

* declared provided interfaces
* declared required interfaces
* policy-approved bindings
* bounded chain depth
* cycle detection
* per-hop audit

This prevents harmless-looking skills from composing into an unbounded agent.

## Mobile-specific note

On iOS especially, assume:

* no general container runtime
* no arbitrary executable loading in the traditional sense
* stay inside the app sandbox and your embedded runtime model

On Android, app sandboxing is standard, and there is also an SDK Sandbox facility for certain privacy-focused cases, but for your DI skill model the main control plane should still be your own inner runtime. ([Android Developers][9])

## Suggested Rust runtime shape

Your host state might look conceptually like:

```rust
struct HostState {
    wasi: WasiCtx,
    policy: PolicyEngine,
    sqlite: DbPool,
    mounts: MountTable,
    net: NetworkBroker,
    tool_registry: ToolRegistry,
    audit: AuditSink,
    capability_store: CapabilityStore,
}
```

Each skill instance gets:

* a Wasm store
* a capability set
* a policy context
* an audit session id
* optional per-skill state namespace

And every hostcall does:

1. validate manifest declaration
2. validate current capability token
3. evaluate policy
4. execute via broker
5. emit audit event
6. return typed result

## Capability rollout

Capabilities should be introduced in the following phases.

### Tier 0

* pure compute
* local deterministic transforms
* read-only structured inputs
* skill-local ephemeral memory

### Tier 1

* namespaced persistent state in SQLite
* read-only virtual files
* bounded clocks/random with replay support

### Tier 2

* mediated HTTP GET to allowlisted domains
* bounded POST/webhook
* approved inter-skill calls

### Tier 3

* writes to shared stores
* sensitive named queries
* user-document export
* external service credentials

### Tier 4

* high-impact tools
* broad network
* policy changes
* installing other skills
* autonomous loops

This staged model preserves capability-mediated dependency injection instead of granting broad powers early.

## Optional Rust/Wasm realization

A Rust host implementation can use:

* **Wasmtime** for the embedded runtime
* **WASI Preview 2 / Component Model direction** for modular interfaces
* host-defined `di:*` interfaces instead of exposing raw WASI broadly

Wasmtime supports WebAssembly, WASI, and the Component Model, and its WASI context is explicit and additive rather than ambient. ([Wasmtime][1])

The important design move is:
**use WASI sparingly, and DI interfaces heavily.**

WASI is useful for the substrate.
Host-defined `di:net`, `di:store`, `di:fs`, `di:audit`, and `di:policy` interfaces are where governance lives.

## Governing result

The model requires:

* Keep **SQLite in the trusted host**
* Run skills inside **embedded Wasm**
* Expose capabilities only through **policy-mediated hostcalls**
* Prefer **logical capabilities** over raw OS resources
* Start with **HTTP mediation**, not raw sockets
* Use **virtual mounts**, not raw filesystem paths
* Use **named queries / namespaced state**, not arbitrary SQL
* Make time/randomness **injectable and replayable**
This yields a practical dependency-injection runtime that stays small,
cross-platform, and governable.

[1]: https://docs.wasmtime.dev/ "Wasmtime: Introduction"
[2]: https://developer.android.com/guide/components/fundamentals "Application fundamentals | App architecture"
[3]: https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.app-sandbox "App Sandbox Entitlement | Apple Developer Documentation"
[4]: https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation "AppContainer isolation - Win32 apps"
[5]: https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox "Protecting user data with App Sandbox"
[6]: https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox "Accessing files from the macOS App Sandbox"
[7]: https://developer.android.com/training/data-storage/sqlite "Save data using SQLite | App data and files"
[8]: https://sqlite.org/docs.html "SQLite Documentation"
[9]: https://developer.android.com/design-for-safety/privacy-sandbox/reference/sdksandbox/package-summary "android.app.sdksandbox | API reference"
