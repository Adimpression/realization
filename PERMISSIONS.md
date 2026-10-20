# Workstation Permissions and Execution Boundaries

This document describes the implemented workstation permission model. It keeps
three controls separate because each answers a different question.

## Permission layers

1. **Ability declaration**: states an ability's intent, input and output
   contracts, requested authorities, side effects, and executor or broker.
2. **Session capability grant**: states which workstation operations the
   current session may expose.
3. **Invocation delegation**: narrows an admitted ability's requested rights to
   the concrete targets and duration approved for one invocation.

Importing or admitting an ability does not grant a session capability. Granting
a session capability does not admit an ability or install its executor. Neither
action creates invocation approval. Runtime checks all applicable layers before
dispatch.

## Session capability inventory

New sessions receive these capabilities by default:

- `ws.fs.read`
- `ws.process.run`
- `ws.markdown.create`
- `ws.markdown.append`
- `ws.skill.catalog`
- `ws.skill.import`
- `ws.skill.export`
- `ws.skill.invoke`
- `ws.skill.compose`

The session registry also makes these capabilities available for explicit
granting:

- `ws.repo.tree`
- `ws.repo.search`
- `ws.workflow.list`
- `ws.workflow.get`
- `ws.workflow.run`
- `ws.net.http`
- `ws.operator.list`
- `ws.operator.get`

The canonical inventory is defined in
[capabilities.py](workstation/runtime_core/src/workstation/runtime/core/capabilities.py).
Execution rejects any capability absent from the session's
`allowed_capabilities` before argument normalization or dispatch.

## Grant and revocation commands

The chat shell exposes:

```text
/permissions
/grant-permission <capability>
/revoke-permission <capability>
```

`/grant-permission` accepts only names in the available capability registry.
`/revoke-permission` uses the same registry. The following skill-management
capabilities are protected from revocation so that the in-chat management path
remains usable:

- `ws.skill.catalog`
- `ws.skill.import`
- `ws.skill.export`

Capability changes are persisted with the workstation session and emit grant or
revocation receipts. The command behavior is implemented in
[chat_commands.py](workstation/runtime_core/src/workstation/runtime/core/chat_commands.py).

## Dispatch boundaries

Session capabilities are stable operation names, not executor frameworks.
Their implementations have different dispatch paths:

- `ws.repo.tree`, `ws.repo.search`, `ws.fs.read`, `ws.process.run`, and
  `ws.net.http` use the shared host-interaction action layer.
- Markdown, skill management, workflow, and operator capabilities use their
  owning workstation runtime services.
- `ws.skill.invoke` resolves an installed governed skill, reevaluates admission
  and lifecycle state, computes effective invocation delegation, and dispatches
  the declared executor framework.

`ws.skill.invoke` may therefore lead to `wasm_wasi`, `python3`, `bash`, or
another supported executor. Wasmtime is used only when the selected skill's
declared executor framework is `wasm_wasi`; the other session capabilities do
not become Wasm executions merely because they are grantable.

The builtin `Workstation Greeting From Wasm` example is defined in
[builtin_skills.py](workstation/skills_builtin/src/workstation/skills/builtin/builtin_skills.py),
and Wasm execution is implemented in
[wasm_skill_runtime.py](wasm_skill_runtime.py).

## Network capability

`ws.net.http` is implemented, available, and not granted by default. It can be
enabled for the current session with:

```text
/grant-permission ws.net.http
```

The operation issues one explicit host-side HTTP request through
[host_interaction_action_dispatch.py](host_interaction_action_dispatch.py) and
[host_interaction_actions.py](host_interaction_actions.py). The method set,
timeout, and retained response size are bounded by that operation's contract.
This grant does not provide ambient network access to skill executors.

Wasm has a stricter boundary. [host_abi.py](host_abi.py) declares all ambient
Wasm capabilities, including network, as disabled. Wasm code can interact with
the host only through the governed `bssc` hostcall ABI, and the current stable
Wasm broker subset does not include the network brokers present in the wider
host broker registry.

An ability may declare `communicate`, but that declaration is an authority upper
bound rather than a grant. A usable network path still requires a matching host
operation, session availability, invocation-time governance, and a dispatch
surface that exposes that operation to the selected executor.

## Ability delivery boundary

Shipping an ability and providing its host realizer remain separate acts. The
ability declares the exact executor or broker it requires. Admission determines
whether that declaration may participate in reasoning. At invocation, runtime
mechanically checks that the host provides the declared realizer and that the
required authority is available. Semantic or LLM-assisted selection cannot
invent a host implementation, grant authority, or substitute an undeclared
executor.

See [SKILL_INTERFACE.md](SKILL_INTERFACE.md) for the portable ability boundary
and [SKILLS.md](SKILLS.md) for the wider skill model.
