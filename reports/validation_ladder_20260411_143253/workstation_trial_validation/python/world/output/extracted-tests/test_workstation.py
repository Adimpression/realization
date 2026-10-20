# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import io
import importlib
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from args import parse_args
from execution_frameworks import _shell_cross_boundary
from host_interaction_receipts import host_interaction_capability_call_receipt
from learning_context import load_learning_context
from skill_schema_io import artifact_from_skill_document
from store import SQLiteVectorArtifactStore
from workstation.cli import (
    _prompt_for_workstation_escalation,
    handle_workstation_chat_command,
    handle_workstation_launch_command,
    handle_workstation_prompt_command,
    handle_workstation_skill_catalog_command,
    handle_workstation_skill_export_command,
    handle_workstation_skill_import_command,
    handle_workstation_trial_validate_command,
    run_workstation_chat_loop,
)
from workstation.llm_driver import (
    normalize_workstation_tool_definitions_for_provider,
    run_workstation_openai_turn,
    workstation_tool_capability_name,
    workstation_tool_wire_name,
)
from workstation.capabilities import DEFAULT_WORKSTATION_CAPABILITIES, execute_workstation_capability
from workstation.direct_composition import (
    derive_workstation_partial_invocation_payload_from_prompt,
    derive_workstation_invocation_payload_from_prompt,
    preferred_workstation_skill_invocation_plan,
)
from workstation.governance import (
    WORKSTATION_DEFAULT_POLICY_TITLE,
    workstation_default_policy_payload,
    workstation_governance_inventory,
)
from workstation.skill_management import import_workstation_skill_file, workstation_prompt_skill_shortlist_payload
from workstation.skill_composition_planning import preferred_workstation_skill_composition_plan
from workstation.skill_invocation import resolve_workstation_skill, workstation_missing_required_inputs, workstation_skill_store
from workstation.skill_invocation import bounded_nested_effect_traces
from workstation.skill_invocation import workstation_nested_skill_answer_text
from workstation.session import launch_workstation_session, prompt_workstation_session
from workstation.models import WorkstationDelegationEscalationRequest, WorkstationSession
from workstation.task_contract import normalize_prompt_to_task_boundary_contract
from workstation.trial_validation import (
    _materialize_apiclient_fake_http_environment,
    _materialize_ansible_fake_toolchain,
    _materialize_common_trial_host_fixtures,
    _materialize_deviceuser_fake_macos_toolchain,
    _materialize_sdkuser_fake_sdk_environment,
    validate_workstation_trial_domains,
)
from workstation.workstation_core import workstation_learn_markdown_action


class _FakeFunction:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, tool_call_id: str, name: str, arguments: str) -> None:
        self.id = tool_call_id
        self.type = "function"
        self.function = _FakeFunction(name, arguments)


class _FakeMessage:
    def __init__(self, *, content: str = "", tool_calls: list[_FakeToolCall] | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []


class _FakeChoice:
    def __init__(self, message: _FakeMessage) -> None:
        self.message = message


class _InterruptingInputStream:
    def __init__(self, items: list[object]) -> None:
        self._items = list(items)

    def readline(self) -> str:
        if not self._items:
            return ""
        item = self._items.pop(0)
        if isinstance(item, BaseException):
            raise item
        return str(item)


class _FakeResponse:
    def __init__(self, message: _FakeMessage) -> None:
        self.choices = [_FakeChoice(message)]


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_1",
                            "ws.repo.tree",
                            json.dumps({"target": "main"}),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="I inspected the workspace and found the repository tree."))


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


class _FakeSkillInvokeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_skill_1",
                            "ws.skill.invoke",
                            json.dumps({"skill_title": "Workstation Greeting"}),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="The installed skill says hello from skill."))


class _FakeSkillInvokeChat:
    def __init__(self) -> None:
        self.completions = _FakeSkillInvokeCompletions()


class _FakeSkillInvokeClient:
    def __init__(self) -> None:
        self.chat = _FakeSkillInvokeChat()


class _FakeMarkdownCreateCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_markdown_create_1",
                            "ws.markdown.create",
                            json.dumps(
                                {
                                    "path": "notes/chat_learnings.md",
                                    "markdown_text": "# Saved Learnings\n\n- The dilution relation preserves amount.",
                                }
                            ),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="Saved the learnings markdown to notes/chat_learnings.md."))


class _FakeMarkdownCreateChat:
    def __init__(self) -> None:
        self.completions = _FakeMarkdownCreateCompletions()


class _FakeMarkdownCreateClient:
    def __init__(self) -> None:
        self.chat = _FakeMarkdownCreateChat()


class _NestedSkillResult:
    def __init__(self, *, stdout: str = "", answer: str = "", parsed_output: object = None, result: object = None) -> None:
        self.stdout = stdout
        self.answer = answer
        self.parsed_output = parsed_output
        self.result = result


class _FakeRepoSearchSkillCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_repo_search_1",
                            "ws.skill.invoke",
                            json.dumps(
                                {
                                    "skill_title": "Workstation Repo Search",
                                    "invocation_payload": {
                                        "mount": "main",
                                        "pattern": "def main",
                                        "max_matches": 10,
                                    },
                                    "requested_delegation": [
                                        {
                                            "capability": "ws.fs.read",
                                            "target": "main",
                                            "rationale": "Need to inspect repository files.",
                                        }
                                    ],
                                }
                            ),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="I found the main function in app.py."))


class _FakeRepoSearchSkillChat:
    def __init__(self) -> None:
        self.completions = _FakeRepoSearchSkillCompletions()


class _FakeRepoSearchSkillClient:
    def __init__(self) -> None:
        self.chat = _FakeRepoSearchSkillChat()


class _FakeMinimalRepoSearchSkillCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_repo_search_minimal_1",
                            "ws.skill.invoke",
                            json.dumps(
                                {
                                    "skill_title": "Workstation Repo Search",
                                    "semantic_unit": "Find where workstation chat is implemented in this workspace.",
                                }
                            ),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="The workstation chat implementation is in workstation/cli.py."))


class _FakeMinimalRepoSearchSkillChat:
    def __init__(self) -> None:
        self.completions = _FakeMinimalRepoSearchSkillCompletions()


class _FakeMinimalRepoSearchSkillClient:
    def __init__(self) -> None:
        self.chat = _FakeMinimalRepoSearchSkillChat()


class _FakeExplicitSkillFailureThenFallbackCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_skill_fail_1",
                            "ws.skill.invoke",
                            json.dumps(
                                {
                                    "skill_title": "Symbol Search Commands 03 — Find Python Class Definition",
                                    "semantic_unit": "Use the symbol search skill to find the Python class definition for BSSCController under src.",
                                }
                            ),
                        )
                    ]
                )
            )
        return _FakeResponse(
            _FakeMessage(
                tool_calls=[
                    _FakeToolCall(
                        "call_fallback_1",
                        "ws.fs.read",
                        json.dumps({"target": "main", "path": "src/demo.py"}),
                    )
                ]
            )
        )


class _FakeExplicitSkillFailureThenFallbackChat:
    def __init__(self) -> None:
        self.completions = _FakeExplicitSkillFailureThenFallbackCompletions()


class _FakeExplicitSkillFailureThenFallbackClient:
    def __init__(self) -> None:
        self.chat = _FakeExplicitSkillFailureThenFallbackChat()


class _FakeImplicitSkillApprovalThenFallbackCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_skill_approval_1",
                            "ws.skill.invoke",
                            json.dumps(
                                {
                                    "skill_title": "Python Commands 13 — Create Zip Archive",
                                    "semantic_unit": "Create `realized-tests.zip` in mount `skill_tmp` from mount `skill_input` at `tests`.",
                                }
                            ),
                        )
                    ]
                )
            )
        return _FakeResponse(
            _FakeMessage(
                tool_calls=[
                    _FakeToolCall(
                        "call_fallback_after_approval_1",
                        "ws.fs.read",
                        json.dumps({"target": "skill_input", "path": "tests"}),
                    )
                ]
            )
        )


class _FakeImplicitSkillApprovalThenFallbackChat:
    def __init__(self) -> None:
        self.completions = _FakeImplicitSkillApprovalThenFallbackCompletions()


class _FakeImplicitSkillApprovalThenFallbackClient:
    def __init__(self) -> None:
        self.chat = _FakeImplicitSkillApprovalThenFallbackChat()


class _RetryThenSucceedCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1 and "temperature" in kwargs:
            raise RuntimeError("Unsupported value: 'temperature' does not support 0.0 with this model. Only the default (1) value is supported.")
        return _FakeResponse(_FakeMessage(content="Fallback temperature path succeeded."))


class _RetryThenSucceedChat:
    def __init__(self) -> None:
        self.completions = _RetryThenSucceedCompletions()


class _RetryThenSucceedClient:
    def __init__(self) -> None:
        self.chat = _RetryThenSucceedChat()


class _RetryOnServerErrorCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("Error code: 500")
        return _FakeResponse(_FakeMessage(content="Transient provider retry succeeded."))


class _RetryOnServerErrorChat:
    def __init__(self) -> None:
        self.completions = _RetryOnServerErrorCompletions()


class _RetryOnServerErrorClient:
    def __init__(self) -> None:
        self.chat = _RetryOnServerErrorChat()


class _FakeEscalationSkillCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_escalation_1",
                            "ws.skill.invoke",
                            json.dumps(
                                {
                                    "skill_title": "Workstation Greeting",
                                    "requested_delegation": [
                                        {
                                            "capability": "ws.fs.write",
                                            "target": "scratch",
                                            "rationale": "Need scratch write for this invocation.",
                                        }
                                    ],
                                }
                            ),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="The skill completed after approval."))


class _FakeEscalationSkillChat:
    def __init__(self) -> None:
        self.completions = _FakeEscalationSkillCompletions()


class _FakeEscalationSkillClient:
    def __init__(self) -> None:
        self.chat = _FakeEscalationSkillChat()


class _FakeSkillComposeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_compose_1",
                            "ws.skill.compose",
                            json.dumps(
                                {
                                    "steps": [
                                        {
                                            "step_id": "emit",
                                            "skill_title": "Emit Text",
                                            "bindings": [
                                                {
                                                    "target_region": "a",
                                                    "target_path": "/a/text",
                                                    "source_root_name": "text",
                                                    "source_root_region": "a",
                                                }
                                            ],
                                        },
                                        {
                                            "step_id": "consume",
                                            "skill_title": "Consume Text",
                                            "bindings": [
                                                {
                                                    "target_region": "a",
                                                    "target_path": "/a/text",
                                                    "source_step_id": "emit",
                                                    "source_region": "d",
                                                    "source_path": "/d/text",
                                                    "mapper": {"kind": "identity"},
                                                }
                                            ],
                                        },
                                    ],
                                    "root_inputs": {
                                        "text": "hello world",
                                    },
                                }
                            ),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="Composed the skills successfully."))


class _FakeSkillComposeChat:
    def __init__(self) -> None:
        self.completions = _FakeSkillComposeCompletions()


class _FakeSkillComposeClient:
    def __init__(self) -> None:
        self.chat = _FakeSkillComposeChat()


class _FakeBadTargetThenAnswerCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse(
                _FakeMessage(
                    tool_calls=[
                        _FakeToolCall(
                            "call_bad_target_1",
                            "ws.repo.tree",
                            json.dumps({"target": "does_not_exist"}),
                        )
                    ]
                )
            )
        return _FakeResponse(_FakeMessage(content="Recovered after tool error."))


class _FakeBadTargetThenAnswerChat:
    def __init__(self) -> None:
        self.completions = _FakeBadTargetThenAnswerCompletions()


class _FakeBadTargetThenAnswerClient:
    def __init__(self) -> None:
        self.chat = _FakeBadTargetThenAnswerChat()


class WorkstationTests(unittest.TestCase):
    def setUp(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation vertical-slice regression testing, helps with preparing an isolated temporary workspace and workstation root.

        Reference to Theory:
            Verifies the workstation session, attachment, prompt, and capability model without disturbing the outer BSSC architecture.

        Example Input Output:
            Input: `setUp()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.tempdir = tempfile.TemporaryDirectory(prefix="workstation_tests_")
        self.workstation_home = Path(self.tempdir.name) / ".workstation"
        self.workstation_home.mkdir(parents=True, exist_ok=True)
        self.env_patcher = patch.dict(os.environ, {"WORKSTATION_HOME": str(self.workstation_home)}, clear=False)
        self.env_patcher.start()
        self.workspace = Path(self.tempdir.name) / "project"
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "README.md").write_text("# Demo Project\n")
        (self.workspace / "app.py").write_text("def main():\n    return 'hello'\n")
        (self.workspace / "src").mkdir(parents=True, exist_ok=True)
        (self.workspace / "src" / "demo.py").write_text(
            "class BSSCController:\n"
            "    pass\n\n"
            "class DemoRunner:\n"
            "    pass\n"
        )
        (self.workspace / "workstation").mkdir(parents=True, exist_ok=True)
        (self.workspace / "workstation" / "cli.py").write_text(
            "\n".join(
                [
                    "def handle_workstation_chat_command(args):",
                    "    return run_workstation_chat_loop(args)",
                    "",
                ]
            )
        )
        self.root = Path(self.tempdir.name) / "session"
        self.skills_sqlite = Path(self.tempdir.name) / "skills.sqlite3"
        skill_store = SQLiteVectorArtifactStore()
        skill_store.sqlite_path = self.skills_sqlite
        skill_store.persist_artifact(
            artifact_from_skill_document(
                {
                    "schema": "bssc_skill.v1",
                    "kind": "knowledge",
                    "title": "Workstation Greeting",
                    "answer": "hello from skill",
                }
            ),
            run_id="test_workstation_skill_import",
        )

    def tearDown(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation vertical-slice regression testing, helps with cleaning up the temporary workspace and session root after each test.

        Reference to Theory:
            Verifies the workstation session, attachment, prompt, and capability model without disturbing the outer BSSC architecture.

        Example Input Output:
            Input: `tearDown()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.env_patcher.stop()
        self.tempdir.cleanup()

    def _persist_python_ability_skill(
        self,
        *,
        title: str,
        inputs: dict[str, str],
        outputs: dict[str, str],
        normalization: dict[str, object],
        python_lines: list[str],
    ) -> None:
        store = SQLiteVectorArtifactStore()
        store.sqlite_path = self.skills_sqlite
        store.load_all_artifacts()
        python_script = "\n".join(python_lines)
        if "__name__ == \"__main__\"" not in python_script and "__name__ == '__main__'" not in python_script:
            python_script = (
                f"{python_script}\n\n"
                "if __name__ == '__main__':\n"
                "    import json\n"
                "    import sys\n"
                "    raw = sys.stdin.buffer.read()\n"
                "    payload = json.loads(raw.decode('utf-8')) if raw else {}\n"
                "    result = main(payload)\n"
                "    sys.stdout.write(json.dumps(result))\n"
            )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": title,
                "executor": "python3",
                "entrypoint": "main",
                "inputs": inputs,
                "outputs": outputs,
                "declaration": {
                    "intent": f"Execute {title}.",
                    "inputs": inputs,
                    "outputs": outputs,
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["local executor invocation"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                    "executor_framework": "python3",
                },
                "normalization": normalization,
                "python": python_script,
            }
        )
        store.persist_artifact(artifact, run_id=f"test:{title}")

    def test_parse_args_supports_workstation_commands(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation CLI entry testing, helps with verifying that the new workstation commands parse as first-class commands rather than falling back into the controller `run` shim.

        Reference to Theory:
            Verifies the workstation entry surface without entangling it with the outer BSSC controller runtime.

        Example Input Output:
            Input: `test_parse_args_supports_workstation_commands()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        args = parse_args(["workstation-launch", "--root", str(self.root), "--workspace", str(self.workspace)])
        self.assertEqual(args.command, "workstation-launch")
        args = parse_args(["workstation-prompt", "--root", str(self.root), "--prompt", "Inspect the workspace."])
        self.assertEqual(args.command, "workstation-prompt")
        args = parse_args(["workstation-chat", "--root", str(self.root)])
        self.assertEqual(args.command, "workstation-chat")
        args = parse_args(["workstation-skill-catalog", "--root", str(self.root)])
        self.assertEqual(args.command, "workstation-skill-catalog")
        args = parse_args(["workstation-skill-catalog", "--root", str(self.root), "--query", "python", "--limit", "5"])
        self.assertEqual(args.query, "python")
        self.assertEqual(args.limit, 5)
        args = parse_args(["workstation-skill-import", "--root", str(self.root), "--skill-file", str(self.workspace / "demo.yaml")])
        self.assertEqual(args.command, "workstation-skill-import")
        args = parse_args(["workstation-skill-export", "--root", str(self.root), "--skill-title", "Workstation Greeting"])
        self.assertEqual(args.command, "workstation-skill-export")
        args = parse_args(["workstation-trial-validate", "--domains", "symbolsearch", "--workspace", str(self.workspace)])
        self.assertEqual(args.command, "workstation-trial-validate")
        args = parse_args(
            [
                "workstation-launch",
                "--root",
                str(self.root),
                "--workspace",
                str(self.workspace),
                "--skills-sqlite",
                str(self.skills_sqlite),
            ]
        )
        self.assertEqual(args.skills_sqlite, self.skills_sqlite)

    def test_workstation_learn_markdown_action_persists_learning_context_under_session_root(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Learn markdown into the workstation corpus.",
        )
        markdown_path = self.workspace / "notes" / "kinematics.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text("# Kinematics Demo\n\nVelocity is displacement per unit time.\n", encoding="utf-8")
        captured: dict[str, object] = {}

        def _fake_subprocess_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            captured["command"] = list(command)
            captured["cwd"] = kwargs.get("cwd")
            env = kwargs.get("env")
            self.assertIsInstance(env, dict)
            captured["env"] = dict(env)
            out_path = Path(command[command.index("--out") + 1])
            report_path = Path(command[command.index("--report-out") + 1])
            out_path.write_text(
                "\n".join(
                    [
                        "schema: bssc_skill.v2",
                        "kind: knowledge",
                        "title: Kinematics Demo",
                        "answer: Velocity is displacement per unit time.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            report_path.write_text(
                json.dumps(
                    {
                        "subject_id": "kinematics-demo",
                        "context_path": str(self.root / "corpus" / "kinematics-demo" / "context.json"),
                        "learned_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with patch("workstation.workstation_core.subprocess.run", side_effect=_fake_subprocess_run), patch(
            "workstation.capabilities.execute_workstation_capability",
            return_value={
                "status": "ok",
                "imported_count": 1,
                "imported": [{"title": "Kinematics Demo"}],
                "canonical_export_path": "kinematics.skill.yaml",
            },
        ):
            result = workstation_learn_markdown_action(
                root_path=self.root,
                markdown_path=markdown_path,
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(captured["cwd"], str(Path(__file__).resolve().parents[1]))
        command_env = captured["env"]
        self.assertIsInstance(command_env, dict)
        self.assertEqual(command_env.get("LEARNING_CONTEXT_ROOT"), str(self.root.resolve()))
        payload = result.payload
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("learning_context_root"), str(self.root.resolve()))
        report = payload.get("report")
        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("subject_id"), "kinematics-demo")
        self.assertEqual(
            report.get("context_path"),
            str(self.root / "corpus" / "kinematics-demo" / "context.json"),
        )

    def test_launch_workstation_materializes_root(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation session creation testing, helps with verifying that launch materializes the expected discovery files and session state.

        Reference to Theory:
            Verifies the workstation launcher and attachment model for the first vertical slice.

        Example Input Output:
            Input: `test_launch_workstation_materializes_root()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report = launch_workstation_session(root_path=self.root, workspace_path=self.workspace, initial_task="Inspect the project.")
        self.assertEqual(Path(report["root_path"]), self.root.resolve())
        self.assertTrue((self.root / "README.md").exists())
        self.assertTrue((self.root / "WORKSTATION.toml").exists())
        self.assertTrue((self.root / "ATTACHMENTS.json").exists())
        self.assertTrue((self.root / "TOOLS.json").exists())
        self.assertTrue((self.root / "BLEND_CONTEXT.json").exists())
        self.assertTrue((self.root / "BLEND_SESSION.json").exists())
        self.assertTrue((self.root / "TASK.md").exists())
        self.assertTrue((self.root / "SKILLS.json").exists())
        self.assertTrue((self.root / "mounts" / "main").is_symlink())
        session = WorkstationSession.from_dict(report)
        self.assertTrue(any(item.kind == "session_root" for item in session.attachments))
        self.assertTrue(any(item.kind == "skill_store" for item in session.attachments))
        self.assertTrue(any(item.name == "skill_input" for item in session.attachments))
        self.assertTrue(any(item.name == "skill_tmp" for item in session.attachments))
        self.assertTrue(any(item.name == "skill_output" for item in session.attachments))
        self.assertIn("ws.skill.catalog", report["allowed_capabilities"])
        self.assertNotIn("ws.repo.search", report["allowed_capabilities"])
        self.assertNotIn("ws.repo.tree", report["allowed_capabilities"])
        self.assertNotIn("ws.workflow.list", report["allowed_capabilities"])
        self.assertNotIn("ws.workflow.get", report["allowed_capabilities"])
        self.assertNotIn("ws.workflow.run", report["allowed_capabilities"])

    def test_launch_with_skill_store_materializes_skill_catalog(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation skill-integration regression testing, helps with verifying that launching a workstation against a skill store materializes the installed-skill discovery catalog and exposes `ws.skill.invoke`.

        Reference to Theory:
            Verifies the workstation shell / pluggable-worker model without entangling it with the outer controller surface.

        Example Input Output:
            Input: `test_launch_with_skill_store_materializes_skill_catalog()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report = launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Use the installed skills.",
        )
        self.assertIn("ws.skill.invoke", report["allowed_capabilities"])
        self.assertNotIn("ws.repo.search", report["allowed_capabilities"])
        self.assertNotIn("ws.repo.tree", report["allowed_capabilities"])
        self.assertNotIn("ws.workflow.list", report["allowed_capabilities"])
        self.assertNotIn("ws.workflow.get", report["allowed_capabilities"])
        self.assertNotIn("ws.workflow.run", report["allowed_capabilities"])
        session = WorkstationSession.from_dict(report)
        self.assertTrue(any(item.name == "session" and item.kind == "session_root" for item in session.attachments))
        skills_payload = json.loads((self.root / "SKILLS.json").read_text())
        titles = [item["title"] for item in skills_payload["skills"]]
        self.assertIn("Workstation Repo Tree", titles)
        self.assertIn("Workstation Repo Search", titles)
        self.assertIn("Workstation Greeting From Wasm", titles)
        self.assertIn("Workstation Greeting", titles)

    def test_skill_catalog_returns_persistent_skill_home_metadata(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation skill-home discovery testing, helps with verifying that the workstation can return one stable catalog payload describing the persistent skill store and its attached import/export paths.

        Reference to Theory:
            Verifies the workstation shell keeps its worker inventory explicit and session-visible instead of hiding it behind an ambient SQLite path.

        Example Input Output:
            Input: `test_skill_catalog_returns_persistent_skill_home_metadata()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use the installed skills.",
            )
        )
        result = execute_workstation_capability(session, "ws.skill.catalog", {})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "skills")
        self.assertEqual(result["skill_store_attachment"], "skills")
        self.assertEqual(result["skill_exports_attachment"], "skills_exports")
        self.assertEqual(result["skill_imports_attachment"], "skills_imports")
        self.assertTrue(str(result["skill_home"]["store_path"]).endswith(".sqlite3"))

    def test_skill_catalog_supports_query_and_limit(self) -> None:
        """
        High Level Purpose:
            In circumstances like large workstation worker inventories, helps with verifying that the workstation skill catalog can be narrowed by a short query and bounded limit instead of always returning the full inventory.

        Reference to Theory:
            Verifies the workstation shell can expose worker discovery as an explicit filtered surface, which is important once multiple trial bundles share one skill home.

        Example Input Output:
            Input: `test_skill_catalog_supports_query_and_limit()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Inspect the skill catalog.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.catalog",
            {"query": "greeting", "limit": 2},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query"], "greeting")
        self.assertEqual(result["returned_skill_count"], 2)
        self.assertGreaterEqual(result["total_skill_count"], 3)
        self.assertTrue(all("greeting" in str(item["title"]).casefold() for item in result["skills"]))

    def test_prompt_skill_shortlist_prioritizes_repo_search(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompt handling against a larger worker inventory, helps with verifying that the prompt-local skill shortlist surfaces the most relevant workers first.

        Reference to Theory:
            Verifies the workstation shell can prefer direct worker composition before generic tool use when the prompt already points strongly at one installed worker.

        Example Input Output:
            Input: `test_prompt_skill_shortlist_prioritizes_repo_search()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Find where main is implemented in this workspace.",
            )
        )
        payload = workstation_prompt_skill_shortlist_payload(
            session=session,
            prompt="Find where main is implemented in this workspace.",
        )
        self.assertGreaterEqual(payload["returned_skill_count"], 1)
        self.assertEqual(payload["skills"][0]["title"], "Workstation Repo Search")

    def test_prompt_skill_shortlist_uses_semantic_bonus_for_device_browser_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation routing over imported device-user workers, helps with verifying that browser-launch prompts can still shortlist the correct worker even when the title uses different wording.

        Reference to Theory:
            Verifies the workstation shell can preserve direct worker composition for action-oriented prompts without relying on the full controller.

        Example Input Output:
            Input: `test_prompt_skill_shortlist_uses_semantic_bonus_for_device_browser_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Open Google Chrome to `https://example.com`.",
            )
        )
        with patch(
            "workstation.skill_management.workstation_skill_catalog_payload",
            return_value={
                "skills": [
                    {"title": "Device User Capabilities 01 — Launch Browser At Specific URL"},
                    {"title": "Device User Capabilities 03 — Open File In Chosen App"},
                    {"title": "Device User Capabilities 08 — Open System Settings Pane"},
                ],
            },
        ):
            payload = workstation_prompt_skill_shortlist_payload(
                session=session,
                prompt="Open Google Chrome to `https://example.com`.",
            )
        self.assertGreaterEqual(payload["returned_skill_count"], 1)
        self.assertEqual(payload["skills"][0]["title"], "Device User Capabilities 01 — Launch Browser At Specific URL")

    def test_direct_composition_derives_symbol_search_payload(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation direct composition over imported trial workers, helps with verifying that obvious prompt literals can be turned into a bounded invocation payload without a full controller loop.

        Reference to Theory:
            Supports direct skill composition before generic tool use by letting the shell bind prompt literals into explicit worker inputs.

        Example Input Output:
            Input: `test_direct_composition_derives_symbol_search_payload()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"symbol": "required input value", "root": "required input value"},
            prompt="Find every occurrence of the symbol `BSSCController` under `/Users/ravindranathakila/service/realized`.",
        )
        self.assertEqual(
            payload,
            {
                "symbol": "BSSCController",
                "root": "/Users/ravindranathakila/service/realized",
            },
        )

    def test_direct_composition_derives_bare_symbol_and_strips_trailing_path_punctuation(self) -> None:
        """
        High Level Purpose:
            In circumstances like natural-language workstation prompting over imported trial workers, helps with verifying that direct composition can derive obvious bare symbol/path inputs without requiring backticks and without keeping sentence-ending punctuation on the path.

        Reference to Theory:
            Supports workstation compatibility with trial prompts by letting the shell bind prompt-local worker inputs directly from the natural-language ask before the LLM tool loop expands context.

        Example Input Output:
            Input: `test_direct_composition_derives_bare_symbol_and_strips_trailing_path_punctuation()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"symbol": "required input value", "root": "required input value"},
            prompt="Find every occurrence of the symbol BSSCController under /Users/ravindranathakila/service/realized.",
        )
        self.assertEqual(
            payload,
            {
                "symbol": "BSSCController",
                "root": "/Users/ravindranathakila/service/realized",
            },
        )

    def test_direct_composition_derives_yaml_key_and_root(self) -> None:
        """
        High Level Purpose:
            In circumstances like symbolsearch-style workstation prompting, helps with verifying that direct composition can derive one required YAML key input together with the root path from the natural-language prompt.

        Reference to Theory:
            Supports direct skill composition by binding obvious prompt literals into worker inputs before the broader model tool loop runs.

        Example Input Output:
            Input: `test_direct_composition_derives_yaml_key_and_root()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"key": "required input value", "root": "required input value"},
            prompt="Find YAML keys named `artifact_type` under `/Users/ravindranathakila/service/realized`.",
        )
        self.assertEqual(
            payload,
            {
                "key": "artifact_type",
                "root": "/Users/ravindranathakila/service/realized",
            },
        )

    def test_direct_composition_derives_find_files_by_name_payload(self) -> None:
        """
        High Level Purpose:
            In circumstances like bash-style workstation prompting, helps with verifying that a filename literal can still bind the required `name` input even when it also looks like a path token.

        Reference to Theory:
            Supports direct skill composition by preserving obvious filename intent instead of forcing the workstation into the generic LLM tool loop for simple file-name search workers.

        Example Input Output:
            Input: `test_direct_composition_derives_find_files_by_name_payload()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={
                "name": "required input value",
                "root": "required input value",
            },
            prompt="Find files named `README.md` under `/Users/ravindranathakila/service/realized`.",
            skill_title="Bash Commands 06 — Find Files By Name / Bash Commands 06 Find Files By Name",
        )
        self.assertEqual(
            payload,
            {
                "name": "README.md",
                "root": "/Users/ravindranathakila/service/realized",
            },
        )

    def test_direct_composition_derives_todo_tag_without_backticks(self) -> None:
        """
        High Level Purpose:
            In circumstances like symbolsearch-style workstation prompting, helps with verifying that direct composition can recover a common uppercase tag like TODO even when the prompt does not wrap it in backticks.

        Reference to Theory:
            Supports direct skill composition by recovering obvious search intent from ordinary natural language instead of requiring perfectly structured tool arguments.

        Example Input Output:
            Input: `test_direct_composition_derives_todo_tag_without_backticks()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"tag": "required input value", "root": "required input value"},
            prompt="Find all TODO lines under `/Users/ravindranathakila/service/realized`.",
        )
        self.assertEqual(
            payload,
            {
                "tag": "TODO",
                "root": "/Users/ravindranathakila/service/realized",
            },
        )

    def test_direct_composition_escapes_literal_method_call_pattern(self) -> None:
        """
        High Level Purpose:
            In circumstances like method-call search prompts, helps with verifying that direct composition escapes punctuation-heavy literal patterns before passing them into regex-based symbol-search workers.

        Reference to Theory:
            Supports direct skill composition by preserving literal search intent for search workers that execute through regular-expression tools such as `rg`.

        Example Input Output:
            Input: `test_direct_composition_escapes_literal_method_call_pattern()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"pattern": "required input value", "root": "required input value"},
            prompt="Find lines containing the method call `.run(` under `/Users/ravindranathakila/service/realized`.",
        )
        self.assertEqual(
            payload,
            {
                "pattern": r"\.run\(",
                "root": "/Users/ravindranathakila/service/realized",
            },
        )

    def test_direct_composition_derives_python_mount_copy_payload(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation execution of imported python command workers, helps with verifying that direct composition can derive mount-scoped source and destination inputs from one ordinary copy prompt.

        Reference to Theory:
            Supports workstation compatibility with the command-style trial corpus by turning mount/path phrasing into explicit governed worker arguments before the generic tool loop runs.

        Example Input Output:
            Input: `test_direct_composition_derives_python_mount_copy_payload()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={
                "source_mount": "required input value",
                "source_relative_path": "required input value",
                "destination_mount": "required input value",
                "destination_relative_path": "required input value",
            },
            prompt="Copy `trials/python/README.md` from mount `skill_input` to mount `skill_tmp` at `python-readme.copy`.",
            skill_title="Python Commands 05 — Copy File",
        )
        self.assertEqual(
            payload,
            {
                "source_mount": "skill_input",
                "source_relative_path": "trials/python/README.md",
                "destination_mount": "skill_tmp",
                "destination_relative_path": "python-readme.copy",
            },
        )

    def test_direct_composition_derives_python_mount_write_payload(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation execution of imported python command workers, helps with verifying that direct composition can derive mount, relative path, and text for a write-style prompt.

        Reference to Theory:
            Supports workstation compatibility with the command-style trial corpus by binding concrete prompt literals into structured worker inputs before fallback tool use.

        Example Input Output:
            Input: `test_direct_composition_derives_python_mount_write_payload()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={
                "mount": "required input value",
                "relative_path": "required input value",
                "text": "required input value",
            },
            prompt="Write `hello world` to mount `skill_tmp` at `python-suite.txt`.",
            skill_title="Python Commands 03 — Write Text File",
        )
        self.assertEqual(
            payload,
            {
                "mount": "skill_tmp",
                "relative_path": "python-suite.txt",
                "text": "hello world",
            },
        )

    def test_direct_composition_derives_api_query_and_pagination_defaults(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation execution of imported API-client workers, helps with verifying that direct composition can derive query strings and bounded polling defaults from natural-language prompts.

        Reference to Theory:
            Supports workstation compatibility with API-style trial workers by translating ordinary request phrasing into explicit invocation payloads without full controller integration.

        Example Input Output:
            Input: `test_direct_composition_derives_api_query_and_pagination_defaults()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        query_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"url": "required input value", "query": "required input value"},
            prompt="Fetch JSON from `https://api.example.com/search` with query `q=widgets` and `limit=10`.",
            skill_title="API Client Commands 02 — Get Json With Query Parameters",
        )
        self.assertEqual(
            query_payload,
            {
                "url": "https://api.example.com/search",
                "query": {"q": "widgets", "limit": "10"},
            },
        )
        headers_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"url": "required input value", "headers": "required input value"},
            prompt="Fetch JSON from `https://api.example.com/items` with the header `X-Trace-Id: abc-123`.",
            skill_title="API Client Commands 08 — Get Json With Custom Headers",
        )
        self.assertEqual(
            headers_payload,
            {
                "url": "https://api.example.com/items",
                "headers": {"X-Trace-Id": "abc-123"},
            },
        )
        form_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"url": "required input value", "form_fields": "required input value"},
            prompt="Post the form fields `grant_type=client_credentials` and `scope=read` to `https://api.example.com/token`.",
            skill_title="API Client Commands 11 — Post Form Urlencoded Data",
        )
        self.assertEqual(
            form_payload,
            {
                "url": "https://api.example.com/token",
                "form_fields": {"grant_type": "client_credentials", "scope": "read"},
            },
        )
        download_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"url": "required input value", "destination": "required input value"},
            prompt="Download `https://example.com` to `/tmp/example.html`.",
            skill_title="Bash Commands 12 — Download Url To File",
        )
        self.assertEqual(
            download_payload,
            {
                "url": "https://example.com",
                "destination": "/tmp/example.html",
            },
        )
        poll_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={
                "url": "required input value",
                "status_field": "required input value",
                "target_value": "required input value",
                "poll_interval_seconds": "required input value",
                "max_attempts": "required input value",
            },
            prompt="Poll `https://api.example.com/jobs/42` until the JSON field `status` becomes `completed`.",
            skill_title="API Client Commands 12 — Poll Job Status Until Complete",
        )
        self.assertEqual(
            poll_payload,
            {
                "url": "https://api.example.com/jobs/42",
                "status_field": "status",
                "target_value": "completed",
                "poll_interval_seconds": "1",
                "max_attempts": "10",
            },
        )

    def test_direct_composition_derives_archive_mount_directionality(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation execution of archive-oriented command workers, helps with verifying that direct composition keeps source and destination mounts/paths in the correct roles even when the prompt names the destination first.

        Reference to Theory:
            Supports workstation compatibility with command-style trial prompts by preserving directional semantics in source/destination worker inputs rather than relying on literal order alone.

        Example Input Output:
            Input: `test_direct_composition_derives_archive_mount_directionality()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={
                "source_mount": "required input value",
                "source_relative_path": "required input value",
                "destination_mount": "required input value",
                "destination_relative_path": "required input value",
            },
            prompt="Create `realized-tests.zip` in mount `skill_tmp` from mount `skill_input` at `tests`.",
            skill_title="Python Commands 13 — Create Zip Archive",
        )
        self.assertEqual(
            payload,
            {
                "source_mount": "skill_input",
                "source_relative_path": "tests",
                "destination_mount": "skill_tmp",
                "destination_relative_path": "realized-tests.zip",
            },
        )

    def test_preferred_direct_composition_plan_selects_ansible_absolute_path_prompts(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompting over imported ansible trial skills, helps with verifying that obvious directory-creation and file-content prompts are claimed by the matching ansible workers instead of falling through to generic process execution.

        Reference to Theory:
            Verifies the workstation skill-first policy by keeping high-confidence ansible command prompts on the skill path before the LLM or host process tools intervene.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_selects_ansible_absolute_path_prompts()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        ansible_bundle = trials_dir / "ansible.skill.yaml"
        ansible_bundle.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "ansible" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported ansible skills when appropriate.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/ansible.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        create_plan = preferred_workstation_skill_invocation_plan(
            session=session,
            prompt="Create the directory `/tmp/ansible-demo` with mode `0755`.",
        )
        self.assertIsNotNone(create_plan)
        self.assertIn("Ensure Directory Exists", str(create_plan.get("skill_title", "")))
        self.assertEqual(
            create_plan.get("invocation_payload"),
            {
                "path": "/tmp/ansible-demo",
                "mode": "0755",
            },
        )
        write_plan = preferred_workstation_skill_invocation_plan(
            session=session,
            prompt="Write the text `ready=true` to `/tmp/ansible.env`.",
        )
        self.assertIsNotNone(write_plan)
        self.assertIn("Write File Content", str(write_plan.get("skill_title", "")))
        self.assertEqual(
            write_plan.get("invocation_payload", {}).get("path"),
            "/tmp/ansible.env",
        )
        self.assertIn(
            "ready=true",
            set(str(item) for item in dict(write_plan.get("invocation_payload", {})).values()),
        )

    def test_direct_composition_derives_deviceuser_payload_shape(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation execution of payload-oriented device workers, helps with verifying that direct composition can synthesize the execution payload expected by the selected worker title.

        Reference to Theory:
            Supports the workstation shell/worker split by keeping prompt interpretation in the shell while still invoking payload-oriented workers with explicit structured inputs.

        Example Input Output:
            Input: `test_direct_composition_derives_deviceuser_payload_shape()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        browser_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"url": "required input value", "browser": "required input value"},
            prompt="Open Google Chrome to `https://example.com`.",
            skill_title="Device User Capabilities 01 — Launch Browser At Specific URL",
        )
        self.assertEqual(
            browser_payload,
            {
                "url": "https://example.com",
                "browser": "Google Chrome",
            },
        )
        screenshot_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"payload": "execution input"},
            prompt="Take a screenshot and save it to mount `skill_tmp` at `deviceuser-screen.png`.",
            skill_title="Device User Capabilities 10 — Capture Screenshot To File",
        )
        self.assertEqual(
            screenshot_payload,
            {
                "payload": {
                    "mount": "skill_tmp",
                    "relative_path": "deviceuser-screen.png",
                }
            },
        )
        screenshot_python_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"dictstr_str": "number"},
            prompt="Take a screenshot and save it to mount `skill_tmp` at `deviceuser-screen.png`.",
            skill_title="Device User Capabilities 10 — Capture Screenshot To File / Python Function",
        )
        self.assertIsNone(screenshot_python_payload)

    def test_preferred_direct_composition_plan_prefers_top_symbol_search_worker(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompting over an imported trial store, helps with verifying that the shell can select one strong prompt-local worker plan before falling back to the model tool loop.

        Reference to Theory:
            Supports the workstation design choice to prefer direct worker composition before heavier reasoning when the prompt-local shortlist is already determinate.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_prefers_top_symbol_search_worker()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = SQLiteVectorArtifactStore()
        store.sqlite_path = self.skills_sqlite
        store.load_all_artifacts()
        store.persist_artifacts(
            [
                artifact_from_skill_document(
                    {
                        "schema": "bssc_skill.v2",
                        "kind": "ability",
                        "title": "Symbol Search Commands 01 — Find Symbol Occurrences / Symbol Search Commands 01 Find Symbol Occurrences",
                        "executor": "bash",
                        "inputs": {
                            "symbol": "required input value",
                            "root": "required input value",
                        },
                        "outputs": {
                            "result": "execution result",
                        },
                        "declaration": {
                            "intent": "Find symbol occurrences under one root path.",
                            "inputs": {
                                "symbol": "required input value",
                                "root": "required input value",
                            },
                            "outputs": {
                                "result": "execution result",
                            },
                            "authorities_requested": ["execute", "read"],
                            "authority_bounds": {
                                "execute": {
                                    "scope": "local_executor",
                                    "target": "bash_skill_runtime",
                                    "context": "explicit_user_prompt",
                                    "duration": "single_invocation",
                                    "triggering_conditions": ["user invokes skill"],
                                    "approval_class": "automatic",
                                },
                                "read": {
                                    "scope": "filesystem_mount",
                                    "target": "invocation_supplied_root",
                                    "context": "explicit_user_prompt",
                                    "duration": "single_invocation",
                                    "triggering_conditions": ["worker reads under requested root"],
                                    "approval_class": "automatic",
                                },
                            },
                            "data_classes_touched": ["public"],
                            "side_effects": ["local executor invocation", "filesystem read"],
                            "persistence_behavior": "none",
                            "invocation_rights": ["direct_user_invocation"],
                            "composition_rights": [],
                            "escalation_rights": [],
                            "approval_requirements": ["automatic"],
                            "risk_tier": "tier1_bounded_transform",
                            "executor_framework": "bash",
                        },
                        "shell": "grep -R --line-number \"$symbol\" \"$root\"",
                    }
                ),
            ],
            run_id="test:direct_symbol_search",
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        plan = preferred_workstation_skill_invocation_plan(
            session=session,
            prompt="Find every occurrence of the symbol `BSSCController` under `/Users/ravindranathakila/service/realized`.",
        )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(
            plan["skill_title"],
            "Symbol Search Commands 01 — Find Symbol Occurrences / Symbol Search Commands 01 Find Symbol Occurrences",
        )
        self.assertEqual(
            plan["invocation_payload"],
            {
                "symbol": "BSSCController",
                "root": "/Users/ravindranathakila/service/realized",
            },
        )

    def test_preferred_direct_composition_plan_uses_action_bonus_for_command_style_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompting over imported command-style workers, helps with verifying that direct composition can still pick the obvious worker when retrieval scores are low but the action/title match is clear.

        Reference to Theory:
            Supports workstation compatibility with the trial corpus by preferring prompt-local worker composition over generic tool fallback when the action semantics are already determinate.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_uses_action_bonus_for_command_style_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "Python Commands 03 — Write Text File",
                        "score": 3,
                        "inputs": {
                            "mount": "required input value",
                            "relative_path": "required input value",
                            "text": "required input value",
                        },
                    },
                    {
                        "title": "Python Commands 02 — Read Text File",
                        "score": 3,
                        "inputs": {
                            "mount": "required input value",
                            "relative_path": "required input value",
                        },
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Write `hello world` to mount `skill_tmp` at `python-suite.txt`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["skill_title"], "Python Commands 03 — Write Text File")
        self.assertEqual(
            plan["invocation_payload"],
            {
                "mount": "skill_tmp",
                "relative_path": "python-suite.txt",
                "text": "hello world",
            },
        )

    def test_preferred_direct_composition_plan_penalizes_copy_worker_for_move_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompting over near-neighbor file-operation skills, helps with verifying that an explicit move prompt does not stay on the copy worker just because the titles otherwise overlap heavily.

        Reference to Theory:
            Supports direct skill composition by keeping action semantics aligned with the prompt surface rather than treating all file-transfer workers as equivalent.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_penalizes_copy_worker_for_move_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "Python Commands 05 — Copy File",
                        "score": 6,
                        "inputs": {
                            "source_mount": "required input value",
                            "source_relative_path": "required input value",
                            "destination_mount": "required input value",
                            "destination_relative_path": "required input value",
                        },
                    },
                    {
                        "title": "Python Commands 06 — Move File",
                        "score": 5,
                        "inputs": {
                            "source_mount": "required input value",
                            "source_relative_path": "required input value",
                            "destination_mount": "required input value",
                            "destination_relative_path": "required input value",
                        },
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Move `python-readme.copy` from mount `skill_tmp` to mount `skill_output` at `python-readme.moved`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["skill_title"], "Python Commands 06 — Move File")
        self.assertEqual(
            plan["invocation_payload"],
            {
                "source_mount": "skill_tmp",
                "source_relative_path": "python-readme.copy",
                "destination_mount": "skill_output",
                "destination_relative_path": "python-readme.moved",
            },
        )

    def test_preferred_direct_composition_plan_prefers_paginated_get_worker_for_fetch_page_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation direct composition over near-neighbor API workers, helps with verifying that a paginated fetch prompt selects the paginated GET worker instead of a mutating JSON-body worker with a higher retrieval score.

        Reference to Theory:
            Supports direct skill composition by keeping fetch-style prompts on read-oriented workers when the prompt surface already names page and page-size semantics.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_prefers_paginated_get_worker_for_fetch_page_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "API Client Commands 04 — Put Json Body / Api Client Commands 04 Put Json Body",
                        "score": 11,
                        "inputs": {
                            "url": "required input value",
                            "json_text": "required input value",
                        },
                    },
                    {
                        "title": "API Client Commands 09 — Get Paginated Json / Api Client Commands 09 Get Paginated Json",
                        "score": 8,
                        "inputs": {
                            "url": "required input value",
                            "page": "required input value",
                            "per_page": "required input value",
                        },
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Fetch page `2` with page size `50` from `https://api.example.com/items`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(
            plan["skill_title"],
            "API Client Commands 09 — Get Paginated Json / Api Client Commands 09 Get Paginated Json",
        )
        self.assertEqual(
            plan["invocation_payload"],
            {
                "url": "https://api.example.com/items",
                "page": "2",
                "per_page": "50",
            },
        )

    def test_preferred_direct_composition_plan_prefers_remove_worker_for_remove_prompt(self) -> None:
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "Bash Commands 09 — Remove File",
                        "score": 5,
                        "inputs": {
                            "path": "required input value",
                        },
                    },
                    {
                        "title": "Bash Commands 07 — Copy File",
                        "score": 6,
                        "inputs": {
                            "source_path": "required input value",
                            "destination_path": "required input value",
                        },
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Remove `/tmp/hosts.moved`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["skill_title"], "Bash Commands 09 — Remove File")
        self.assertEqual(plan["invocation_payload"], {"path": "/tmp/hosts.moved"})

    def test_preferred_direct_composition_plan_prefers_write_text_file_for_plain_text_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation direct composition over adjacent file-writing workers, helps with verifying that a plain-text `.txt` prompt selects the text writer instead of a JSON writer with a higher retrieval score.

        Reference to Theory:
            Supports direct skill composition by keeping worker selection aligned with the concrete prompt substrate rather than over-weighting nearby structured-data titles.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_prefers_write_text_file_for_plain_text_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "Python Commands 09 — Write Json File / Python Commands 09 Write Json File",
                        "score": 11,
                        "inputs": {
                            "mount": "required input value",
                            "relative_path": "required input value",
                            "json_text": "required input value",
                        },
                    },
                    {
                        "title": "Python Commands 03 — Write Text File",
                        "score": 8,
                        "inputs": {
                            "mount": "required input value",
                            "relative_path": "required input value",
                            "text": "required input value",
                        },
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Write `hello world` to mount `skill_tmp` at `python-suite.txt`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["skill_title"], "Python Commands 03 — Write Text File")
        self.assertEqual(
            plan["invocation_payload"],
            {
                "mount": "skill_tmp",
                "relative_path": "python-suite.txt",
                "text": "hello world",
            },
        )

    def test_preferred_direct_composition_plan_prefers_launch_browser_worker_for_url_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation direct composition over imported device-user workers, helps with verifying that a browser-launch prompt selects the specific launch-browser worker instead of a looser browser-related worker.

        Reference to Theory:
            Verifies the workstation shell can stay on the direct worker path by using a narrow semantic tiebreak rather than falling back to the generic tool loop.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_prefers_launch_browser_worker_for_url_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Open Google Chrome to `https://example.com`.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "Device User Capabilities 01 — Launch Browser At Specific URL",
                        "inputs": {"url": "required input value", "browser": "required input value"},
                        "score": 6,
                    },
                    {
                        "title": "Device User Capabilities 06 — Search The Web In Browser",
                        "inputs": {"payload": "execution input"},
                        "score": 6,
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Open Google Chrome to `https://example.com`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["skill_title"], "Device User Capabilities 01 — Launch Browser At Specific URL")
        self.assertEqual(plan["invocation_payload"], {"url": "https://example.com", "browser": "Google Chrome"})

    def test_preferred_direct_composition_plan_prefers_mount_aware_screenshot_worker(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation direct composition over imported device-user workers, helps with verifying that a screenshot prompt targeting a governed mount prefers the mount-aware Python worker over the unguided shell example worker.

        Reference to Theory:
            Verifies the workstation shell keeps prompt-local worker composition aligned with governed output targeting instead of choosing a looser example worker on a retrieval-score tie.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_prefers_mount_aware_screenshot_worker()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "Device User Capabilities 10 — Capture Screenshot To File / Device User Capabilities 10 Capture Screenshot To File",
                        "inputs": {"payload": "execution input"},
                        "score": 11,
                        "executor_framework": "bash",
                    },
                    {
                        "title": "Device User Capabilities 10 — Capture Screenshot To File / Python Function",
                        "inputs": {"payload": "execution input"},
                        "score": 11,
                        "executor_framework": "python3",
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Take a screenshot and save it to mount `skill_tmp` at `deviceuser-screen.png`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["skill_title"], "Device User Capabilities 10 — Capture Screenshot To File / Python Function")
        self.assertEqual(
            plan["invocation_payload"],
            {
                "payload": {
                    "mount": "skill_tmp",
                    "relative_path": "deviceuser-screen.png",
                }
            },
        )

    def test_preferred_direct_composition_plan_rejects_title_only_payload_for_malformed_screenshot_worker(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct composition over one good worker and one malformed learned sibling that only shares the title surface, helps with verifying that title-based payload inference does not override the declared input contract.

        Reference to Theory:
            Supports robust worker selection by requiring title-derived payloads to still align with the worker's declared inputs instead of treating lexical title overlap as sufficient.

        Example Input Output:
            Input: `test_preferred_direct_composition_plan_rejects_title_only_payload_for_malformed_screenshot_worker()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use installed trial skills when appropriate.",
            )
        )
        with patch(
            "workstation.direct_composition.workstation_prompt_skill_shortlist_payload",
            return_value={
                "skills": [
                    {
                        "title": "Device User Capabilities 10 — Capture Screenshot To File / Python Function",
                        "inputs": {"dictstr_str": "number"},
                        "score": 12,
                        "executor_framework": "python3",
                    },
                    {
                        "title": "Device User Capabilities 10 — Capture Screenshot To File / Device User Capabilities 10 Capture Screenshot To File",
                        "inputs": {"payload": "execution input"},
                        "score": 11,
                        "executor_framework": "bash",
                    },
                ]
            },
        ):
            plan = preferred_workstation_skill_invocation_plan(
                session=session,
                prompt="Take a screenshot and save it to mount `skill_tmp` at `deviceuser-screen.png`.",
            )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(
            plan["skill_title"],
            "Device User Capabilities 10 — Capture Screenshot To File / Device User Capabilities 10 Capture Screenshot To File",
        )
        self.assertEqual(
            plan["invocation_payload"],
            {
                "payload": {
                    "mount": "skill_tmp",
                    "relative_path": "deviceuser-screen.png",
                }
            },
        )

    def test_derive_workstation_invocation_payload_returns_none_when_declared_inputs_have_no_prompt_binding(self) -> None:
        """
        High Level Purpose:
            In circumstances like malformed learned sibling skills whose declared inputs do not align with the prompt surface, helps with verifying that direct composition treats the worker as non-derivable instead of synthesizing an empty payload.

        Reference to Theory:
            Prevents title-only lexical matches from being mistaken for executable plans when no declared leaf/input mapping can actually be grounded from the prompt.

        Example Input Output:
            Input: `test_derive_workstation_invocation_payload_returns_none_when_declared_inputs_have_no_prompt_binding()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"dictstr_str": "number"},
            prompt="Take a screenshot and save it to mount `skill_tmp` at `deviceuser-screen.png`.",
            skill_title="Device User Capabilities 10 — Capture Screenshot To File / Python Function",
        )
        self.assertIsNone(payload)

    def test_resolve_workstation_skill_accepts_shortened_trial_title(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation invocation over imported trial workers, helps with verifying that a shortened natural-language title can still resolve to one unique installed worker.

        Reference to Theory:
            Supports workstation compatibility with imported trial corpora by letting the shell resolve one pluggable worker without requiring the model to reproduce duplicated title suffixes verbatim.

        Example Input Output:
            Input: `test_resolve_workstation_skill_accepts_shortened_trial_title()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = SQLiteVectorArtifactStore()
        store.sqlite_path = self.skills_sqlite
        store.load_all_artifacts()
        store.persist_artifacts(
            [
                artifact_from_skill_document(
                    {
                        "schema": "bssc_skill.v2",
                        "kind": "ability",
                        "title": "Symbol Search Commands 01 — Find Symbol Occurrences / Symbol Search Commands 01 Find Symbol Occurrences",
                        "executor": "bash",
                        "inputs": {
                            "symbol": "required input value",
                            "root": "required input value",
                        },
                        "outputs": {
                            "result": "execution result",
                        },
                        "declaration": {
                            "intent": "Find symbol occurrences under one root path.",
                            "inputs": {
                                "symbol": "required input value",
                                "root": "required input value",
                            },
                            "outputs": {
                                "result": "execution result",
                            },
                            "authorities_requested": ["execute", "read"],
                            "authority_bounds": {
                                "execute": {
                                    "scope": "local_executor",
                                    "target": "bash_skill_runtime",
                                    "context": "explicit_user_prompt",
                                    "duration": "single_invocation",
                                    "triggering_conditions": ["user invokes skill"],
                                    "approval_class": "automatic",
                                },
                                "read": {
                                    "scope": "filesystem_mount",
                                    "target": "invocation_supplied_root",
                                    "context": "explicit_user_prompt",
                                    "duration": "single_invocation",
                                    "triggering_conditions": ["worker reads under requested root"],
                                    "approval_class": "automatic",
                                },
                            },
                            "data_classes_touched": ["public"],
                            "side_effects": ["local executor invocation", "filesystem read"],
                            "persistence_behavior": "none",
                            "invocation_rights": ["direct_user_invocation"],
                            "composition_rights": [],
                            "escalation_rights": [],
                            "approval_requirements": ["automatic"],
                            "risk_tier": "tier1_bounded_transform",
                            "executor_framework": "bash",
                        },
                        "shell": "grep -R --line-number \"$symbol\" \"$root\"",
                    }
                ),
            ],
            run_id="test:shortened_title_resolution",
        )
        resolved = resolve_workstation_skill(
            skill_title="Symbol Search Commands 01 — Find Symbol Occurrences",
            skill_store_path=self.skills_sqlite,
        )
        self.assertIsNotNone(resolved)
        assert resolved is not None
        artifact, source = resolved
        self.assertEqual(
            artifact.title,
            "Symbol Search Commands 01 — Find Symbol Occurrences / Symbol Search Commands 01 Find Symbol Occurrences",
        )
        self.assertEqual(source["source_kind"], "attached_skill_store")

    def test_resolve_workstation_skill_prefers_exact_longer_title_over_shorter_prefix_match(self) -> None:
        """
        High Level Purpose:
            In circumstances like builtin-worker resolution alongside installed skills, helps with verifying that an exact longer requested title is not incorrectly shadowed by one shorter installed title that merely shares the prefix.

        Reference to Theory:
            Supports the workstation shell / pluggable-worker model by allowing shortened title matching only as user-query convenience rather than as ambiguous reverse-prefix resolution.

        Example Input Output:
            Input: `test_resolve_workstation_skill_prefers_exact_longer_title_over_shorter_prefix_match()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        resolved = resolve_workstation_skill(
            skill_title="Workstation Greeting From Wasm",
            skill_store_path=self.skills_sqlite,
        )
        self.assertIsNotNone(resolved)
        assert resolved is not None
        artifact, source = resolved
        self.assertEqual(artifact.title, "Workstation Greeting From Wasm")
        self.assertEqual(source["source_kind"], "builtin_workstation")

    def test_workstation_skill_catalog_excludes_policy_records(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation discovery over a shared skill home, helps with verifying that governance records do not appear as runnable workers in the workstation skill catalog.

        Reference to Theory:
            Supports the workstation shell / pluggable-worker model by keeping worker discovery focused on knowledge and ability artifacts instead of governance envelopes.

        Example Input Output:
            Input: `test_workstation_skill_catalog_excludes_policy_records()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = SQLiteVectorArtifactStore()
        store.sqlite_path = self.skills_sqlite
        store.load_all_artifacts()
        store.persist_artifacts(
            [
                artifact_from_skill_document(workstation_default_policy_payload()),
                artifact_from_skill_document(
                    {
                        "schema": "bssc_skill.v1",
                        "kind": "knowledge",
                        "title": "Catalog Visible Skill",
                        "answer": "visible",
                    }
                ),
            ],
            run_id="test:catalog_policy_filter",
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Inspect the workstation skill catalog.",
            )
        )
        titles = {
            item["title"]
            for item in execute_workstation_capability(session, "ws.skill.catalog", {})["skills"]
        }
        self.assertIn("Catalog Visible Skill", titles)
        self.assertNotIn(WORKSTATION_DEFAULT_POLICY_TITLE, titles)

    def test_import_workstation_skill_file_keeps_vector_indexing_off_for_skill_store(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation bundle import performance hardening, helps with verifying that workstation skill imports do not initialize sqlite-vec or the embedding encoder when the attached workstation store is intentionally vector-disabled.

        Reference to Theory:
            Verifies the workstation skill-home seam keeps its current title/catalog-driven behavior without paying unrelated vector-index startup cost during import.

        Example Input Output:
            Input: `test_import_workstation_skill_file_keeps_vector_indexing_off_for_skill_store()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        source_file = self.workspace / "trials" / "demo-import.skill.yaml"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Imported Skill",
                    "answer: hello from imported skill",
                ]
            )
            + "\n"
        )
        canonical_export_path = self.root / "exports" / "demo-import.skill.yaml"
        previous_vector_mode = os.environ.get("STATE_VECTOR_MODE")
        real_import_module = importlib.import_module

        def guarded_import(module_name: str, *args: object, **kwargs: object) -> object:
            if module_name == "sqlite_vec":
                raise AssertionError("sqlite_vec should stay unused for workstation skill-store import")
            return real_import_module(module_name, *args, **kwargs)

        try:
            os.environ.pop("STATE_VECTOR_MODE", None)
            with (
                patch("store.importlib.import_module", side_effect=guarded_import),
                patch("store.EmbeddingGemmaEncoder", side_effect=AssertionError("embedding encoder should stay unused for workstation skill-store import")),
            ):
                payload = import_workstation_skill_file(
                    skill_store_path=self.skills_sqlite,
                    source_file=source_file,
                    canonical_export_path=canonical_export_path,
                )
        finally:
            if previous_vector_mode is None:
                os.environ.pop("STATE_VECTOR_MODE", None)
            else:
                os.environ["STATE_VECTOR_MODE"] = previous_vector_mode

        self.assertEqual(payload.get("status"), "ok")
        self.assertTrue(canonical_export_path.exists())
        store = workstation_skill_store(self.skills_sqlite)
        self.assertEqual(store.vector_mode_override, "off")
        self.assertFalse(store.vector_enabled())

    def test_workstation_governance_inventory_filters_transient_bundle_policies(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared workstation skill-home governance loading, helps with verifying that bundle-local export policies do not remain active alongside the durable workstation skill-home policy.

        Reference to Theory:
            Supports workstation compatibility with many imported bundles by preventing transient bundle installation policies from contaminating shared worker admission.

        Example Input Output:
            Input: `test_workstation_governance_inventory_filters_transient_bundle_policies()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = SQLiteVectorArtifactStore()
        store.sqlite_path = self.skills_sqlite
        store.load_all_artifacts()
        store.persist_artifacts(
            [
                artifact_from_skill_document(
                    {
                        "schema": "bssc_skill.v2",
                        "kind": "policy",
                        "title": "Local Bundle Admission Policy / abc123def456",
                        "policy": {
                            "intent": "Admit the governed skills packaged in this bundle on a fresh system.",
                            "target_kinds": ["knowledge", "ability"],
                            "max_risk_tier": "tier1_bounded_transform",
                            "allowed_authorities": ["read"],
                            "denied_authorities": [],
                            "allowed_executors": ["python3"],
                            "required_approval_for_risk_tiers": {},
                        },
                    }
                ),
            ],
            run_id="test:transient_policy",
        )
        inventory = workstation_governance_inventory(store)
        policy_titles = [artifact.title for artifact in inventory["policies"]]
        self.assertIn(WORKSTATION_DEFAULT_POLICY_TITLE, policy_titles)
        self.assertNotIn("Local Bundle Admission Policy / abc123def456", policy_titles)

    def test_skill_invoke_recomputes_current_lifecycle_for_stale_imported_worker(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation use against an older shared skill home, helps with verifying that invocation follows the current workstation governance snapshot instead of stale stored lifecycle state from an earlier rejected import.

        Reference to Theory:
            Supports workstation compatibility with reused skill homes by making the shell recompute effective worker admission before invoking a pluggable worker.

        Example Input Output:
            Input: `test_skill_invoke_recomputes_current_lifecycle_for_stale_imported_worker()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = SQLiteVectorArtifactStore()
        store.sqlite_path = self.skills_sqlite
        store.load_all_artifacts()
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Stale Lifecycle Greeting",
                "executor": "python3",
                "entrypoint": "main",
                "outputs": {
                    "greeting": "greeting",
                },
                "declaration": {
                    "intent": "Return a greeting.",
                    "inputs": {},
                    "outputs": {"greeting": "greeting"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["local executor invocation"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                    "executor_framework": "python3",
                },
                "python": "\n".join(
                    [
                        "def main(payload: dict | None = None) -> dict:",
                        "    return {'status': 'ok', 'answer': 'hello from stale lifecycle worker', 'result': {'greeting': 'hello from stale lifecycle worker'}}",
                    ]
                ),
            }
        )
        content = dict(artifact.content)
        content["skill_admission"] = {
            "status": "rejected",
            "admitted": False,
            "rationale": "stale import state",
            "policy_titles": ["Local Bundle Admission Policy / old"],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": "2026-04-01T00:00:00+00:00",
        }
        content["skill_lifecycle"] = {
            "review_status": "pending_review",
            "admission_status": "rejected",
            "installation_status": "blocked",
            "activation_status": "inactive",
            "trust_status": "restricted",
            "quarantine_status": "clear",
            "status_reason": "stale rejected state",
            "updated_at": "2026-04-01T00:00:00+00:00",
        }
        artifact.content = content
        store.persist_artifacts([artifact], run_id="test:stale_lifecycle_worker")
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use stale imported skills safely.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {"skill_title": "Stale Lifecycle Greeting"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["executor_framework"], "python3")
        self.assertTrue(result["nested_effect_traces"])
        self.assertTrue(result["nested_effect_traces"][0]["decision"]["allowed"])
        self.assertEqual(result["nested_effect_traces"][0]["admission"]["status"], "admitted")
        self.assertEqual(result["nested_effect_traces"][0]["lifecycle"]["trust_status"], "trusted")

    def test_skill_import_persists_to_skill_home_and_refreshes_catalog(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation skill lifecycle testing, helps with verifying that the workstation can import one portable skill bundle into the persistent skill home and refresh the discovery catalog.

        Reference to Theory:
            Verifies the workstation shell can manage pluggable workers through governed import/export flows instead of bypassing the existing skill infrastructure.

        Example Input Output:
            Input: `test_skill_import_persists_to_skill_home_and_refreshes_catalog()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        skill_file = self.workspace / "demo_import_skill.yaml"
        skill_file.write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Imported Workstation Greeting",
                    "answer: hello from imported workstation skill",
                    "",
                ]
            )
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Import a workstation skill.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {"source_target": "main", "path": "demo_import_skill.yaml"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "skills")
        self.assertTrue(Path(result["staged_import_path"]).exists())
        self.assertTrue(Path(result["canonical_export_path"]).exists())
        catalog = json.loads((self.root / "SKILLS.json").read_text())
        titles = [item["title"] for item in catalog["skills"]]
        self.assertIn("Imported Workstation Greeting", titles)
        invoke_result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {"skill_title": "Imported Workstation Greeting"},
        )
        self.assertEqual(invoke_result["status"], "ok")
        self.assertEqual(invoke_result["answer"], "hello from imported workstation skill")

    def test_skill_export_writes_portable_bundle_to_exports_attachment(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation skill lifecycle testing, helps with verifying that the workstation can export one governed worker from the persistent skill home into the standard exports attachment.

        Reference to Theory:
            Verifies worker exchange remains explicit and portable outside the workstation session boundary.

        Example Input Output:
            Input: `test_skill_export_writes_portable_bundle_to_exports_attachment()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Export the installed skill.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.export",
            {"skill_title": "Workstation Greeting"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["destination_target"], "skills_exports")
        exported_path = Path(result["destination_path"])
        self.assertTrue(exported_path.exists())
        self.assertIn("Workstation Greeting", exported_path.read_text())

    def test_skill_export_can_write_to_workspace_relative_path_with_short_title(self) -> None:
        """
        High Level Purpose:
            In circumstances like conversational workstation export requests, helps with verifying that one shortened unique skill title can be exported directly into the attached workspace even when the model names a non-attachment path segment like `exports`.

        Reference to Theory:
            Verifies the workstation exchange surface follows user intent for workspace-relative export targets instead of forcing all exports through the persistent skill-home attachment vocabulary.

        Example Input Output:
            Input: `test_skill_export_can_write_to_workspace_relative_path_with_short_title()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Export an imported Python skill into the workspace.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        result = execute_workstation_capability(
            session,
            "ws.skill.export",
            {
                "skill_title": "Python Commands 02 — Read Text File",
                "destination_target": "exports",
                "destination_path": "exports/python-read-text-file.yaml",
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["destination_target"], "main")
        exported_path = Path(result["destination_path"])
        self.assertEqual(exported_path, (self.workspace / "exports" / "python-read-text-file.yaml").resolve())
        self.assertTrue(exported_path.exists())
        self.assertIn("Python Commands 02", exported_path.read_text())

    def test_skill_invoke_accepts_top_level_declared_inputs(self) -> None:
        """
        High Level Purpose:
            In circumstances like model-produced workstation tool calls, helps with verifying that top-level declared skill inputs are accepted even when the model omits the nested `invocation_payload` wrapper.

        Reference to Theory:
            Verifies the workstation shell tolerates natural tool-call shapes while still driving the imported skill path explicitly.

        Example Input Output:
            Input: `test_skill_invoke_accepts_top_level_declared_inputs()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported Python file skills.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        approval_required = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Python Commands 03 — Write Text File",
                "mount": "main",
                "relative_path": "exports/summary.txt",
                "text": "Classes: BSSCController, DemoRunner",
            },
        )
        self.assertEqual(approval_required["status"], "approval_required")
        self.assertEqual(
            approval_required["invocation_request"]["skill_title"],
            "Python Commands 03 — Write Text File / Python Commands 03 Write Text File",
        )
        self.assertEqual(approval_required["invocation_request"]["invocation_mode"], "direct_named")
        self.assertEqual(approval_required["invocation_result"]["status"], "approval_required")
        self.assertEqual(
            approval_required["missing_delegation"],
            [
                {
                    "capability": "ws.fs.write",
                    "target": "main",
                    "rationale": "Need to expose the requested workstation mount to the invoked skill.",
                }
            ],
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Python Commands 03 — Write Text File",
                "mount": "main",
                "relative_path": "exports/summary.txt",
                "text": "Classes: BSSCController, DemoRunner",
                "approved_delegation": [{"capability": "ws.fs.write", "target": "main"}],
                "approved_delegation_scope": "one_invocation",
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["invocation_request"]["bindings"][0]["status"], "provided")
        self.assertEqual(result["invocation_result"]["status"], "ok")
        written_path = (self.workspace / "exports" / "summary.txt").resolve()
        self.assertTrue(written_path.exists())
        self.assertEqual(written_path.read_text().strip(), "Classes: BSSCController, DemoRunner")

    def test_skill_invoke_derives_python_read_inputs_from_plain_relative_path_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like explicit workstation skill usage over imported Python file workers, helps with verifying that a plain relative path in the prompt is enough to derive the worker payload without requiring backticks or a hand-built payload object.

        Reference to Theory:
            Verifies the workstation skill-first path remains usable in ordinary chat phrasing for file-oriented imported skills.

        Example Input Output:
            Input: `test_skill_invoke_derives_python_read_inputs_from_plain_relative_path_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported Python file skills.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Python Commands 02 — Read Text File",
                "semantic_unit": "Use the Python read-text-file skill to read src/demo.py and show me the contents.",
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("class BSSCController", result["answer"])

    def test_fs_read_can_access_session_discovery_files(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation discovery-file access, helps with verifying that the session attachment exposes workstation-root files such as SKILLS.json to normal file reads.

        Reference to Theory:
            Verifies the workstation discovery surface remains explicit and addressable rather than hidden behind the workspace attachment.

        Example Input Output:
            Input: `test_fs_read_can_access_session_discovery_files()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use the installed skills.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.fs.read",
            {"target": "session", "path": "SKILLS.json"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("Workstation Greeting", result["content"])

    def test_fs_read_workspace_target_falls_back_to_session_discovery_file_when_needed(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation model behavior, helps with verifying that a mistaken attempt to read SKILLS.json from the workspace attachment still resolves to the workstation session discovery file.

        Reference to Theory:
            Verifies a pragmatic compatibility fallback so the workstation discovery surface remains usable even when the model chooses the wrong attachment for a known session file.

        Example Input Output:
            Input: `test_fs_read_workspace_target_falls_back_to_session_discovery_file_when_needed()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use the installed skills.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.fs.read",
            {"target": "main", "path": "SKILLS.json"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("Workstation Greeting", result["content"])

    def test_boundary_contract_normalizes_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompt normalization testing, helps with verifying that a natural-language prompt becomes a boundary-complete task contract.

        Reference to Theory:
            Verifies reuse of BSSC boundary-shape completeness theory inside the workstation prompt model.

        Example Input Output:
            Input: `test_boundary_contract_normalizes_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        contract = normalize_prompt_to_task_boundary_contract(
            "Open the browser, download the quarterly report, and summarize it."
        )
        self.assertIn("download file", contract.side_effects)
        self.assertIn("summary", contract.output_values)
        self.assertIn("report URL or search target", contract.missing_requirements)
        self.assertTrue(contract.boundary_shape)

    def test_workstation_tool_names_are_provider_safe_and_reversible(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation provider-compatibility regression testing, helps with verifying that stable workstation capability names are translated into provider-safe tool names and back again.

        Reference to Theory:
            Verifies the host-owned workstation driver adapts the capability surface to provider constraints without changing the stable workstation capability vocabulary.

        Example Input Output:
            Input: `test_workstation_tool_names_are_provider_safe_and_reversible()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(workstation_tool_wire_name("ws.repo.tree"), "ws__repo__tree")
        self.assertEqual(workstation_tool_capability_name("ws__repo__tree"), "ws.repo.tree")
        definitions, reverse_map = normalize_workstation_tool_definitions_for_provider(
            [
                {
                    "type": "function",
                    "function": {
                        "name": "ws.repo.tree",
                        "description": "tree",
                        "parameters": {"type": "object"},
                    },
                }
            ]
        )
        self.assertEqual(definitions[0]["function"]["name"], "ws__repo__tree")
        self.assertEqual(reverse_map["ws__repo__tree"], "ws.repo.tree")

    def test_workstation_llm_turn_retries_without_temperature_when_model_rejects_it(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation provider-compatibility regression testing, helps with verifying that the host-owned LLM driver retries without `temperature` when the provider rejects it for the selected model.

        Reference to Theory:
            Verifies that workstation LLM prompting remains host-owned and provider-compatible without changing the stable workstation prompt/tool contract.

        Example Input Output:
            Input: `test_workstation_llm_turn_retries_without_temperature_when_model_rejects_it()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report = run_workstation_openai_turn(
            session=WorkstationSession.from_dict(
                launch_workstation_session(
                    root_path=self.root,
                    workspace_path=self.workspace,
                    initial_task="Inspect the project.",
                )
            ),
            task_contract=normalize_prompt_to_task_boundary_contract("Inspect the workspace."),
            prompt="Inspect the workspace.",
            message_history=[],
            tool_definitions=[],
            tool_executor=lambda _name, _arguments: {},
            model="test-model",
            client=_RetryThenSucceedClient(),
        )
        self.assertIn("Fallback temperature path succeeded.", report["assistant_text"])

    def test_workstation_llm_turn_retries_transient_server_error(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation provider hardening, helps with verifying that the host-owned workstation driver retries a transient provider 500 instead of failing the whole turn immediately.

        Reference to Theory:
            Verifies reliability handling stays at the workstation host boundary rather than leaking transient provider failures into workstation or skill logic.

        Example Input Output:
            Input: `test_workstation_llm_turn_retries_transient_server_error()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report = run_workstation_openai_turn(
            session=WorkstationSession.from_dict(
                launch_workstation_session(
                    root_path=self.root,
                    workspace_path=self.workspace,
                    initial_task="Inspect the project.",
                )
            ),
            task_contract=normalize_prompt_to_task_boundary_contract("Inspect the workspace."),
            prompt="Inspect the workspace.",
            message_history=[],
            tool_definitions=[],
            tool_executor=lambda _name, _arguments: {},
            model="test-model",
            client=_RetryOnServerErrorClient(),
        )
        self.assertIn("Transient provider retry succeeded.", report["assistant_text"])

    def test_single_workspace_session_accepts_root_like_target(self) -> None:
        """
        High Level Purpose:
            In circumstances like real-model workstation usage, helps with verifying that a one-workspace session accepts root-like target values such as `/` instead of failing on attachment-name exactness.

        Reference to Theory:
            Verifies the workstation attachment model stays usable for live LLM tool calls while still remaining attachment-scoped.

        Example Input Output:
            Input: `test_single_workspace_session_accepts_root_like_target()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
                initial_task="Inspect the project.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.repo.tree",
            {"target": "/"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "main")

    def test_single_workspace_session_accepts_workspace_alias_target(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation tool use, helps with verifying that common workspace-like aliases such as `/workspace` resolve to the single attached workspace instead of failing on exact attachment naming.

        Reference to Theory:
            Verifies the workstation attachment model remains robust for real model tool calls while still staying attachment-scoped.

        Example Input Output:
            Input: `test_single_workspace_session_accepts_workspace_alias_target()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
                initial_task="Inspect the project.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.repo.tree",
            {"target": "/workspace"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "main")

    def test_single_workspace_session_accepts_dot_slash_target(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation tool planning, helps with verifying that `./` resolves to the single attached workspace instead of failing as an unknown attachment.

        Reference to Theory:
            Verifies the workstation shell tolerates common root-like attachment spellings that models emit during repository inspection.

        Example Input Output:
            Input: `test_single_workspace_session_accepts_dot_slash_target()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
                initial_task="Inspect the project.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.repo.tree",
            {"target": "./"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "main")

    def test_single_workspace_session_accepts_root_alias_target(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation tool planning, helps with verifying that bare aliases such as `root` resolve to the single attached workspace.

        Reference to Theory:
            Verifies the workstation shell keeps single-workspace sessions usable even when the model invents a generic repository-root alias.

        Example Input Output:
            Input: `test_single_workspace_session_accepts_root_alias_target()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
                initial_task="Inspect the project.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.repo.tree",
            {"target": "root"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "main")

    def test_skill_invoke_executes_installed_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation-to-skill integration testing, helps with verifying that the workstation can invoke one installed governed skill from an attached skill store.

        Reference to Theory:
            Verifies the first pluggable-worker path where the workstation shell invokes a reusable installed skill explicitly.

        Example Input Output:
            Input: `test_skill_invoke_executes_installed_skill()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use the installed skills.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {"skill_title": "Workstation Greeting"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["answer"], "hello from skill")
        self.assertEqual(result["skill_title"], "Workstation Greeting")

    def test_skill_compose_executes_explicit_two_step_mapping_plan(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation skill-composition execution testing, helps with verifying that one explicit multi-step plan can feed the structured output of one skill into the input of another through the leaf composition layer.

        Reference to Theory:
            Verifies the workstation can execute first-class composition plans over governed skills instead of relying only on prompt heuristics or answer-text chaining.

        Example Input Output:
            Input: `test_skill_compose_executes_explicit_two_step_mapping_plan()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Emit Text",
            inputs={"text": "text input"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        self._persist_python_ability_skill(
            title="Consume Text",
            inputs={"text": "text input"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"consumed:{payload.get('text', '')}\"}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Compose installed skills.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.compose",
            {
                "steps": [
                    {
                        "step_id": "emit",
                        "skill_title": "Emit Text",
                        "bindings": [
                            {
                                "target_region": "a",
                                "target_path": "/a/text",
                                "source_root_name": "text",
                                "source_root_region": "a",
                            }
                        ],
                    },
                    {
                        "step_id": "consume",
                        "skill_title": "Consume Text",
                        "bindings": [
                            {
                                "target_region": "a",
                                "target_path": "/a/text",
                                "source_step_id": "emit",
                                "source_region": "d",
                                "source_path": "/d/text",
                                "mapper": {"kind": "identity"},
                            }
                        ],
                    },
                ],
                "root_inputs": {
                    "text": "hello world",
                },
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["capability"], "ws.skill.compose")
        self.assertEqual(result["final_output_step"], "consume")
        self.assertEqual(result["final_output"], {"result": "consumed:hello world"})
        self.assertIn("consumed:hello world", result["answer"])
        self.assertEqual(result["requested_skill_titles"], ["Emit Text", "Consume Text"])
        self.assertEqual(result["steps"][0]["parsed_output"], {"text": "hello world"})
        self.assertEqual(result["steps"][1]["parsed_output"], {"result": "consumed:hello world"})

    def test_skill_compose_accepts_workflow_plan_projection(self) -> None:
        """
        High Level Purpose:
            In circumstances like the first Blend workflow-object cut, helps with verifying that `ws.skill.compose` accepts a typed `workflow_plan` projection without requiring legacy top-level `steps`.

        Reference to Theory:
            Verifies the additive `BlendWorkflowPlan` seam projects onto the already-working compose executor instead of replacing it.

        Example Input Output:
            Input: `test_skill_compose_accepts_workflow_plan_projection()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Emit Text",
            inputs={"text": "text input"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        self._persist_python_ability_skill(
            title="Consume Text",
            inputs={"text": "text input"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"consumed:{payload.get('text', '')}\"}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Compose skills through workflow projections.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.compose",
            {
                "workflow_plan": {
                    "workflow_kind": "skill_compose",
                    "steps": [
                        {
                            "step_id": "emit",
                            "operator_kind": "skill",
                            "operator_name": "Emit Text",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/text",
                                    "source_root_name": "text",
                                    "source_root_region": "a",
                                }
                            ],
                        },
                        {
                            "step_id": "consume",
                            "operator_kind": "skill",
                            "operator_name": "Consume Text",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/text",
                                    "source_step_id": "emit",
                                    "source_region": "d",
                                    "source_path": "/d/text",
                                    "mapper": {"kind": "identity"},
                                }
                            ],
                        },
                    ],
                    "root_inputs": {"text": "hello workflow"},
                    "final_output_step": "consume",
                    "metadata": {"target": "skills"},
                }
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["final_output"], {"result": "consumed:hello workflow"})
        self.assertEqual(result["workflow_plan"]["final_output_step"], "consume")
        self.assertEqual(result["workflow_run"]["status"], "ok")
        self.assertEqual(result["workflow_run"]["final_output"], {"result": "consumed:hello workflow"})
        self.assertTrue(result["workflow_id"].startswith("bwf_plan_"))
        self.assertTrue(result["workflow_run_id"].startswith("bwf_run_"))
        self.assertEqual(result["workflow_store"]["workflow_id"], result["workflow_id"])
        self.assertEqual(result["workflow_store"]["workflow_run_id"], result["workflow_run_id"])
        self.assertTrue(Path(result["workflow_store"]["plan_path"]).exists())
        self.assertTrue(Path(result["workflow_store"]["run_path"]).exists())
        self.assertTrue(Path(result["workflow_store"]["index_path"]).exists())
        self.assertEqual(
            [step["operator_name"] for step in result["workflow_plan"]["steps"]],
            ["Emit Text", "Consume Text"],
        )

    def test_workflow_list_and_get_surface_persisted_workflow_objects(self) -> None:
        self._persist_python_ability_skill(
            title="Emit Text",
            inputs={"text": "text input"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        self._persist_python_ability_skill(
            title="Consume Text",
            inputs={"text": "text input"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"consumed:{payload.get('text', '')}\"}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                    "ws.workflow.list",
                    "ws.workflow.get",
                ),
                initial_task="Inspect persisted workflows.",
            )
        )
        run_result = execute_workstation_capability(
            session,
            "ws.workflow.run",
            {
                "workflow_plan": {
                    "workflow_kind": "skill_compose",
                    "steps": [
                        {
                            "step_id": "emit",
                            "operator_kind": "skill",
                            "operator_name": "Emit Text",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/text",
                                    "source_root_name": "text",
                                    "source_root_region": "a",
                                }
                            ],
                        },
                        {
                            "step_id": "consume",
                            "operator_kind": "skill",
                            "operator_name": "Consume Text",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/text",
                                    "source_step_id": "emit",
                                    "source_region": "d",
                                    "source_path": "/d/text",
                                    "mapper": {"kind": "identity"},
                                }
                            ],
                        },
                    ],
                    "root_inputs": {"text": "hello list"},
                    "final_output_step": "consume",
                    "metadata": {"target": "skills"},
                }
            },
        )
        self.assertEqual(run_result["status"], "ok")
        workflow_id = run_result["workflow_id"]
        workflow_run_id = run_result["workflow_run_id"]
        list_result = execute_workstation_capability(session, "ws.workflow.list", {"kind": "runs", "limit": 10})
        self.assertEqual(list_result["status"], "ok")
        self.assertEqual(list_result["kind"], "runs")
        self.assertEqual(list_result["workflow_summary_list"]["kind"], "runs")
        self.assertTrue(any(item["workflow_run_id"] == workflow_run_id for item in list_result["items"]))
        get_plan_result = execute_workstation_capability(session, "ws.workflow.get", {"workflow_id": workflow_id})
        self.assertEqual(get_plan_result["status"], "ok")
        self.assertEqual(get_plan_result["kind"], "plan")
        self.assertEqual(get_plan_result["workflow_plan"]["workflow_id"], workflow_id)
        self.assertEqual(get_plan_result["workflow_graph"]["workflow_id"], workflow_id)
        self.assertEqual(get_plan_result["workflow_run_history"]["kind"], "runs")
        self.assertTrue(any(item["workflow_run_id"] == workflow_run_id for item in get_plan_result["workflow_run_history"]["items"]))
        self.assertTrue(any(item["node_id"] == "emit" for item in get_plan_result["workflow_graph"]["nodes"]))
        get_run_result = execute_workstation_capability(session, "ws.workflow.get", {"workflow_run_id": workflow_run_id})
        self.assertEqual(get_run_result["status"], "ok")
        self.assertEqual(get_run_result["kind"], "run")
        self.assertEqual(get_run_result["workflow_run"]["workflow_run_id"], workflow_run_id)
        self.assertEqual(get_run_result["workflow_graph"]["workflow_run_id"], workflow_run_id)
        self.assertEqual(get_run_result["workflow_timeline"]["workflow_run_id"], workflow_run_id)
        self.assertEqual(len(get_run_result["workflow_timeline"]["entries"]), 2)
        self.assertEqual(get_run_result["workflow_timeline"]["entries"][0]["step_id"], "emit")
        self.assertTrue(any(item["is_final_output"] for item in get_run_result["workflow_graph"]["nodes"]))

    def test_operator_list_and_get_surface_dynamic_operator_objects(self) -> None:
        self._persist_python_ability_skill(
            title="Emit Text",
            inputs={"text": "text input"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.operator.list",
                    "ws.operator.get",
                ),
                initial_task="Inspect operator surfaces.",
            )
        )
        list_result = execute_workstation_capability(
            session,
            "ws.operator.list",
            {
                "target": "skills",
                "limit": 50,
            },
        )
        self.assertEqual(list_result["status"], "ok")
        operator_names = {item["operator_name"] for item in list_result["items"]}
        self.assertIn("Emit Text", operator_names)
        self.assertIn("ws.fs.read", operator_names)
        self.assertEqual(list_result["operator_summary_list"]["returned_count"], list_result["returned_count"])
        get_result = execute_workstation_capability(
            session,
            "ws.operator.get",
            {
                "target": "skills",
                "operator_name": "Emit Text",
                "operator_kind": "skill",
            },
        )
        self.assertEqual(get_result["status"], "ok")
        self.assertEqual(get_result["operator"]["operator_name"], "Emit Text")
        self.assertEqual(get_result["operator"]["operator_kind"], "skill")
        self.assertEqual(get_result["operator_detail"]["operator"]["operator_name"], "Emit Text")
        capability_result = execute_workstation_capability(
            session,
            "ws.operator.get",
            {
                "target": "skills",
                "operator_name": "ws.fs.read",
                "operator_kind": "capability",
            },
        )
        self.assertEqual(capability_result["status"], "ok")
        self.assertEqual(capability_result["operator"]["execution_adapter"], "workstation.capability")
        self.assertEqual(capability_result["operator"]["source_kind"], "workstation_capability")
        self.assertEqual(capability_result["operator_detail"]["operator"]["execution_adapter"], "workstation.capability")

    def test_workflow_run_can_rerun_persisted_workflow_by_id(self) -> None:
        self._persist_python_ability_skill(
            title="Emit Text",
            inputs={"text": "text input"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {"boundary_term": "a*", "leaves": [{"region": "a*", "path": "/a/text", "carrier_kind": "value", "data_type": "String", "semantic_label": "text", "value": "text input", "leaf_class": "scalar"}]},
                    "d": {"boundary_term": "d*", "leaves": [{"region": "d*", "path": "/d/text", "carrier_kind": "value", "data_type": "String", "semantic_label": "text", "value": "text output", "leaf_class": "scalar"}]},
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        self._persist_python_ability_skill(
            title="Consume Text",
            inputs={"text": "text input"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {"boundary_term": "a*", "leaves": [{"region": "a*", "path": "/a/text", "carrier_kind": "value", "data_type": "String", "semantic_label": "text", "value": "text input", "leaf_class": "scalar"}]},
                    "d": {"boundary_term": "d*", "leaves": [{"region": "d*", "path": "/d/result", "carrier_kind": "value", "data_type": "String", "semantic_label": "result", "value": "result output", "leaf_class": "scalar"}]},
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"consumed:{payload.get('text', '')}\"}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                    "ws.workflow.list",
                    "ws.workflow.get",
                ),
                initial_task="Rerun persisted workflows by id.",
            )
        )
        first_run = execute_workstation_capability(
            session,
            "ws.workflow.run",
            {
                "workflow_plan": {
                    "workflow_kind": "skill_compose",
                    "steps": [
                        {
                            "step_id": "emit",
                            "operator_kind": "skill",
                            "operator_name": "Emit Text",
                            "bindings": [{"target_region": "a", "target_path": "/a/text", "source_root_name": "text", "source_root_region": "a"}],
                        },
                        {
                            "step_id": "consume",
                            "operator_kind": "skill",
                            "operator_name": "Consume Text",
                            "bindings": [{"target_region": "a", "target_path": "/a/text", "source_step_id": "emit", "source_region": "d", "source_path": "/d/text", "mapper": {"kind": "identity"}}],
                        },
                    ],
                    "root_inputs": {"text": "hello rerun"},
                    "final_output_step": "consume",
                    "metadata": {"target": "skills"},
                }
            },
        )
        self.assertEqual(first_run["status"], "ok")
        rerun = execute_workstation_capability(
            session,
            "ws.workflow.run",
            {"workflow_id": first_run["workflow_id"]},
        )
        self.assertEqual(rerun["status"], "ok")
        self.assertEqual(rerun["capability"], "ws.workflow.run")
        self.assertEqual(rerun["workflow_id"], first_run["workflow_id"])
        self.assertNotEqual(rerun["workflow_run_id"], first_run["workflow_run_id"])
        self.assertEqual(rerun["final_output"], {"result": "consumed:hello rerun"})

    def test_workflow_run_can_mix_capability_and_skill_steps(self) -> None:
        self._persist_python_ability_skill(
            title="Consume Text",
            inputs={"text": "text input"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"consumed:{payload.get('text', '')}\"}",
            ],
        )
        source_path = self.workspace / "src" / "demo.py"
        source_text = source_path.read_text()
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                ),
                initial_task="Run mixed capability and skill workflows.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.workflow.run",
            {
                "workflow_plan": {
                    "workflow_kind": "workflow",
                    "steps": [
                        {
                            "step_id": "read_source",
                            "operator_kind": "capability",
                            "operator_name": "ws.fs.read",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/path",
                                    "source_root_name": "path",
                                    "source_root_region": "a",
                                }
                            ],
                            "metadata": {"target": "main"},
                        },
                        {
                            "step_id": "consume",
                            "operator_kind": "skill",
                            "operator_name": "Consume Text",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/text",
                                    "source_step_id": "read_source",
                                    "source_region": "d",
                                    "source_path": "/d/content",
                                    "mapper": {"kind": "identity"},
                                }
                            ],
                        },
                    ],
                    "root_inputs": {"path": "src/demo.py"},
                    "final_output_step": "consume",
                    "metadata": {"target": "skills"},
                }
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["requested_operator_names"], ["ws.fs.read", "Consume Text"])
        self.assertEqual(result["requested_skill_titles"], ["Consume Text"])
        self.assertEqual(result["steps"][0]["operator_kind"], "capability")
        self.assertEqual(result["steps"][0]["operator_name"], "ws.fs.read")
        self.assertEqual(result["steps"][0]["resolved_target"], "main")
        self.assertEqual(result["steps"][1]["operator_kind"], "skill")
        self.assertEqual(result["final_output"], {"result": f"consumed:{source_text}"})

    def test_workflow_run_ignores_skill_invoke_step_delegation_as_nested_host_right(self) -> None:
        """
        High Level Purpose:
            In circumstances like Blend workflow execution of workstation skill operators, helps with verifying that the outer `ws.skill.invoke` capability requirement is not forwarded as nested host delegation.

        Reference to Theory:
            Verifies the workstation / Blend boundary keeps operator selection rights separate from delegated host effects inside the nested skill runtime.

        Example Input Output:
            Input: `test_workflow_run_ignores_skill_invoke_step_delegation_as_nested_host_right()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Nested Greeting Ability",
            inputs={"payload": "stdin payload or JSON input"},
            outputs={"greeting": "greeting text"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/payload",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "payload",
                                "value": "stdin payload or JSON input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/greeting",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "greeting",
                                "value": "greeting text",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'greeting': f\"hello:{payload.get('payload', '')}\"}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                ),
                initial_task="Run one workstation skill through a workflow step.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.workflow.run",
            {
                "workflow_plan": {
                    "workflow_kind": "workflow",
                    "steps": [
                        {
                            "step_id": "greet",
                            "operator_kind": "skill",
                            "operator_name": "Nested Greeting Ability",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/payload",
                                    "source_root_name": "payload",
                                    "source_root_region": "a",
                                }
                            ],
                            "requested_delegation": [
                                {
                                    "capability": "ws.skill.invoke",
                                    "target": "Nested Greeting Ability",
                                }
                            ],
                        }
                    ],
                    "root_inputs": {"payload": "hello"},
                    "final_output_step": "greet",
                    "metadata": {"target": "skills"},
                }
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["requested_skill_titles"], ["Nested Greeting Ability"])
        self.assertEqual(result["requested_delegation"], [])
        self.assertEqual(result["unsupported_delegation"], [])
        self.assertEqual(result["steps"][0]["status"], "ok")
        self.assertEqual(result["final_output"], {"greeting": "hello:hello"})

    def test_skill_compose_returns_approval_required_when_one_step_needs_write_delegation(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation multi-step plans over write-capable skills, helps with verifying that a composition halts with one bounded approval request instead of silently falling back or executing without the needed grant.

        Reference to Theory:
            Verifies the workstation composition surface reuses the same permission boundary as ordinary skill invocation.

        Example Input Output:
            Input: `test_skill_compose_returns_approval_required_when_one_step_needs_write_delegation()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Compose imported Python file skills.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        result = execute_workstation_capability(
            session,
            "ws.skill.compose",
            {
                "steps": [
                    {
                        "step_id": "write",
                        "skill_title": "Python Commands 03 — Write Text File",
                        "bindings": [
                            {
                                "target_region": "a",
                                "target_path": "/a/mount",
                                "source_root_name": "mount",
                                "source_root_region": "a",
                            },
                            {
                                "target_region": "a",
                                "target_path": "/a/relative_path",
                                "source_root_name": "relative_path",
                                "source_root_region": "a",
                            },
                            {
                                "target_region": "a",
                                "target_path": "/a/text",
                                "source_root_name": "text",
                                "source_root_region": "a",
                            },
                        ],
                    }
                ],
                "root_inputs": {
                    "mount": "main",
                    "relative_path": "exports/composed.txt",
                    "text": "hello from composition",
                },
            },
        )
        self.assertEqual(result["status"], "approval_required")
        self.assertEqual(result["capability"], "ws.skill.compose")
        self.assertEqual(result["blocked_step_id"], "write")
        self.assertEqual(result["blocked_skill_title"], "Python Commands 03 — Write Text File")
        self.assertEqual(
            result["missing_delegation"],
            [
                {
                    "capability": "ws.fs.write",
                    "target": "main",
                    "rationale": "Need to expose the requested workstation mount to the invoked skill.",
                }
            ],
        )

    def test_partial_prompt_payload_derivation_keeps_write_destination_without_text(self) -> None:
        """
        High Level Purpose:
            In circumstances like automatic workstation composition planning, helps with verifying that prompt-local destination fields can be recovered even when the full required payload still needs one mapped input from a prior skill.

        Reference to Theory:
            Verifies the planner can separate root-bound inputs from skill-to-skill leaf bindings instead of forcing every step to be directly invokable from the raw prompt.

        Example Input Output:
            Input: `test_partial_prompt_payload_derivation_keeps_write_destination_without_text()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = derive_workstation_partial_invocation_payload_from_prompt(
            inputs={
                "mount": "required input value",
                "relative_path": "required input value",
                "text": "required input value",
            },
            prompt="Read the text file `src/demo.py` from mount `main` and write it to mount `skill_tmp` at `demo.copy`.",
            skill_title="Python Commands 03 — Write Text File",
        )
        self.assertEqual(
            payload,
            {
                "mount": "skill_tmp",
                "relative_path": "demo.copy",
            },
        )

    def test_preferred_workstation_skill_composition_plan_builds_read_to_write_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like pre-LLM workstation composition planning, helps with verifying that an ordinary read-then-write prompt compiles into one first-class workflow run over imported trial skills.

        Reference to Theory:
            Verifies the first workstation-facing automatic composition planner builds leaf bindings from the canonical ledgers instead of relying on prompt-only chaining.

        Example Input Output:
            Input: `test_preferred_workstation_skill_composition_plan_builds_read_to_write_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                ),
                initial_task="Compose imported Python file skills automatically.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        plan = preferred_workstation_skill_composition_plan(
            session=session,
            prompt="Read the text file `src/demo.py` from mount `main` and write it to mount `skill_tmp` at `demo.copy`.",
        )
        self.assertIsNotNone(plan)
        self.assertEqual(
            plan["steps"][0]["skill_title"],
            "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
        )
        self.assertEqual(
            plan["steps"][1]["skill_title"],
            "Python Commands 03 — Write Text File / Python Commands 03 Write Text File",
        )
        self.assertEqual(
            plan["root_inputs"],
            {
                "step_1_mount": "main",
                "step_1_relative_path": "src/demo.py",
                "step_2_mount": "skill_tmp",
                "step_2_relative_path": "demo.copy",
            },
        )
        self.assertIn(
            {
                "target_region": "a",
                "target_path": "/a/text",
                "source_step_id": "step_1",
                "source_region": "d",
                "source_path": "/d/result",
                "mapper": {"kind": "project_field", "field": "text"},
            },
            plan["steps"][1]["bindings"],
        )

    def test_prompt_workstation_session_auto_composes_read_then_write_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like one ordinary workstation prompt that clearly implies a two-step pipeline, helps with verifying that the shell can auto-compose imported skills before the LLM loop and execute them end to end.

        Reference to Theory:
            Verifies the first automatic workstation composition cut is executable, governed, and additive to the existing skill-first shell behavior.

        Example Input Output:
            Input: `test_prompt_workstation_session_auto_composes_read_then_write_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                ),
                initial_task="Compose imported Python file skills automatically.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Read the text file `src/demo.py` from mount `main` and write it to mount `skill_tmp` at `demo.copy`.",
            delegation_approval_callback=lambda _request: True,
        )
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.workflow.run")
        self.assertEqual(report["tool_receipts"][0]["result"]["status"], "ok")
        self.assertEqual(
            report["tool_receipts"][0]["result"]["requested_skill_titles"],
            [
                "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
                "Python Commands 03 — Write Text File / Python Commands 03 Write Text File",
            ],
        )
        self.assertEqual(
            (self.root / "scratch" / "demo.copy").read_text(),
            (self.workspace / "src" / "demo.py").read_text(),
        )

    def test_preferred_workstation_skill_composition_plan_builds_three_step_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like widening workstation composition planning, helps with verifying that one ordinary prompt can compile into a bounded three-step linear skill pipeline instead of stopping at two-step composition only.

        Reference to Theory:
            Verifies richer multi-step planning still stays on the explicit leaf/mapping substrate instead of falling back to opaque chaining.

        Example Input Output:
            Input: `test_preferred_workstation_skill_composition_plan_builds_three_step_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                ),
                initial_task="Compose imported Python file skills automatically.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        plan = preferred_workstation_skill_composition_plan(
            session=session,
            prompt=(
                "Read the text file `src/demo.py` from mount `main`, "
                "then write it to mount `skill_tmp` at `demo.copy`, "
                "then read the text file `demo.copy` from mount `skill_tmp`."
            ),
        )
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan["steps"]), 3)
        self.assertEqual(
            [step["skill_title"] for step in plan["steps"]],
            [
                "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
                "Python Commands 03 — Write Text File / Python Commands 03 Write Text File",
                "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
            ],
        )
        self.assertEqual(
            plan["root_inputs"],
            {
                "step_1_mount": "main",
                "step_1_relative_path": "src/demo.py",
                "step_2_mount": "skill_tmp",
                "step_2_relative_path": "demo.copy",
                "step_3_mount": "skill_tmp",
                "step_3_relative_path": "demo.copy",
            },
        )
        self.assertEqual(plan["final_output_step"], "step_3")
        self.assertIn(
            {
                "target_region": "a",
                "target_path": "/a/text",
                "source_step_id": "step_1",
                "source_region": "d",
                "source_path": "/d/result",
                "mapper": {"kind": "project_field", "field": "text"},
            },
            plan["steps"][1]["bindings"],
        )

    def test_preferred_workstation_skill_composition_plan_builds_conditional_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like widening workstation composition planning, helps with verifying that a later step can be guarded by one explicit condition over an earlier step's output leaf.

        Reference to Theory:
            Verifies bounded conditional planning stays on the existing compose schema by emitting `run_if` over explicit source leaves instead of inventing a second execution model.

        Example Input Output:
            Input: `test_preferred_workstation_skill_composition_plan_builds_conditional_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Read Prepared Text",
            inputs={"text": "required input value"},
            outputs={"text": "text output", "status": "status output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            },
                            {
                                "region": "d*",
                                "path": "/d/status",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "status",
                                "value": "status output",
                                "leaf_class": "scalar",
                            },
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', ''), 'status': 'ok'}",
            ],
        )
        self._persist_python_ability_skill(
            title="Write Captured Text",
            inputs={"text": "required input value"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"written:{payload.get('text', '')}\"}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Compose conditional skills automatically.",
            )
        )
        plan = preferred_workstation_skill_composition_plan(
            session=session,
            prompt="Read the text `hello`, then if status is `ok`, write the text.",
        )
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan["steps"]), 2)
        self.assertEqual(
            [step["skill_title"] for step in plan["steps"]],
            ["Read Prepared Text", "Write Captured Text"],
        )
        self.assertEqual(plan["root_inputs"], {"step_1_text": "hello"})
        self.assertEqual(
            plan["steps"][1]["run_if"],
            [
                {
                    "source_step_id": "step_1",
                    "source_region": "d",
                    "source_path": "/d/status",
                    "operator": "equals",
                    "expected_value": "ok",
                }
            ],
        )
        self.assertIn(
            {
                "target_region": "a",
                "target_path": "/a/text",
                "source_step_id": "step_1",
                "source_region": "d",
                "source_path": "/d/text",
                "mapper": {"kind": "identity"},
            },
            plan["steps"][1]["bindings"],
        )

    def test_prompt_workstation_session_auto_composes_three_step_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like one ordinary workstation prompt that implies more than two steps, helps with verifying that the shell can auto-compose and execute a bounded three-step pipeline before the generic LLM loop.

        Reference to Theory:
            Verifies planner widening remains executable and governed while staying on the explicit workflow-run path.

        Example Input Output:
            Input: `test_prompt_workstation_session_auto_composes_three_step_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                allowed_capabilities=(
                    *DEFAULT_WORKSTATION_CAPABILITIES,
                    "ws.workflow.run",
                ),
                initial_task="Compose imported Python file skills automatically.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        report = prompt_workstation_session(
            root_path=self.root,
            prompt=(
                "Read the text file `src/demo.py` from mount `main`, "
                "then write it to mount `skill_tmp` at `demo.copy`, "
                "then read the text file `demo.copy` from mount `skill_tmp`."
            ),
            delegation_approval_callback=lambda _request: True,
        )
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.workflow.run")
        result = report["tool_receipts"][0]["result"]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["requested_skill_titles"],
            [
                "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
                "Python Commands 03 — Write Text File / Python Commands 03 Write Text File",
                "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
            ],
        )
        self.assertEqual(result["final_output_step"], "step_3")
        self.assertEqual(
            result["final_output"]["text"],
            (self.workspace / "src" / "demo.py").read_text(),
        )
        self.assertEqual(
            (self.root / "scratch" / "demo.copy").read_text(),
            (self.workspace / "src" / "demo.py").read_text(),
        )

    def test_prompt_workstation_session_auto_composes_conditional_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like conditional multi-step workstation planning, helps with verifying that an ordinary prompt can emit one explicit workflow run with `run_if` and execute it end to end.

        Reference to Theory:
            Verifies bounded conditional planning remains an additive extension of the existing compose path instead of inventing a separate control-flow runtime.

        Example Input Output:
            Input: `test_prompt_workstation_session_auto_composes_conditional_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Read Prepared Text",
            inputs={"text": "required input value"},
            outputs={"text": "text output", "status": "status output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            },
                            {
                                "region": "d*",
                                "path": "/d/status",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "status",
                                "value": "status output",
                                "leaf_class": "scalar",
                            },
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', ''), 'status': 'ok'}",
            ],
        )
        self._persist_python_ability_skill(
            title="Write Captured Text",
            inputs={"text": "required input value"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"written:{payload.get('text', '')}\"}",
            ],
        )
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            allowed_capabilities=(
                *DEFAULT_WORKSTATION_CAPABILITIES,
                "ws.workflow.run",
            ),
            initial_task="Compose conditional skills automatically.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Read the text `hello`, then if status is `ok`, write the text.",
            delegation_approval_callback=lambda _request: True,
        )
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.workflow.run")
        result = report["tool_receipts"][0]["result"]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["requested_skill_titles"],
            ["Read Prepared Text", "Write Captured Text"],
        )
        self.assertEqual(result["final_output"], {"result": "written:hello"})
        self.assertEqual(
            result["steps"][1]["condition_receipts"],
            [
                {
                    "kind": "run_if",
                    "source_step_id": "step_1",
                    "source_region": "d",
                    "source_path": "/d/status",
                    "operator": "equals",
                    "expected_value": "ok",
                    "actual_value": "ok",
                    "matched": True,
                }
            ],
        )

    def test_preferred_workstation_skill_composition_plan_builds_branching_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like bounded branching planner widening, helps with verifying that one conditional clause with an `otherwise` branch expands into two explicit compose steps over inverse `run_if` conditions.

        Reference to Theory:
            Verifies branching remains encoded as explicit guarded steps on the existing compose substrate instead of inventing a second branch-only runtime representation.

        Example Input Output:
            Input: `test_preferred_workstation_skill_composition_plan_builds_branching_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Read Prepared Text",
            inputs={"text": "required input value"},
            outputs={"text": "text output", "status": "status output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            },
                            {
                                "region": "d*",
                                "path": "/d/status",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "status",
                                "value": "status output",
                                "leaf_class": "scalar",
                            },
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', ''), 'status': 'ok'}",
            ],
        )
        self._persist_python_ability_skill(
            title="Write Captured Text",
            inputs={"text": "required input value"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"written:{payload.get('text', '')}\"}",
            ],
        )
        self._persist_python_ability_skill(
            title="Append Captured Text",
            inputs={"text": "required input value"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"appended:{payload.get('text', '')}\"}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Compose branching skills automatically.",
            )
        )
        plan = preferred_workstation_skill_composition_plan(
            session=session,
            prompt="Read the text `hello`, then if status is `ok`, write the text, otherwise append the text.",
        )
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan["steps"]), 3)
        self.assertEqual(
            [step["skill_title"] for step in plan["steps"]],
            ["Read Prepared Text", "Write Captured Text", "Append Captured Text"],
        )
        self.assertEqual(plan["root_inputs"], {"step_1_text": "hello"})
        self.assertEqual(plan["steps"][1]["branch_label"], "if")
        self.assertEqual(plan["steps"][2]["branch_label"], "else")
        self.assertEqual(
            plan["steps"][1]["run_if"],
            [
                {
                    "source_step_id": "step_1",
                    "source_region": "d",
                    "source_path": "/d/status",
                    "operator": "equals",
                    "expected_value": "ok",
                }
            ],
        )
        self.assertEqual(
            plan["steps"][2]["run_if"],
            [
                {
                    "source_step_id": "step_1",
                    "source_region": "d",
                    "source_path": "/d/status",
                    "operator": "not_equals",
                    "expected_value": "ok",
                }
            ],
        )
        self.assertIn(
            {
                "target_region": "a",
                "target_path": "/a/text",
                "source_step_id": "step_1",
                "source_region": "d",
                "source_path": "/d/text",
                "mapper": {"kind": "identity"},
            },
            plan["steps"][2]["bindings"],
        )

    def test_prompt_workstation_session_auto_composes_branching_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like bounded branching compose planning, helps with verifying that an ordinary prompt emits one workflow run and still returns the executed branch output when the alternate final branch is skipped.

        Reference to Theory:
            Verifies branching stays on explicit guarded compose steps and that the workstation reports the last executed branch output instead of losing the answer when a later branch is skipped.

        Example Input Output:
            Input: `test_prompt_workstation_session_auto_composes_branching_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Read Prepared Text",
            inputs={"text": "required input value"},
            outputs={"text": "text output", "status": "status output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            },
                            {
                                "region": "d*",
                                "path": "/d/status",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "status",
                                "value": "status output",
                                "leaf_class": "scalar",
                            },
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', ''), 'status': 'ok'}",
            ],
        )
        self._persist_python_ability_skill(
            title="Write Captured Text",
            inputs={"text": "required input value"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"written:{payload.get('text', '')}\"}",
            ],
        )
        self._persist_python_ability_skill(
            title="Append Captured Text",
            inputs={"text": "required input value"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"appended:{payload.get('text', '')}\"}",
            ],
        )
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            allowed_capabilities=(
                *DEFAULT_WORKSTATION_CAPABILITIES,
                "ws.workflow.run",
            ),
            initial_task="Compose branching skills automatically.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Read the text `hello`, then if status is `ok`, write the text, otherwise append the text.",
            delegation_approval_callback=lambda _request: True,
        )
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.workflow.run")
        result = report["tool_receipts"][0]["result"]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["requested_skill_titles"],
            ["Read Prepared Text", "Write Captured Text", "Append Captured Text"],
        )
        self.assertEqual(result["final_output_step"], "step_2")
        self.assertEqual(result["final_output"], {"result": "written:hello"})
        self.assertEqual(result["steps"][1]["branch_label"], "if")
        self.assertEqual(result["steps"][2]["status"], "skipped")
        self.assertEqual(result["steps"][2]["branch_label"], "else")
        self.assertEqual(
            result["steps"][2]["condition_receipts"],
            [
                {
                    "kind": "run_if",
                    "source_step_id": "step_1",
                    "source_region": "d",
                    "source_path": "/d/status",
                    "operator": "not_equals",
                    "expected_value": "ok",
                    "actual_value": "ok",
                    "matched": False,
                }
            ],
        )

    def test_preferred_workstation_skill_composition_plan_builds_iterative_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like widening workstation composition planning, helps with verifying that a later step can be marked iterative through one explicit `iterate_until` condition on its own output leaf.

        Reference to Theory:
            Verifies bounded iterative planning stays on the existing compose schema instead of inventing a second loop representation.

        Example Input Output:
            Input: `test_preferred_workstation_skill_composition_plan_builds_iterative_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Read Prepared Text",
            inputs={"text": "required input value"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        self._persist_python_ability_skill(
            title="Poll Status",
            inputs={},
            outputs={"has_more": "has more output"},
            normalization={
                "regions": {
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/has_more",
                                "carrier_kind": "value",
                                "data_type": "Boolean",
                                "semantic_label": "has_more",
                                "value": True,
                                "leaf_class": "scalar",
                            }
                        ],
                    }
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    return {'has_more': False}",
            ],
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Compose iterative skills automatically.",
            )
        )
        plan = preferred_workstation_skill_composition_plan(
            session=session,
            prompt="Read the text `hello`, then repeat poll status until has_more is `false`.",
        )
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan["steps"]), 2)
        self.assertEqual(
            [step["skill_title"] for step in plan["steps"]],
            ["Read Prepared Text", "Poll Status"],
        )
        self.assertEqual(plan["root_inputs"], {"step_1_text": "hello"})
        self.assertEqual(
            plan["steps"][1]["iterate_until"],
            [
                {
                    "source_step_id": "step_2",
                    "source_region": "d",
                    "source_path": "/d/has_more",
                    "operator": "equals",
                    "expected_value": False,
                }
            ],
        )

    def test_prompt_workstation_session_auto_composes_iterative_pipeline(self) -> None:
        """
        High Level Purpose:
            In circumstances like iterative workstation planning, helps with verifying that an ordinary prompt can emit one explicit workflow run with `iterate_until` and execute it to completion.

        Reference to Theory:
            Verifies iterative planning remains an additive extension of the compose path over explicit step-local output conditions.

        Example Input Output:
            Input: `test_prompt_workstation_session_auto_composes_iterative_pipeline()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        counter_path = self.root / "poll_counter.txt"
        self._persist_python_ability_skill(
            title="Read Prepared Text",
            inputs={"text": "required input value"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        self._persist_python_ability_skill(
            title="Poll Status",
            inputs={},
            outputs={"has_more": "has more output"},
            normalization={
                "regions": {
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/has_more",
                                "carrier_kind": "value",
                                "data_type": "Boolean",
                                "semantic_label": "has_more",
                                "value": True,
                                "leaf_class": "scalar",
                            }
                        ],
                    }
                }
            },
            python_lines=[
                f"from pathlib import Path",
                f"COUNTER_PATH = Path({str(counter_path)!r})",
                "def main(payload: dict | None = None) -> dict:",
                "    count = 0",
                "    if COUNTER_PATH.exists():",
                "        count = int(COUNTER_PATH.read_text().strip() or '0')",
                "    count += 1",
                "    COUNTER_PATH.write_text(str(count))",
                "    return {'has_more': count < 3}",
            ],
        )
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            allowed_capabilities=(
                *DEFAULT_WORKSTATION_CAPABILITIES,
                "ws.workflow.run",
            ),
            initial_task="Compose iterative skills automatically.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Read the text `hello`, then repeat poll status until has_more is `false`.",
            delegation_approval_callback=lambda _request: True,
        )
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.workflow.run")
        result = report["tool_receipts"][0]["result"]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["requested_skill_titles"],
            ["Read Prepared Text", "Poll Status"],
        )
        self.assertEqual(result["final_output"], {"has_more": False})
        poll_steps = [item for item in result["steps"] if item["step_id"] == "step_2"]
        self.assertEqual(len(poll_steps), 3)
        self.assertEqual(counter_path.read_text().strip(), "3")

    def test_prompt_workstation_session_can_use_skill_compose(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation LLM planning over explicit multi-step skill plans, helps with verifying that the host-owned prompt loop can emit the `ws.skill.compose` schema and execute it through the normal tool path.

        Reference to Theory:
            Verifies the workstation planner/runtime can express composition as one first-class capability instead of only chaining single-skill tool calls implicitly.

        Example Input Output:
            Input: `test_prompt_workstation_session_can_use_skill_compose()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._persist_python_ability_skill(
            title="Emit Text",
            inputs={"text": "text input"},
            outputs={"text": "text output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'text': payload.get('text', '')}",
            ],
        )
        self._persist_python_ability_skill(
            title="Consume Text",
            inputs={"text": "text input"},
            outputs={"result": "result output"},
            normalization={
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/text",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "text",
                                "value": "text input",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/result",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "result",
                                "value": "result output",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                }
            },
            python_lines=[
                "def main(payload: dict | None = None) -> dict:",
                "    payload = payload or {}",
                "    return {'result': f\"consumed:{payload.get('text', '')}\"}",
            ],
        )
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Use explicit skill compositions when appropriate.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Compose two installed skills to carry hello world through an explicit pipeline.",
            client=_FakeSkillComposeClient(),
        )
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.compose")
        self.assertEqual(report["tool_receipts"][0]["result"]["status"], "ok")
        self.assertIn("Composed the skills successfully.", report["assistant_text"])

    def test_skill_invoke_applies_delegated_mounts_to_builtin_repo_search_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation-to-skill delegation testing, helps with verifying that delegated workstation read rights become invocation-scoped governed mounts inside the nested skill runtime.

        Reference to Theory:
            Verifies the workstation shell / pluggable-worker split by proving the shell can attenuate attachment rights into a nested worker instead of falling back to ambient host access.

        Example Input Output:
            Input: `test_skill_invoke_applies_delegated_mounts_to_builtin_repo_search_skill()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Search the repository through a skill.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Workstation Repo Search",
                "invocation_payload": {
                    "mount": "main",
                    "pattern": "def main",
                    "max_matches": 10,
                },
                "requested_delegation": [
                    {
                        "capability": "ws.fs.read",
                        "target": "main",
                        "rationale": "Need to inspect repository files.",
                    }
                ],
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["skill_source"]["source_kind"], "builtin_workstation")
        self.assertEqual(result["delegated_virtual_mounts"]["main"]["root"], str(self.workspace.resolve()))
        self.assertIn("Found 1 matches", result["answer"])
        nested_effect_kinds = [
            str(item.get("request", {}).get("effect_kind", "") or item.get("effect_kind", ""))
            for item in result["nested_effect_traces"]
        ]
        self.assertIn("fs.find_mount", nested_effect_kinds)
        self.assertIn("fs.read_mount", nested_effect_kinds)

    def test_skill_invoke_applies_delegated_mounts_to_builtin_repo_tree_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation-to-skill delegation testing, helps with verifying that delegated workstation read rights become invocation-scoped governed mounts inside the builtin repo-tree worker runtime.

        Reference to Theory:
            Verifies the workstation shell / pluggable-worker split by proving repository tree inspection can move onto a worker instead of a direct shell capability.

        Example Input Output:
            Input: `test_skill_invoke_applies_delegated_mounts_to_builtin_repo_tree_skill()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        (self.workspace / "src").mkdir(parents=True, exist_ok=True)
        (self.workspace / "src" / "demo.py").write_text("print('ok')\n")
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Inspect the repository tree through a skill.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Workstation Repo Tree",
                "invocation_payload": {
                    "mount": "main",
                    "relative_path": "src",
                    "max_depth": 2,
                    "max_entries": 10,
                },
                "requested_delegation": [
                    {
                        "capability": "ws.fs.read",
                        "target": "main",
                        "rationale": "Need to inspect repository directories.",
                    }
                ],
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["skill_source"]["source_kind"], "builtin_workstation")
        self.assertEqual(result["delegated_virtual_mounts"]["main"]["root"], str(self.workspace.resolve()))
        self.assertIn("demo.py", "\n".join(result["result"].get("tree", [])))
        nested_effect_kinds = [
            str(item.get("request", {}).get("effect_kind", "") or item.get("effect_kind", ""))
            for item in result["nested_effect_traces"]
        ]
        self.assertIn("fs.list_mount", nested_effect_kinds)

    def test_repo_tree_normalizes_trial_mount_path_target(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation use against the trial corpus, helps with verifying that one repo-tree call can recover the attachment and subpath when the model supplies a full trial-style mount path as the target.

        Reference to Theory:
            Verifies the workstation shell can interpret trial-style attachment spelling without special-casing the imported worker bundles themselves.

        Example Input Output:
            Input: `test_repo_tree_normalizes_trial_mount_path_target()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        (trials_dir / "example.txt").write_text("demo\n")
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
                initial_task="Inspect the trial mount.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.repo.tree",
            {"target": "/workstation/mounts/skill_input/trials"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "skill_input")
        self.assertEqual(result["path"], "trials")
        self.assertIn("example.txt", result["tree"])

    def test_repo_tree_normalizes_absolute_workspace_path_argument(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation prompting, helps with verifying that a repo-tree call can collapse one absolute host path back into an attachment-relative path instead of treating it as an escape.

        Reference to Theory:
            Verifies the workstation shell keeps capability execution attachment-bounded even when the model echoes a full host path under the already-selected workspace attachment.

        Example Input Output:
            Input: `test_repo_tree_normalizes_absolute_workspace_path_argument()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        (trials_dir / "example.txt").write_text("demo\n")
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
                initial_task="Inspect the trial mount by absolute path.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.repo.tree",
            {
                "target": "main",
                "path": str(self.workspace.resolve()),
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["target"], "main")
        self.assertEqual(result["path"], "")
        self.assertIn("trials/", result["tree"])

    def test_skill_invoke_normalizes_trial_alias_mount_and_delegation_targets(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation-to-skill invocation against trial-authored workers, helps with verifying that full mount-path spellings are normalized to attachment aliases before delegation and nested-skill execution.

        Reference to Theory:
            Verifies the workstation shell can mediate imported trial workers without rewriting their mount vocabulary.

        Example Input Output:
            Input: `test_skill_invoke_normalizes_trial_alias_mount_and_delegation_targets()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        (trials_dir / "readme.txt").write_text("def main\n")
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Invoke the repo search skill through trial aliases.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Workstation Repo Search",
                "invocation_payload": {
                    "mount": "/workstation/mounts/skill_input",
                    "pattern": "def main",
                    "relative_path": "trials",
                },
                "requested_delegation": [
                    {
                        "capability": "ws.fs.read",
                        "target": "/workstation/mounts/skill_input",
                        "rationale": "Need to inspect the input mount.",
                    }
                ],
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["granted_delegation"][0]["target"], "skill_input")
        self.assertEqual(result["delegated_virtual_mounts"]["skill_input"]["root"], str(self.workspace.resolve()))

    def test_skill_invoke_derives_repo_search_payload_and_delegation_when_omitted(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation model behavior, helps with verifying that builtin repo-search invocation can derive a bounded payload and read delegation from the semantic unit when the model omits explicit skill arguments.

        Reference to Theory:
            Verifies the workstation shell can refine a natural-language request into explicit worker inputs and delegated rights instead of failing on omitted structured fields.

        Example Input Output:
            Input: `test_skill_invoke_derives_repo_search_payload_and_delegation_when_omitted()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Search the repository through a skill.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Workstation Repo Search",
                "semantic_unit": "Find where main is implemented in this workspace.",
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["granted_delegation"][0]["capability"], "ws.fs.read")
        self.assertEqual(result["granted_delegation"][0]["target"], "main")
        self.assertEqual(result["delegated_virtual_mounts"]["main"]["root"], str(self.workspace.resolve()))
        self.assertIn("Found 1 matches", result["answer"])

    def test_skill_invoke_repo_search_ignores_trailing_output_instruction_in_pattern_derivation(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation prompting, helps with verifying that repo-search payload derivation strips trailing output-format instructions instead of treating them as part of the search pattern.

        Reference to Theory:
            Verifies the workstation shell derives worker inputs from the semantic unit while keeping the search intent separate from the answer-format request.

        Example Input Output:
            Input: `test_skill_invoke_repo_search_ignores_trailing_output_instruction_in_pattern_derivation()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Search the repository through a skill.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Workstation Repo Search",
                "semantic_unit": "Search for def main and return only the first matching path.",
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("Found 1 matches", result["answer"])

    def test_skill_invoke_executes_builtin_wasm_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation-to-Wasmtime integration testing, helps with verifying that the workstation can invoke one builtin Wasm-backed skill through the normal skill path.

        Reference to Theory:
            Verifies that Wasmtime is one worker runtime under the workstation shell rather than the workstation shell itself.

        Example Input Output:
            Input: `test_skill_invoke_executes_builtin_wasm_skill()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use the builtin Wasm worker.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {"skill_title": "Workstation Greeting From Wasm"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn(result["skill_source"]["source_kind"], {"builtin_workstation", "attached_skill_store"})
        self.assertEqual(result["executor_framework"], "wasm_wasi")
        self.assertEqual(result["answer"], "hello from workstation wasm")
        nested_effect_kinds = [item["request"]["effect_kind"] for item in result["nested_effect_traces"]]
        self.assertIn("execute.wasm_wasi", nested_effect_kinds)

    def test_skill_invoke_requests_outside_session_grant_require_approval(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation delegated-rights planning, helps with verifying that a skill invocation asking for workstation rights outside the current session grant produces an escalation-needed result.

        Reference to Theory:
            Verifies the workstation governance model by distinguishing ordinary invocation from new authority acquisition.

        Example Input Output:
            Input: `test_skill_invoke_requests_outside_session_grant_require_approval()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                skills_sqlite_path=self.skills_sqlite,
                initial_task="Use the installed skills.",
            )
        )
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Workstation Greeting",
                "requested_delegation": [
                    {
                        "capability": "ws.fs.write",
                        "target": "main",
                        "rationale": "Need to modify repository files.",
                    }
                ],
            },
        )
        self.assertEqual(result["status"], "approval_required")
        self.assertEqual(result["missing_delegation"][0]["capability"], "ws.fs.write")

    def test_host_interaction_capability_call_receipt_projects_delegation_fields(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared workstation receipt projection, helps with verifying that capability-call receipts expose delegated-rights information in one stable top-level field instead of forcing downstream consumers to inspect capability-specific result blobs.

        Reference to Theory:
            Verifies the workstation receipt model by making requested, approved, escalated, granted, and missing rights explicit at the receipt boundary.

        Example Input Output:
            Input: `test_host_interaction_capability_call_receipt_projects_delegation_fields()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        receipt = host_interaction_capability_call_receipt(
            capability="ws.skill.invoke",
            arguments={
                "skill_title": "Workstation Greeting",
                "requested_delegation": [
                    {
                        "capability": "ws.fs.read",
                        "target": "main",
                        "rationale": "Need repository access.",
                    }
                ],
                "approved_delegation": [
                    {
                        "capability": "ws.fs.write",
                        "target": "scratch",
                        "rationale": "Approved scratch write.",
                    }
                ],
                "approved_delegation_scope": "one_invocation",
            },
            result={
                "status": "ok",
                "target": "skills",
                "requested_delegation": [
                    {
                        "capability": "ws.fs.read",
                        "target": "main",
                        "rationale": "Need repository access.",
                    }
                ],
                "approved_delegation": [
                    {
                        "capability": "ws.fs.write",
                        "target": "scratch",
                        "rationale": "Approved scratch write.",
                    }
                ],
                "escalated_delegation": [
                    {
                        "capability": "ws.fs.write",
                        "target": "scratch",
                        "rationale": "Approved scratch write.",
                    }
                ],
                "granted_delegation": [
                    {
                        "capability": "ws.fs.read",
                        "target": "main",
                        "rationale": "Need repository access.",
                    },
                    {
                        "capability": "ws.fs.write",
                        "target": "scratch",
                        "rationale": "Approved scratch write.",
                    },
                ],
                "missing_delegation": [],
            },
            phase="completed",
        )
        self.assertEqual(receipt["target"], "skills")
        self.assertEqual(receipt["delegation"]["status"], "ok")
        self.assertEqual(receipt["delegation"]["scope"], "one_invocation")
        self.assertEqual(receipt["delegation"]["requested"][0]["target"], "main")
        self.assertEqual(receipt["delegation"]["approved"][0]["target"], "scratch")
        self.assertEqual(receipt["delegation"]["escalated"][0]["target"], "scratch")
        self.assertEqual(len(receipt["delegation"]["granted"]), 2)
        self.assertEqual(receipt["delegation"]["missing"], [])

    def test_host_interaction_capability_call_receipt_projects_invocation_contract(self) -> None:
        receipt = host_interaction_capability_call_receipt(
            capability="ws.skill.invoke",
            arguments={"skill_title": "Emit Text"},
            result={
                "status": "ok",
                "target": "skills",
                "invocation_request": {
                    "skill_title": "Emit Text",
                    "invocation_mode": "direct_named",
                    "bindings": [
                        {
                            "target_region": "a",
                            "target_path": "/a/text",
                            "source_root_name": "text",
                            "status": "provided",
                        }
                    ],
                },
                "invocation_result": {
                    "status": "ok",
                    "output_payload": {"text": "hello world"},
                },
            },
            phase="completed",
        )

        self.assertEqual(receipt["invocation"]["request"]["skill_title"], "Emit Text")
        self.assertEqual(receipt["invocation"]["request"]["bindings"][0]["target_path"], "/a/text")
        self.assertEqual(receipt["invocation"]["result"]["status"], "ok")
        self.assertEqual(receipt["invocation"]["result"]["output_payload"], {"text": "hello world"})

    def test_host_interaction_capability_call_receipt_projects_composition_lineage(self) -> None:
        receipt = host_interaction_capability_call_receipt(
            capability="ws.skill.compose",
            arguments={"workflow_id": "emit-consume"},
            result={
                "status": "ok",
                "requested_skill_titles": ["Emit Text", "Consume Text"],
                "final_output_step": "consume",
                "plan_authorities": ["direct_user_invocation"],
                "steps": [
                    {
                        "step_id": "emit",
                        "title": "Emit Text",
                        "status": "ok",
                        "iteration": 1,
                        "binding_receipts": [
                            {
                                "target_region": "a",
                                "target_path": "/a/text",
                                "source_kind": "root_input",
                                "source_root_name": "text",
                            }
                        ],
                        "condition_receipts": [],
                    },
                    {
                        "step_id": "consume",
                        "title": "Consume Text",
                        "status": "ok",
                        "iteration": 1,
                        "binding_receipts": [
                            {
                                "target_region": "a",
                                "target_path": "/a/text",
                                "source_kind": "step_output",
                                "source_step_id": "emit",
                                "source_path": "/d/text",
                            }
                        ],
                        "condition_receipts": [
                            {
                                "kind": "run_if",
                                "source_step_id": "emit",
                                "matched": True,
                            }
                        ],
                    },
                ],
            },
            phase="completed",
        )

        self.assertEqual(receipt["composition"]["workflow_id"], "emit-consume")
        self.assertEqual(receipt["composition"]["requested_skill_titles"], ["Emit Text", "Consume Text"])
        self.assertEqual(receipt["composition"]["final_output_step"], "consume")
        self.assertEqual(receipt["composition"]["plan_authorities"], ["direct_user_invocation"])
        self.assertEqual(receipt["composition"]["steps"][1]["binding_receipts"][0]["source_step_id"], "emit")
        self.assertTrue(receipt["composition"]["steps"][1]["condition_receipts"][0]["matched"])

    def test_prompt_workstation_session_runs_end_to_end_with_fake_client(self) -> None:
        """
        High Level Purpose:
            In circumstances like first workstation vertical-slice validation, helps with verifying that one launched workstation can accept a prompt, normalize it, execute a mediated tool call, and record the assistant response.

        Reference to Theory:
            Verifies the workstation launcher, prompt model, tool mediation, and receipt path as one end-to-end slice.

        Example Input Output:
            Input: `test_prompt_workstation_session_runs_end_to_end_with_fake_client()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
            initial_task="Inspect the project.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Inspect the workspace and tell me what is there.",
            client=_FakeClient(),
        )
        self.assertIn("I inspected the workspace", report["assistant_text"])
        self.assertEqual(len(report["tool_receipts"]), 1)
        receipts = (self.root / "receipts" / "events.jsonl").read_text()
        self.assertIn("\"kind\": \"capability_call\"", receipts)
        self.assertIn("\"phase\": \"started\"", receipts)
        messages = (self.root / "MESSAGES.jsonl").read_text()
        self.assertIn("\"role\": \"user\"", messages)
        self.assertIn("\"role\": \"assistant\"", messages)

    def test_prompt_workstation_session_can_use_installed_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation end-to-end skill integration testing, helps with verifying that one workstation turn can drive `ws.skill.invoke` and return the installed skill result through the normal host-owned LLM loop.

        Reference to Theory:
            Verifies the workstation shell / pluggable-worker split as a real end-to-end path rather than only a direct capability helper.

        Example Input Output:
            Input: `test_prompt_workstation_session_can_use_installed_skill()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Use installed skills when appropriate.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Use the installed skill titled Workstation Greeting.",
            client=_FakeSkillInvokeClient(),
        )
        self.assertIn("hello from skill", report["assistant_text"])
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")

    def test_prompt_workstation_session_can_save_learnings_markdown_via_llm_tool(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Save chat learnings when requested.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Save the learnings from this chemistry discussion as a new markdown in notes/chat_learnings.md.",
            client=_FakeMarkdownCreateClient(),
        )
        destination = self.workspace / "notes" / "chat_learnings.md"
        self.assertTrue(destination.exists())
        self.assertIn("Saved the learnings markdown", report["assistant_text"])
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.markdown.create")
        self.assertIn("Saved Learnings", destination.read_text())
        self.assertEqual(len(report["learning_context_updates"]), 1)
        self.assertEqual(report["learning_context_updates"][0]["subject_id"], "chemistry")
        context = load_learning_context(self.workspace, "chemistry")
        self.assertEqual(context.canonical_title, "Chemistry")
        self.assertGreaterEqual(len(context.units), 1)

    def test_prompt_workstation_session_can_approve_skill_escalation(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation delegated-rights approval testing, helps with verifying that the host-owned prompt loop can approve a one-invocation escalation, retry the skill call, and record both the decision and the retried capability result.

        Reference to Theory:
            Verifies the workstation escalation model by keeping approval at the host boundary while still allowing the skill invocation to complete.

        Example Input Output:
            Input: `test_prompt_workstation_session_can_approve_skill_escalation()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Use installed skills when appropriate.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Use the installed skill and approve scratch write if needed.",
            client=_FakeEscalationSkillClient(),
            delegation_approval_callback=lambda _request: True,
        )
        self.assertIn("completed after approval", report["assistant_text"])
        tool_receipt = report["tool_receipts"][0]
        self.assertEqual(tool_receipt["result"]["status"], "ok")
        self.assertTrue(tool_receipt["result"]["escalation"]["approved"])
        self.assertEqual(tool_receipt["result"]["approved_delegation_scope"], "one_invocation")
        receipt_lines = [
            json.loads(line)
            for line in (self.root / "receipts" / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        rendered_receipts = "\n".join(json.dumps(item, sort_keys=True) for item in receipt_lines)
        self.assertIn("\"kind\": \"delegation_approval_requested\"", rendered_receipts)
        self.assertIn("\"kind\": \"delegation_approval_decision\"", rendered_receipts)
        capability_receipts = [item for item in receipt_lines if item.get("kind") == "capability_call"]
        self.assertEqual(capability_receipts[-1]["phase"], "completed")
        self.assertEqual(capability_receipts[-1]["target"], "skills")
        self.assertEqual(capability_receipts[-1]["result"]["status"], "ok")
        self.assertEqual(capability_receipts[-1]["delegation"]["status"], "ok")
        self.assertEqual(capability_receipts[-1]["delegation"]["scope"], "one_invocation")
        self.assertEqual(capability_receipts[-1]["delegation"]["requested"][0]["target"], "scratch")
        self.assertEqual(capability_receipts[-1]["delegation"]["approved"][0]["target"], "scratch")
        self.assertEqual(capability_receipts[-1]["delegation"]["escalated"][0]["target"], "scratch")
        self.assertEqual(capability_receipts[-1]["delegation"]["granted"][0]["target"], "scratch")

    def test_prompt_workstation_session_returns_direct_composition_approval_request_without_fallback(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation direct composition over connected trial skills, helps with verifying that an approval-required skill invocation closes the turn with a bounded approval request instead of falling through to the LLM and looping into generic tools.

        Reference to Theory:
            Verifies the skill-first permission model by keeping direct-composed prompts on the skill path even when the selected skill needs delegated rights.

        Example Input Output:
            Input: `test_prompt_workstation_session_returns_direct_composition_approval_request_without_fallback()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        python_bundle = trials_dir / "python.skill.yaml"
        python_bundle.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported Python archive skills when appropriate.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Create `realized-tests.zip` in mount `skill_tmp` from mount `skill_input` at `tests`.",
        )
        self.assertEqual(report["model"], "workstation-direct-composition")
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")
        self.assertEqual(report["tool_receipts"][0]["result"]["status"], "approval_required")
        self.assertIn("ws.fs.write on skill_tmp", report["assistant_text"])
        receipt_lines = [
            json.loads(line)
            for line in (self.root / "receipts" / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        capability_receipts = [item for item in receipt_lines if item.get("kind") == "capability_call"]
        self.assertEqual(capability_receipts[-1]["phase"], "approval_required")
        self.assertEqual(capability_receipts[-1]["target"], "skills")
        self.assertEqual(capability_receipts[-1]["delegation"]["status"], "approval_required")
        self.assertEqual(capability_receipts[-1]["delegation"]["requested"][0]["target"], "skill_input")
        self.assertEqual(capability_receipts[-1]["delegation"]["missing"][0]["target"], "skill_tmp")

    def test_prompt_workstation_session_executes_ansible_render_prompt_without_workspace_mount_inference(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct workstation prompting over ansible file-render skills, helps with verifying that absolute host paths do not get misprojected onto the workspace mount and therefore do not trigger spurious main-mount approval requests.

        Reference to Theory:
            Verifies the workstation shell keeps absolute-path ansible prompts on their intended host path rather than incorrectly converting them into workspace-relative mount operations.

        Example Input Output:
            Input: `test_prompt_workstation_session_executes_ansible_render_prompt_without_workspace_mount_inference()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        ansible_bundle = trials_dir / "ansible.skill.yaml"
        ansible_bundle.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "ansible" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported ansible skills when appropriate.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/ansible.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        absolute_output = Path(self.tempdir.name) / "absolute-app.conf"
        overrides = _materialize_ansible_fake_toolchain(Path(self.tempdir.name) / "ansible_fake_report")
        with patch.dict(os.environ, overrides, clear=False):
            report = prompt_workstation_session(
                root_path=self.root,
                prompt=f"Render `{absolute_output}` from the template text `port={{{{ port }}}}` with `port=8080`.",
            )
        self.assertEqual(report["model"], "workstation-direct-composition")
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")
        self.assertEqual(report["tool_receipts"][0]["result"]["status"], "ok")
        self.assertIn("Render template content", report["assistant_text"])
        self.assertEqual(absolute_output.read_text(encoding="utf-8"), "port=8080\n")

    def test_prompt_workstation_session_uses_repo_search_skill_when_available(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation capability-to-skill migration testing, helps with verifying that one host-owned workstation turn can drive repository search through `ws.skill.invoke` instead of a direct high-level capability.

        Reference to Theory:
            Verifies the workstation shell stays small while higher-level search behavior moves into a pluggable worker skill.

        Example Input Output:
            Input: `test_prompt_workstation_session_uses_repo_search_skill_when_available()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Use skills for higher-level behaviors.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Find where the main function is implemented.",
            client=_FakeRepoSearchSkillClient(),
        )
        self.assertIn("main function", report["assistant_text"])
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")

    def test_prompt_workstation_session_can_use_repo_search_skill_with_minimal_arguments(self) -> None:
        """
        High Level Purpose:
            In circumstances like live workstation provider behavior, helps with verifying that one workstation turn still succeeds when the model calls the repo-search skill by title and semantic unit without constructing a full structured payload itself.

        Reference to Theory:
            Verifies the workstation shell can complete the worker invocation contract from the task boundary instead of requiring the model to be perfect on the first tool call.

        Example Input Output:
            Input: `test_prompt_workstation_session_can_use_repo_search_skill_with_minimal_arguments()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Use skills for higher-level behaviors.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Find where workstation chat is implemented in this workspace.",
            client=_FakeMinimalRepoSearchSkillClient(),
        )
        self.assertIn("matches", report["assistant_text"])
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")

    def test_prompt_workstation_session_keeps_bytes_in_tool_results_json_safe(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Exercise bytes-safe prompt persistence.",
        )
        with patch(
            "workstation.session.run_workstation_openai_turn",
            return_value={
                "assistant_text": "Listed S3 objects.",
                "tool_receipts": [
                    {
                        "name": "ws.skill.invoke",
                        "arguments": {"skill_title": "Demo Bytes Skill", "target": "skills"},
                        "result": {
                            "status": "ok",
                            "skill_title": "Demo Bytes Skill",
                            "answer": b"raw-binary-answer",
                            "payload": {"body": b"bytes-body"},
                        },
                    }
                ],
                "model": "fake-model",
                "rounds": 1,
            },
        ):
            report = prompt_workstation_session(
                root_path=self.root,
                prompt="List objects in the S3 bucket `demo-bucket` with the boto3 SDK.",
                model="fake-model",
                max_tool_rounds=4,
            )
        self.assertEqual(report["assistant_text"], "Listed S3 objects.")
        last_response = json.loads((self.root / "LAST_RESPONSE.json").read_text())
        self.assertEqual(last_response["tool_receipts"][0]["result"]["answer"], "raw-binary-answer")
        self.assertEqual(last_response["tool_receipts"][0]["result"]["payload"]["body"], "bytes-body")

    def test_skill_invoke_derives_minimal_payload_for_imported_symbol_search_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like explicit workstation skill usage over imported trial workers, helps with verifying that `ws.skill.invoke` can derive the required worker payload from the user semantic unit instead of requiring the model to fabricate a full structured payload.

        Reference to Theory:
            Verifies the workstation skill-first policy by keeping an explicit imported-worker request on the skill path rather than silently falling back to generic repository tools.

        Example Input Output:
            Input: `test_skill_invoke_derives_minimal_payload_for_imported_symbol_search_skill()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "symbolsearch.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "symbolsearch" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported skills when appropriate.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/symbolsearch.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Symbol Search Commands 03 — Find Python Class Definition",
                "semantic_unit": "Use the symbol search skill to find the Python class definition for BSSCController under src.",
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("src/demo.py", result["answer"])
        self.assertIn("BSSCController", result["answer"])

    def test_nested_skill_answer_text_bounds_large_stdout(self) -> None:
        """
        High Level Purpose:
            In circumstances like large search-style worker output, helps with verifying that the shell-facing answer stays bounded instead of persisting unbounded stdout into workstation chat logs and receipts.

        Reference to Theory:
            Verifies the skill-first workstation shell can prefer workers without letting one large worker answer exhaust report and session storage.

        Example Input Output:
            Input: `test_nested_skill_answer_text_bounds_large_stdout()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        lines = [f"src/file_{index:02d}.py:{index}:match" for index in range(40)]
        answer = workstation_nested_skill_answer_text(_NestedSkillResult(stdout="\n".join(lines)))
        self.assertIn("src/file_00.py:0:match", answer)
        self.assertIn("... [truncated]", answer)
        self.assertLessEqual(len(answer), 4500)
        self.assertNotIn("src/file_39.py:39:match", answer)

    def test_nested_skill_answer_text_bounds_parsed_matches(self) -> None:
        """
        High Level Purpose:
            In circumstances like structured worker matches projected back into workstation chat, helps with verifying that the projected answer remains bounded even when the nested worker returned many matches.

        Reference to Theory:
            Verifies the workstation shell / pluggable-worker split still preserves bounded host artifacts for high-volume search workers.

        Example Input Output:
            Input: `test_nested_skill_answer_text_bounds_parsed_matches()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        matches = [f"src/file_{index:02d}.py:{index}:match" for index in range(35)]
        answer = workstation_nested_skill_answer_text(_NestedSkillResult(parsed_output={"matches": matches}))
        self.assertIn("src/file_00.py:0:match", answer)
        self.assertIn("... [truncated]", answer)
        self.assertLessEqual(len(answer), 4500)
        self.assertNotIn("src/file_34.py:34:match", answer)

    def test_bounded_nested_effect_traces_trims_large_match_lists(self) -> None:
        """
        High Level Purpose:
            In circumstances like nested workstation worker receipts, helps with verifying that large broker trace payloads are bounded before they are persisted into workstation capability receipts.

        Reference to Theory:
            Verifies the workstation shell preserves debugging context for nested workers without retaining unbounded broker match lists.

        Example Input Output:
            Input: `test_bounded_nested_effect_traces_trims_large_match_lists()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        traces = [
            {
                "effect_kind": "fs.find_mount",
                "result": {
                    "matches": [f"src/file_{index:02d}.py" for index in range(50)],
                },
            }
        ]
        bounded = bounded_nested_effect_traces(traces)
        self.assertEqual(len(bounded), 1)
        self.assertEqual(len(bounded[0]["result"]["matches"]), 20)
        self.assertEqual(bounded[0]["result"]["matches"][0], "src/file_00.py")
        self.assertEqual(bounded[0]["result"]["matches"][-1], "src/file_19.py")

    def test_workstation_llm_turn_does_not_silently_fallback_after_explicit_skill_failure(self) -> None:
        """
        High Level Purpose:
            In circumstances like explicit workstation skill requests, helps with verifying that the host-owned LLM turn closes with a bounded skill failure instead of silently drifting into generic host-tool fallback.

        Reference to Theory:
            Verifies the workstation skill-first policy for explicit skill requests by keeping the turn on the skill path even when the initial invocation fails.

        Example Input Output:
            Input: `test_workstation_llm_turn_does_not_silently_fallback_after_explicit_skill_failure()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        client = _FakeExplicitSkillFailureThenFallbackClient()
        report = run_workstation_openai_turn(
            session=WorkstationSession.from_dict(
                launch_workstation_session(
                    root_path=self.root,
                    workspace_path=self.workspace,
                    initial_task="Use imported skills when appropriate.",
                )
            ),
            task_contract=normalize_prompt_to_task_boundary_contract(
                "Use the symbol search skill to find the Python class definition for BSSCController under src."
            ),
            prompt="Use the symbol search skill to find the Python class definition for BSSCController under src.",
            message_history=[],
            tool_definitions=[],
            tool_executor=lambda capability_name, arguments: {
                "status": "error",
                "capability": capability_name,
                "skill_title": str(arguments.get("skill_title", "")),
                "answer": "Invocation of Symbol Search Commands 03 — Find Python Class Definition failed: Could not derive required inputs from the request (root, symbol).",
            },
            model="test-model",
            client=client,
        )
        self.assertEqual(client.chat.completions.calls, 1)
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")
        self.assertFalse(report["fallback_used"])
        self.assertEqual(report["fulfilled_by"], "ws.skill.invoke")
        self.assertIn("Could not derive required inputs", report["assistant_text"])

    def test_workstation_llm_turn_stops_after_skill_approval_required_for_implicit_skill_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompting where the shell or LLM implies a skill family rather than naming it explicitly, helps with verifying that an approval-required skill invocation closes the turn with a permission request instead of continuing into generic host-tool fallback.

        Reference to Theory:
            Verifies the workstation permission rule for implied skills: try the skill, ask for approval if needed, and do not silently substitute unrelated tools.

        Example Input Output:
            Input: `test_workstation_llm_turn_stops_after_skill_approval_required_for_implicit_skill_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        client = _FakeImplicitSkillApprovalThenFallbackClient()
        report = run_workstation_openai_turn(
            session=WorkstationSession.from_dict(
                launch_workstation_session(
                    root_path=self.root,
                    workspace_path=self.workspace,
                    initial_task="Use imported skills when appropriate.",
                )
            ),
            task_contract=normalize_prompt_to_task_boundary_contract(
                "Create `realized-tests.zip` in mount `skill_tmp` from mount `skill_input` at `tests`."
            ),
            prompt="Create `realized-tests.zip` in mount `skill_tmp` from mount `skill_input` at `tests`.",
            message_history=[],
            tool_definitions=[],
            tool_executor=lambda capability_name, arguments: {
                "status": "approval_required",
                "capability": capability_name,
                "skill_title": str(arguments.get("skill_title", "")),
                "missing_delegation": [
                    {
                        "capability": "ws.fs.write",
                        "target": "skill_tmp",
                        "rationale": "Need to expose the requested workstation mount to the invoked skill.",
                    }
                ],
            },
            model="test-model",
            client=client,
        )
        self.assertEqual(client.chat.completions.calls, 1)
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")
        self.assertEqual(report["fulfilled_by"], "ws.skill.invoke")
        self.assertFalse(report["fallback_used"])
        self.assertIn("requires approval", report["assistant_text"])
        self.assertIn("ws.fs.write on skill_tmp", report["assistant_text"])

    def test_prompt_workstation_session_returns_structured_tool_error_instead_of_raising(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation prompting over imperfect model tool arguments, helps with verifying that one bad attachment target becomes a structured tool error instead of aborting the whole turn.

        Reference to Theory:
            Supports the workstation shell by keeping capability failures mediated and recoverable within the turn rather than letting attachment-resolution exceptions escape.

        Example Input Output:
            Input: `test_prompt_workstation_session_returns_structured_tool_error_instead_of_raising()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
            initial_task="Inspect the project.",
        )
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Inspect the workspace even if one tool call is malformed.",
            client=_FakeBadTargetThenAnswerClient(),
        )
        self.assertEqual(report["assistant_text"], "Recovered after tool error.")
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["result"]["status"], "error")
        self.assertEqual(report["tool_receipts"][0]["result"]["error_type"], "ValueError")

    def test_prompt_workstation_session_returns_direct_failure_answer_without_llm_retry(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct workstation worker composition over a broken imported worker, helps with verifying that an immediate skill failure can still close the turn with a bounded failure answer instead of burning tool rounds in a generic retry loop.

        Reference to Theory:
            Supports the workstation shell / pluggable-worker model by keeping direct worker composition deterministic even when the selected worker fails before producing a normal answer payload.

        Example Input Output:
            Input: `test_prompt_workstation_session_returns_direct_failure_answer_without_llm_retry()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Use direct composition when appropriate.",
        )
        with patch(
            "workstation.session.preferred_workstation_skill_invocation_plan",
            return_value={
                "skill_title": "Broken Worker",
                "semantic_unit": "Do the broken thing.",
            },
        ), patch(
            "workstation.session.execute_workstation_capability",
            return_value={
                "status": "error",
                "answer": "Invocation of Broken Worker failed: SyntaxError: unmatched ')'",
            },
        ), patch(
            "workstation.session.run_workstation_openai_turn",
            side_effect=AssertionError("LLM retry path should not run after a direct failure answer."),
        ):
            report = prompt_workstation_session(
                root_path=self.root,
                prompt="Do the broken thing.",
                client=None,
            )
        self.assertEqual(
            report["assistant_text"],
            "Invocation of Broken Worker failed: SyntaxError: unmatched ')'",
        )
        self.assertEqual(report["model"], "workstation-direct-composition")
        self.assertEqual(report["direct_result_status"], "error")
        self.assertEqual(len(report["tool_receipts"]), 1)
        self.assertEqual(report["tool_receipts"][0]["name"], "ws.skill.invoke")

    def test_prompt_workstation_session_routes_natural_language_skill_import_to_shell_command(self) -> None:
        """
        High Level Purpose:
            In circumstances like natural-language workstation lifecycle prompts, helps with verifying that an obvious skill import request stays on the deterministic shell utility path instead of being misread as an imported worker invocation.

        Reference to Theory:
            Verifies the shell / worker separation by keeping skill lifecycle operations on the shell path before direct composition or LLM planning can claim them.

        Example Input Output:
            Input: `test_prompt_workstation_session_routes_natural_language_skill_import_to_shell_command()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        (trials_dir / "demo.skill.yaml").write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Imported Skill",
                    "answer: hello from imported skill",
                ]
            )
            + "\n"
        )
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Manage workstation skills from chat.",
        )
        with patch(
            "workstation.session.preferred_workstation_skill_invocation_plan",
            side_effect=AssertionError("Direct composition should not run for shell import prompts."),
        ), patch(
            "workstation.session.run_workstation_openai_turn",
            side_effect=AssertionError("LLM path should not run for shell import prompts."),
        ):
            report = prompt_workstation_session(
                root_path=self.root,
                prompt="Import the skill file at trials/demo.skill.yaml into this workstation.",
                client=None,
            )
        self.assertEqual(report["model"], "workstation-shell-command")
        self.assertEqual(report["fulfilled_by"], "ws.skill.import")
        self.assertFalse(report["fallback_used"])
        self.assertIn("Import status: ok", report["assistant_text"])
        self.assertIn("Demo Imported Skill", report["assistant_text"])

    def test_cli_handlers_cover_launch_and_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation CLI regression testing, helps with verifying that the thin workstation entrypoints can launch and prompt a session without involving the outer controller runtime.

        Reference to Theory:
            Verifies the workstation entry surface while keeping the implementation scoped to the workstation package.

        Example Input Output:
            Input: `test_cli_handlers_cover_launch_and_prompt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_argv = ["workstation-launch", "--root", str(self.root), "--workspace", str(self.workspace), "--task", "Inspect the project."]
        for capability in (*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"):
            launch_argv.extend(["--capability", capability])
        launch_args = parse_args(launch_argv)
        with redirect_stdout(io.StringIO()) as buffer:
            exit_code = handle_workstation_launch_command(launch_args)
        self.assertEqual(exit_code, 0)
        self.assertIn("session_id", buffer.getvalue())
        prompt_args = parse_args(
            ["workstation-prompt", "--root", str(self.root), "--prompt", "Inspect the workspace."]
        )
        with patch("workstation.llm_driver.build_workstation_openai_client", return_value=_FakeClient()):
            with redirect_stdout(io.StringIO()) as buffer:
                exit_code = handle_workstation_prompt_command(prompt_args)
        self.assertEqual(exit_code, 0)
        self.assertIn("assistant_text", buffer.getvalue())

    def test_cli_handlers_cover_workstation_skill_lifecycle(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation product-surface regression testing, helps with verifying that the deterministic CLI lifecycle commands for skill catalog, import, and export operate against the same persistent workstation skill home as the chat surface.

        Reference to Theory:
            Verifies that workstation skill lifecycle is exposed as a first-class CLI surface rather than only through internal Python capability calls.

        Example Input Output:
            Input: `test_cli_handlers_cover_workstation_skill_lifecycle()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        skill_file = self.workspace / "cli_import_skill.yaml"
        skill_file.write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: CLI Imported Greeting",
                    "answer: hello from cli import",
                    "",
                ]
            )
        )
        launch_args = parse_args(
            ["workstation-launch", "--root", str(self.root), "--workspace", str(self.workspace), "--task", "Use skills."]
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(handle_workstation_launch_command(launch_args), 0)

        catalog_args = parse_args(["workstation-skill-catalog", "--root", str(self.root)])
        with redirect_stdout(io.StringIO()) as buffer:
            exit_code = handle_workstation_skill_catalog_command(catalog_args)
        self.assertEqual(exit_code, 0)
        self.assertIn("\"skills\"", buffer.getvalue())

        import_args = parse_args(
            ["workstation-skill-import", "--root", str(self.root), "--skill-file", str(skill_file)]
        )
        with redirect_stdout(io.StringIO()) as buffer:
            exit_code = handle_workstation_skill_import_command(import_args)
        self.assertEqual(exit_code, 0)
        self.assertIn("CLI Imported Greeting", buffer.getvalue())

        export_target = Path(self.tempdir.name) / "cli_exported_skill.yaml"
        export_args = parse_args(
            [
                "workstation-skill-export",
                "--root",
                str(self.root),
                "--skill-title",
                "CLI Imported Greeting",
                "--out",
                str(export_target),
            ]
        )
        with redirect_stdout(io.StringIO()) as buffer:
            exit_code = handle_workstation_skill_export_command(export_args)
        self.assertEqual(exit_code, 0)
        self.assertIn("copied_to", buffer.getvalue())
        self.assertTrue(export_target.exists())
        self.assertIn("CLI Imported Greeting", export_target.read_text())

    def test_validate_workstation_trial_domains_runs_fake_prompt_runner(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation trial-audit regression testing, helps with verifying that the workstation trial validator can import one domain bundle, create fresh per-prompt workstation sessions, and record prompt reports without a live provider dependency.

        Reference to Theory:
            Verifies the workstation/trial integration surface while keeping the audit logic inside the workstation package.

        Example Input Output:
            Input: `test_validate_workstation_trial_domains_runs_fake_prompt_runner()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_root = Path(self.tempdir.name) / "trial_domains"
        demo_domain = trials_root / "demo"
        demo_domain.mkdir(parents=True, exist_ok=True)
        (demo_domain / "PROMPTS.md").write_text("- What is the greeting worker?\n")
        (demo_domain / "skill.yaml").write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Greeting Worker",
                    "answer: hello from demo worker",
                    "",
                ]
            )
        )
        report_root = Path(self.tempdir.name) / "workstation_trial_reports"

        def fake_prompt_runner(*, root_path: Path, prompt: str, model: str | None, max_tool_rounds: int) -> dict[str, object]:
            return {
                "assistant_text": f"Handled: {prompt}",
                "model": str(model or "fake"),
                "tool_receipts": [],
                "root_path": str(root_path),
                "rounds": 0,
                "task_contract": {"semantic_unit": prompt},
            }

        report = validate_workstation_trial_domains(
            domains=("demo",),
            workspace_path=self.workspace,
            trials_root=trials_root,
            report_root=report_root,
            model="fake-model",
            max_tool_rounds=2,
            prompt_runner=fake_prompt_runner,
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(len(report["domains"]), 1)
        domain_report = report["domains"][0]
        self.assertEqual(domain_report["status"], "ok")
        self.assertEqual(domain_report["prompt_summary"]["ok"], 1)
        self.assertTrue(Path(domain_report["sqlite"]).exists())
        self.assertTrue(Path(domain_report["canonical_export"]).exists())
        self.assertTrue(Path(domain_report["prompt_results"][0]["report"]).exists())
        sessions_dir = report_root / "demo" / "sessions"
        self.assertTrue(sessions_dir.exists())
        self.assertEqual(list(sessions_dir.iterdir()), [])

    def test_validate_workstation_trial_domains_marks_terminal_tool_failures_as_non_ok(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation trial-audit regression testing, helps with verifying that prompt success classification follows the terminal tool receipt status instead of treating any non-empty assistant text as a successful prompt.

        Reference to Theory:
            Verifies the trial-reporting boundary so successful workstation prompts cannot mask a terminal `error` or `approval_required` tool outcome.

        Example Input Output:
            Input: `test_validate_workstation_trial_domains_marks_terminal_tool_failures_as_non_ok()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_root = Path(self.tempdir.name) / "trial_domains"
        demo_domain = trials_root / "demo"
        demo_domain.mkdir(parents=True, exist_ok=True)
        (demo_domain / "PROMPTS.md").write_text("- Write hello\n")
        (demo_domain / "skill.yaml").write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Greeting Worker",
                    "answer: hello from demo worker",
                    "",
                ]
            )
        )
        report_root = Path(self.tempdir.name) / "workstation_trial_reports"

        for terminal_status in ("approval_required", "error"):
            with self.subTest(terminal_status=terminal_status):
                def fake_prompt_runner(*, root_path: Path, prompt: str, model: str | None, max_tool_rounds: int) -> dict[str, object]:
                    return {
                        "assistant_text": f"Handled: {prompt}",
                        "model": str(model or "fake"),
                        "tool_receipts": [
                            {
                                "name": "ws.skill.invoke",
                                "arguments": {"skill_title": "Demo Skill"},
                                "result": {"status": terminal_status, "skill_title": "Demo Skill"},
                            }
                        ],
                        "root_path": str(root_path),
                        "rounds": 1,
                        "task_contract": {"semantic_unit": prompt},
                    }

                report = validate_workstation_trial_domains(
                    domains=("demo",),
                    workspace_path=self.workspace,
                    trials_root=trials_root,
                    report_root=report_root / terminal_status,
                    model="fake-model",
                    max_tool_rounds=2,
                    prompt_runner=fake_prompt_runner,
                )
                self.assertEqual(report["status"], "partial")
                domain_report = report["domains"][0]
                self.assertEqual(domain_report["status"], "error")
                self.assertEqual(domain_report["prompt_summary"]["ok"], 0)
                self.assertEqual(
                    domain_report["prompt_results"][0]["status"],
                    f"error_terminal_tool_{terminal_status}",
                )
                self.assertEqual(
                    domain_report["prompt_results"][0]["terminal_tool_status"],
                    terminal_status,
                )

    def test_validate_workstation_trial_domains_default_runner_autoapproves_delegation(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation trial-audit regression testing, helps with verifying that the default prompt runner auto-approves bounded delegation so trial prompts can observe final worker outcomes rather than stopping at intermediate approval requests.

        Reference to Theory:
            Verifies the real workstation trial harness keeps approval host-owned while still exercising the final skill path for trial compatibility.

        Example Input Output:
            Input: `test_validate_workstation_trial_domains_default_runner_autoapproves_delegation()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_root = Path(self.tempdir.name) / "trial_domains"
        demo_domain = trials_root / "demo"
        demo_domain.mkdir(parents=True, exist_ok=True)
        (demo_domain / "PROMPTS.md").write_text("- Write hello\n")
        (demo_domain / "skill.yaml").write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Greeting Worker",
                    "answer: hello from demo worker",
                    "",
                ]
            )
        )
        report_root = Path(self.tempdir.name) / "workstation_trial_reports"

        with patch("workstation.trial_validation.prompt_workstation_session") as mock_prompt:
            def _fake_prompt(**kwargs: object) -> dict[str, object]:
                approval_callback = kwargs.get("delegation_approval_callback")
                self.assertTrue(callable(approval_callback))
                self.assertTrue(bool(approval_callback(object())))
                return {
                    "assistant_text": "Handled with approval.",
                    "model": "fake-model",
                    "tool_receipts": [
                        {
                            "name": "ws.skill.invoke",
                            "arguments": {"skill_title": "Demo Skill"},
                            "result": {"status": "ok", "skill_title": "Demo Skill"},
                        }
                    ],
                    "rounds": 1,
                    "task_contract": {"semantic_unit": str(kwargs.get("prompt", ""))},
                }

            mock_prompt.side_effect = _fake_prompt
            report = validate_workstation_trial_domains(
                domains=("demo",),
                workspace_path=self.workspace,
                trials_root=trials_root,
                report_root=report_root / "autoapprove",
                model="fake-model",
                max_tool_rounds=2,
            )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["domains"][0]["status"], "ok")
        self.assertEqual(report["domains"][0]["prompt_results"][0]["terminal_tool_status"], "ok")

    def test_launch_workstation_session_can_attach_shared_blend_world_mounts(self) -> None:
        """
        High Level Purpose:
            In circumstances like Blend-grounded workstation launches, helps with verifying that a session can project shared mutable world mounts instead of always binding `scratch` and `output` to prompt-local session directories.

        Reference to Theory:
            Verifies the first shared-world continuity seam so multiple sessions can act against the same world rather than only passing values across isolated prompts.

        Example Input Output:
            Input: `test_launch_workstation_session_can_attach_shared_blend_world_mounts()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        shared_world = Path(self.tempdir.name) / "shared_world"
        first_root = Path(self.tempdir.name) / "ws_one"
        second_root = Path(self.tempdir.name) / "ws_two"
        first = launch_workstation_session(
            root_path=first_root,
            workspace_path=self.workspace,
            blend_world_path=shared_world,
            initial_task="Use shared world.",
        )
        second = launch_workstation_session(
            root_path=second_root,
            workspace_path=self.workspace,
            blend_world_path=shared_world,
            initial_task="Use shared world.",
        )
        first_by_name = {item["name"]: item for item in first["attachments"]}
        second_by_name = {item["name"]: item for item in second["attachments"]}
        self.assertEqual(first_by_name["scratch"]["source"], str((shared_world / "scratch").resolve()))
        self.assertEqual(first_by_name["output"]["source"], str((shared_world / "output").resolve()))
        self.assertEqual(second_by_name["scratch"]["source"], first_by_name["scratch"]["source"])
        self.assertEqual(second_by_name["output"]["source"], first_by_name["output"]["source"])
        world_payload = json.loads((first_root / "BLEND_WORLD.json").read_text())
        self.assertTrue(world_payload["world_id"].startswith("bworld_"))
        self.assertEqual(
            first_by_name["scratch"]["metadata"]["blend_world_id"],
            world_payload["world_id"],
        )
        self.assertEqual(
            second_by_name["scratch"]["metadata"]["blend_world_id"],
            world_payload["world_id"],
        )

    def test_validate_workstation_trial_domains_shares_world_mounts_across_prompt_sessions(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation trial-audit regression testing, helps with verifying that prompt-local sessions can still share one mutable world when the trial domain expects continuity across prompts.

        Reference to Theory:
            Verifies Blend-style sharing in the trial harness by proving that separate prompt sessions can operate on the same `skill_tmp` world mount.

        Example Input Output:
            Input: `test_validate_workstation_trial_domains_shares_world_mounts_across_prompt_sessions()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_root = Path(self.tempdir.name) / "trial_domains"
        demo_domain = trials_root / "demo"
        demo_domain.mkdir(parents=True, exist_ok=True)
        (demo_domain / "PROMPTS.md").write_text("- Write shared world file\n- Read shared world file\n")
        (demo_domain / "skill.yaml").write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Greeting Worker",
                    "answer: hello from demo worker",
                    "",
                ]
            )
        )
        report_root = Path(self.tempdir.name) / "workstation_trial_reports"

        def fake_prompt_runner(*, root_path: Path, prompt: str, model: str | None, max_tool_rounds: int) -> dict[str, object]:
            attachments_payload = json.loads((root_path / "ATTACHMENTS.json").read_text())
            attachments = {
                str(item["name"]): dict(item)
                for item in attachments_payload.get("attachments", [])
                if isinstance(item, dict)
            }
            tmp_root = Path(attachments["skill_tmp"]["source"])
            shared_file = tmp_root / "shared.txt"
            if prompt.startswith("Write"):
                shared_file.write_text("shared hello\n")
                answer = "wrote shared file"
            else:
                answer = shared_file.read_text().strip()
            return {
                "assistant_text": answer,
                "model": str(model or "fake"),
                "tool_receipts": [
                    {
                        "name": "ws.skill.invoke",
                        "arguments": {"skill_title": "Demo Skill"},
                        "result": {"status": "ok", "skill_title": "Demo Skill"},
                    }
                ],
                "rounds": 1,
                "task_contract": {"semantic_unit": prompt},
            }

        report = validate_workstation_trial_domains(
            domains=("demo",),
            workspace_path=self.workspace,
            trials_root=trials_root,
            report_root=report_root,
            model="fake-model",
            max_tool_rounds=2,
            prompt_runner=fake_prompt_runner,
        )
        self.assertEqual(report["status"], "ok")
        domain_report = report["domains"][0]
        self.assertEqual(domain_report["status"], "ok")
        self.assertEqual(domain_report["prompt_summary"]["ok"], 2)
        self.assertEqual(domain_report["prompt_results"][1]["assistant_text"], "shared hello")
        self.assertEqual(Path(domain_report["world_root"]), (report_root / "demo" / "world").resolve())

    def test_materialize_deviceuser_fake_macos_toolchain_creates_fake_commands(self) -> None:
        """
        High Level Purpose:
            In circumstances like safe workstation validation of device-user workers, helps with verifying that the fake macOS toolchain is materialized with executable command shims and a durable log path.

        Reference to Theory:
            Verifies the workstation trial harness can audit side-effecting device-user prompts without touching the real desktop environment.

        Example Input Output:
            Input: `test_materialize_deviceuser_fake_macos_toolchain_creates_fake_commands()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report_dir = Path(self.tempdir.name) / "deviceuser_trial_report"
        overrides = _materialize_deviceuser_fake_macos_toolchain(report_dir)
        fakebin = report_dir / "fakebin"
        self.assertTrue((fakebin / "open").exists())
        self.assertTrue((fakebin / "pbcopy").exists())
        self.assertTrue((fakebin / "screencapture").exists())
        self.assertIn(str(fakebin), overrides["PATH"])
        self.assertEqual(
            overrides["WORKSTATION_DEVICEUSER_FAKE_LOG"],
            str(report_dir / "fake_macos_tools.log"),
        )

    def test_skill_invoke_uses_normalized_bash_screenshot_runtime_for_imported_deviceuser_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like imported device-user bash workers whose learned shell body still contains a literal example desktop path, helps with verifying that mediated workstation invocation upgrades the runtime to the governed mount-aware screenshot implementation before execution.

        Reference to Theory:
            Supports shared-world execution by making the invoked screenshot worker target the delegated workstation mount instead of a baked example host path from the learned bundle.

        Example Input Output:
            Input: `test_skill_invoke_uses_normalized_bash_screenshot_runtime_for_imported_deviceuser_skill()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "deviceuser.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "deviceuser" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported device-user skills.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/deviceuser.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        report_dir = Path(self.tempdir.name) / "deviceuser_invoke_report"
        overrides = _materialize_deviceuser_fake_macos_toolchain(report_dir)
        with patch.dict(os.environ, overrides, clear=False):
            result = execute_workstation_capability(
                session,
                "ws.skill.invoke",
                {
                    "skill_title": "Device User Capabilities 10 — Capture Screenshot To File / Device User Capabilities 10 Capture Screenshot To File",
                    "semantic_unit": "Take a screenshot and save it to mount `skill_tmp` at `deviceuser-screen.png`.",
                    "invocation_payload": {
                        "payload": {
                            "mount": "skill_tmp",
                            "relative_path": "deviceuser-screen.png",
                        }
                    },
                    "approved_delegation": [{"capability": "ws.fs.write", "target": "skill_tmp"}],
                    "approved_delegation_scope": "one_invocation",
                },
            )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result.get("result_payload", {}).get("status"), "captured")
        skill_tmp_attachment = next(item for item in session.attachments if item.name == "skill_tmp")
        captured_path = (Path(skill_tmp_attachment.source) / "deviceuser-screen.png").resolve()
        self.assertTrue(captured_path.exists())

    def test_materialize_apiclient_fake_http_environment_intercepts_placeholder_urls(self) -> None:
        """
        High Level Purpose:
            In circumstances like safe workstation validation of API-client workers, helps with verifying that the fake HTTP environment intercepts placeholder trial URLs inside child Python runtimes.

        Reference to Theory:
            Verifies the workstation trial harness can audit connected workers deterministically without depending on public DNS or external services.

        Example Input Output:
            Input: `test_materialize_apiclient_fake_http_environment_intercepts_placeholder_urls()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report_dir = Path(self.tempdir.name) / "apiclient_trial_report"
        overrides = _materialize_apiclient_fake_http_environment(report_dir)
        env = os.environ.copy()
        env.update(overrides)
        result = subprocess.run(
            [
                "python3",
                "-c",
                "import json; from urllib.request import urlopen; "
                "print(json.loads(urlopen('https://api.example.com/items/42').read().decode('utf-8'))['id'])",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.stdout.strip(), "42")
        self.assertEqual(
            overrides["WORKSTATION_APICLIENT_FAKE_LOG"],
            str(report_dir / "fake_http.log"),
        )

    def test_materialize_ansible_fake_toolchain_intercepts_privileged_playbooks(self) -> None:
        """
        High Level Purpose:
            In circumstances like safe workstation validation of ansible workers, helps with verifying that the fake ansible toolchain can execute privileged-looking playbook shapes deterministically without touching real host users or services.

        Reference to Theory:
            Verifies the workstation trial harness preserves the ansible worker surface while replacing host-specific side effects with validator-owned fakes.

        Example Input Output:
            Input: `test_materialize_ansible_fake_toolchain_intercepts_privileged_playbooks()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report_dir = Path(self.tempdir.name) / "ansible_trial_report"
        overrides = _materialize_ansible_fake_toolchain(report_dir)
        playbook = Path(self.tempdir.name) / "boundary_playbook.yml"
        vars_path = Path(self.tempdir.name) / "boundary_vars.json"
        playbook.write_text(
            "\n".join(
                [
                    "- hosts: localhost",
                    "  gather_facts: false",
                    "  tasks:",
                    "    - name: Ensure user exists",
                    "      user:",
                    "        name: \"{{ username }}\"",
                    "        state: present",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        vars_path.write_text(json.dumps({"username": "demo-ansible"}), encoding="utf-8")
        env = os.environ.copy()
        env.update(overrides)
        result = subprocess.run(
            [
                "ansible-playbook",
                "-i",
                "localhost,",
                "-c",
                "local",
                str(playbook),
                "--extra-vars",
                f"@{vars_path}",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("TASK [Ensure user exists]", result.stdout)
        self.assertEqual(
            overrides["WORKSTATION_ANSIBLE_FAKE_LOG"],
            str(report_dir / "fake_ansible.log"),
        )

    def test_materialize_sdkuser_fake_sdk_environment_intercepts_child_imports(self) -> None:
        """
        High Level Purpose:
            In circumstances like safe workstation validation of SDK-user workers, helps with verifying that the fake SDK environment satisfies child Python imports for representative cloud clients without requiring real package installs.

        Reference to Theory:
            Verifies the workstation trial harness preserves the SDK worker surface while replacing external package and credential dependencies with deterministic fakes.

        Example Input Output:
            Input: `test_materialize_sdkuser_fake_sdk_environment_intercepts_child_imports()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        report_dir = Path(self.tempdir.name) / "sdkuser_trial_report"
        overrides = _materialize_sdkuser_fake_sdk_environment(report_dir)
        env = os.environ.copy()
        env.update(overrides)
        result = subprocess.run(
            [
                "python3",
                "-c",
                (
                    "import json; "
                    "from openai import OpenAI; "
                    "import boto3; "
                    "print(OpenAI().responses.create(model='gpt-5.4', input='Say hello in one sentence.').output_text); "
                    "print(json.dumps([item['Key'] for item in boto3.client('s3').list_objects_v2(Bucket='demo-bucket').get('Contents', [])]))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        stdout_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(stdout_lines[0], "Hello.")
        self.assertIn("reports/daily.json", stdout_lines[1])
        self.assertEqual(
            overrides["WORKSTATION_SDKUSER_FAKE_LOG"],
            str(report_dir / "fake_sdk.log"),
        )

    def test_direct_composition_derives_sdkuser_payloads_and_defaults(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation direct composition for SDK-user prompts, helps with verifying that prompt-local SDK values and required fake credentials are turned into the right structured worker inputs.

        Reference to Theory:
            Verifies the workstation shell can invoke pluggable SDK workers directly from natural-language prompts without forcing the LLM to hand-assemble payloads.

        Example Input Output:
            Input: `test_direct_composition_derives_sdkuser_payloads_and_defaults()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        openai_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"model": "required input value", "prompt": "required input value"},
            prompt="Generate a short text response with the OpenAI SDK using model `gpt-5.4` and prompt `Say hello in one sentence.`.",
            skill_title="SDK User Commands 01 — OpenAI Text Response",
        )
        self.assertEqual(
            openai_payload,
            {"model": "gpt-5.4", "prompt": "Say hello in one sentence."},
        )
        list_s3_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"bucket": "required input value", "prefix": "required input value"},
            prompt="List objects in the S3 bucket `demo-bucket` with the boto3 SDK.",
            skill_title="SDK User Commands 04 — Boto3 List S3 Objects",
        )
        self.assertEqual(
            list_s3_payload,
            {"bucket": "demo-bucket", "prefix": ""},
        )
        upload_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"local_path": "required input value", "bucket": "required input value", "key": "required input value"},
            prompt="Upload `/tmp/report.txt` to the S3 bucket `demo-bucket` as key `reports/report.txt`.",
            skill_title="SDK User Commands 05 — Boto3 Upload File To S3",
        )
        self.assertEqual(
            upload_payload,
            {"local_path": "/tmp/report.txt", "bucket": "demo-bucket", "key": "reports/report.txt"},
        )

    def test_workstation_missing_required_inputs_accepts_explicit_empty_string_values(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation invocation of string-valued SDK or mount-root skills, helps with verifying that an explicit empty string is treated as a provided value instead of being rejected as missing.

        Reference to Theory:
            Supports skill-first invocation by allowing bounded defaults such as an empty prefix or mount-root relative path to flow through the declared worker contract without false missing-input failures.

        Example Input Output:
            Input: `test_workstation_missing_required_inputs_accepts_explicit_empty_string_values()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "SDK User Commands 04 — Boto3 List S3 Objects",
                "declaration": {
                    "intent": "List S3 objects.",
                    "inputs": {
                        "bucket": "required input value",
                        "prefix": "required input value",
                    },
                    "outputs": {"result": "execution result"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": [],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                    "executor_framework": "python3",
                },
                "inputs": {
                    "bucket": "required input value",
                    "prefix": "required input value",
                },
                "outputs": {"result": "execution result"},
                "executor": "python3",
                "entrypoint": "main",
                "python": "def main(bucket: str = '', prefix: str = ''):\n    return {'status': 'ok'}\n",
            }
        )
        self.assertEqual(
            workstation_missing_required_inputs(
                artifact=artifact,
                payload={"bucket": "demo-bucket", "prefix": ""},
            ),
            [],
        )

    def test_skill_invoke_derives_source_mount_read_delegation_for_copy_style_skills(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation invocation of source/destination mount skills whose declarations only advertise write effects, helps with verifying that the source mount still receives a read delegation because the workflow semantically depends on reading from it.

        Reference to Theory:
            Supports shared-world skill execution by ensuring source-mounted artifacts resolve against the workstation world instead of falling back to a baked skill-local temp mount.

        Example Input Output:
            Input: `test_skill_invoke_derives_source_mount_read_delegation_for_copy_style_skills()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported Python file skills.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Python Commands 14 — Extract Zip Archive",
                "source_mount": "skill_tmp",
                "source_relative_path": "realized-tests.zip",
                "destination_mount": "skill_output",
                "destination_relative_path": "extracted-tests",
                "approved_delegation": [{"capability": "ws.fs.write", "target": "skill_output"}],
                "approved_delegation_scope": "one_invocation",
            },
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("skill_tmp", result.get("delegated_virtual_mounts", {}))
        self.assertEqual(
            sorted(result["delegated_virtual_mounts"]["skill_tmp"].get("permissions", [])),
            ["list", "read"],
        )

    def test_skill_invoke_derives_source_mount_write_delegation_for_move_style_skills(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation invocation of move-style mount skills, helps with verifying that the source mount receives write delegation in addition to read because the move mutates the source world object.

        Reference to Theory:
            Supports shared-world execution by preserving the fact that moving an artifact is not a pure read-from-source operation.

        Example Input Output:
            Input: `test_skill_invoke_derives_source_mount_write_delegation_for_move_style_skills()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported Python file skills.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")
        result = execute_workstation_capability(
            session,
            "ws.skill.invoke",
            {
                "skill_title": "Python Commands 06 — Move File",
                "source_mount": "skill_tmp",
                "source_relative_path": "python-readme.copy",
                "destination_mount": "skill_output",
                "destination_relative_path": "python-readme.moved",
                "approved_delegation": [
                    {"capability": "ws.fs.write", "target": "skill_tmp"},
                    {"capability": "ws.fs.write", "target": "skill_output"},
                ],
                "approved_delegation_scope": "one_invocation",
            },
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("skill_tmp", result.get("delegated_virtual_mounts", {}))
        self.assertEqual(
            sorted(result["delegated_virtual_mounts"]["skill_tmp"].get("permissions", [])),
            ["list", "read", "write"],
        )

    def test_skill_invoke_surfaces_nested_error_payload_as_error_status(self) -> None:
        """
        High Level Purpose:
            In circumstances like nested worker execution that returns a structured broker error while still exiting the process cleanly, helps with verifying that the outer workstation capability reports an error instead of masking it as `ok`.

        Reference to Theory:
            Supports receipt integrity by making terminal worker failure payloads determine the outer skill-invocation status.

        Example Input Output:
            Input: `test_skill_invoke_surfaces_nested_error_payload_as_error_status()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        trials_dir = self.workspace / "trials"
        trials_dir.mkdir(parents=True, exist_ok=True)
        trial_bundle_path = trials_dir / "python.skill.yaml"
        trial_bundle_path.write_text(
            (Path(__file__).resolve().parents[1] / "trials" / "python" / "skill.yaml").read_text()
        )
        session = WorkstationSession.from_dict(
            launch_workstation_session(
                root_path=self.root,
                workspace_path=self.workspace,
                initial_task="Use imported Python file skills.",
            )
        )
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "main",
                "path": "trials/python.skill.yaml",
            },
        )
        self.assertEqual(import_result["status"], "ok")

        class _PatchedNestedResult:
            def __init__(self) -> None:
                self.ok = True
                self.stdout = ""
                self.stderr = ""
                self.answer = ""
                self.notes = []
                self.parsed_output = {"status": "error", "broker": "fs.move_mount", "error": "boom"}
                self.result = {"status": "error", "broker": "fs.move_mount", "error": "boom"}

        with patch("main.BSSCController.execute_function_artifact", return_value=_PatchedNestedResult()):
            result = execute_workstation_capability(
                session,
                "ws.skill.invoke",
                {
                    "skill_title": "Python Commands 02 — Read Text File",
                    "mount": "main",
                    "relative_path": "README.md",
                },
            )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["parsed_output"]["status"], "error")
        slack_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={"token": "required input value", "channel": "required input value", "text": "required input value"},
            prompt="Send the Slack message `deploy complete` to channel `C12345678`.",
            skill_title="SDK User Commands 07 — Slack Send Message",
        )
        self.assertEqual(
            slack_payload,
            {"token": "xoxb-fake-slack-token", "channel": "C12345678", "text": "deploy complete"},
        )
        supabase_payload = derive_workstation_invocation_payload_from_prompt(
            inputs={
                "supabase_url": "required input value",
                "supabase_key": "required input value",
                "table": "required input value",
            },
            prompt="Select rows from Supabase table `profiles`.",
            skill_title="SDK User Commands 12 — Supabase Select Rows",
        )
        self.assertEqual(
            supabase_payload,
            {
                "supabase_url": "https://demo.supabase.local",
                "supabase_key": "fake-supabase-key",
                "table": "profiles",
            },
        )

    def test_materialize_common_trial_host_fixtures_creates_expected_tmp_inputs(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation validation across the trial corpus, helps with verifying that the validator-owned host fixtures for zip extraction, SDK uploads, and bash chmod prompts are created predictably.

        Reference to Theory:
            Verifies the workstation trial harness owns its incidental host prerequisites instead of depending on ambient `/tmp` state.

        Example Input Output:
            Input: `test_materialize_common_trial_host_fixtures_creates_expected_tmp_inputs()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        _materialize_common_trial_host_fixtures()
        self.assertTrue(Path("/tmp/example.zip").exists())
        self.assertTrue(Path("/tmp/report.txt").exists())
        self.assertTrue(Path("/tmp/demo.sh").exists())

    def test_shell_cross_boundary_preserves_system_path_when_payload_uses_path_key(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation invocation of shell-backed workers, helps with verifying that a worker input named `path` does not overwrite the shell runtime PATH and break basic commands.

        Reference to Theory:
            Verifies the workstation/worker boundary preserves a usable host toolchain while still exposing structured worker inputs into the child shell environment.

        Example Input Output:
            Input: `test_shell_cross_boundary_preserves_system_path_when_payload_uses_path_key()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        target = Path(self.tempdir.name) / "shell-path-fixture"
        result = _shell_cross_boundary(
            shell_script='mkdir -p "$path" && printf "%s" "$path"',
            stdin_payload={"path": str(target)},
        )
        self.assertTrue(result.ok, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), str(target))
        self.assertTrue(target.exists())

    def test_cli_handler_covers_workstation_trial_validate(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation CLI regression testing, helps with verifying that the workstation trial-validation command routes into the workstation audit layer and emits its JSON report.

        Reference to Theory:
            Verifies the workstation entry surface while keeping trial-audit orchestration inside the workstation package.

        Example Input Output:
            Input: `test_cli_handler_covers_workstation_trial_validate()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        args = parse_args(
            [
                "workstation-trial-validate",
                "--domains",
                "symbolsearch",
                "--workspace",
                str(self.workspace),
                "--report-root",
                str(self.root / "trial_report"),
            ]
        )
        with patch(
            "workstation.cli.validate_workstation_trial_domains",
            return_value={"status": "ok", "domains": [{"domain": "symbolsearch", "status": "ok"}]},
        ):
            with redirect_stdout(io.StringIO()) as buffer:
                exit_code = handle_workstation_trial_validate_command(args)
        self.assertEqual(exit_code, 0)
        self.assertIn("\"symbolsearch\"", buffer.getvalue())

    def test_run_workstation_chat_loop_handles_turn_and_exit(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation REPL regression testing, helps with verifying that the chat loop can drive one prompt through the session and then exit cleanly.

        Reference to Theory:
            Verifies the host-owned REPL model for workstation sessions without introducing an ambient shell inside the workstation.

        Example Input Output:
            Input: `test_run_workstation_chat_loop_handles_turn_and_exit()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            allowed_capabilities=(*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"),
            initial_task="Inspect the project.",
        )
        input_stream = io.StringIO("Inspect the workspace.\n/exit\n")
        output_stream = io.StringIO()
        with patch("workstation.llm_driver.build_workstation_openai_client", return_value=_FakeClient()):
            exit_code = run_workstation_chat_loop(
                root=self.root,
                model=None,
                max_tool_rounds=8,
                input_stream=input_stream,
                output_stream=output_stream,
            )
        self.assertEqual(exit_code, 0)
        rendered = output_stream.getvalue()
        self.assertIn("Workstation chat started.", rendered)
        self.assertIn("I inspected the workspace", rendered)
        self.assertIn("Session ended.", rendered)

    def test_run_workstation_chat_loop_renders_help_and_then_exits(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation REPL regression testing, helps with verifying that `/help` is handled at the chat shell layer and prints the shared workstation usage surface before normal exit.

        Reference to Theory:
            Verifies the help surface belongs to the host-owned chat shell rather than the underlying workstation runtime.

        Example Input Output:
            Input: `test_run_workstation_chat_loop_renders_help_and_then_exits()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(root_path=self.root, workspace_path=self.workspace, initial_task="Inspect the project.")
        input_stream = io.StringIO("/help\n/exit\n")
        output_stream = io.StringIO()
        exit_code = run_workstation_chat_loop(
            root=self.root,
            model=None,
            max_tool_rounds=8,
            input_stream=input_stream,
            output_stream=output_stream,
        )
        self.assertEqual(exit_code, 0)
        rendered = output_stream.getvalue()
        self.assertIn("Workstation chat commands", rendered)
        self.assertIn("workstation-launch", rendered)
        self.assertIn("Session ended.", rendered)

    def test_run_workstation_chat_loop_handles_skill_listing_slash_command(self) -> None:
        """
        High Level Purpose:
            In circumstances like non-interactive workstation chat fallback usage, helps with verifying that direct slash commands run through the host-owned chat shell instead of being sent to the LLM.

        Reference to Theory:
            Verifies chat-native workstation utilities remain available on the plain fallback loop, not only on the enhanced terminal frontend.

        Example Input Output:
            Input: `test_run_workstation_chat_loop_handles_skill_listing_slash_command()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(root_path=self.root, workspace_path=self.workspace, initial_task="Inspect the project.")
        input_stream = io.StringIO("/list-skills\n/exit\n")
        output_stream = io.StringIO()
        exit_code = run_workstation_chat_loop(
            root=self.root,
            model=None,
            max_tool_rounds=2,
            input_stream=input_stream,
            output_stream=output_stream,
        )
        self.assertEqual(exit_code, 0)
        rendered = output_stream.getvalue()
        self.assertIn("Built-in skills", rendered)
        self.assertIn("Workstation Greeting From Wasm", rendered)
        self.assertIn("Workstation Repo Search", rendered)
        self.assertIn("Session ended.", rendered)

    def test_run_workstation_chat_loop_survives_keyboard_interrupt(self) -> None:
        """
        High Level Purpose:
            In circumstances like interactive workstation shell use, helps with verifying that Ctrl+C interrupts only the active input read instead of terminating the whole shell.

        Reference to Theory:
            Verifies the host-owned chat surface behaves like a resilient shell boundary rather than exiting on every local input interruption.

        Example Input Output:
            Input: `test_run_workstation_chat_loop_survives_keyboard_interrupt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(root_path=self.root, workspace_path=self.workspace, initial_task="Inspect the project.")
        input_stream = _InterruptingInputStream([KeyboardInterrupt(), "/exit\n"])
        output_stream = io.StringIO()
        exit_code = run_workstation_chat_loop(
            root=self.root,
            model=None,
            max_tool_rounds=8,
            input_stream=input_stream,
            output_stream=output_stream,
        )
        self.assertEqual(exit_code, 0)
        rendered = output_stream.getvalue()
        self.assertIn("Input interrupted. Type /exit to quit.", rendered)
        self.assertIn("Session ended.", rendered)

    def test_run_workstation_chat_loop_prompts_for_escalation(self) -> None:
        """
        High Level Purpose:
            In circumstances like interactive workstation escalation testing, helps with verifying that the host-owned REPL prompts the user for one-invocation delegated-rights approval and continues the skill call after approval.

        Reference to Theory:
            Verifies escalation remains a workstation-shell decision instead of a skill-local decision.

        Example Input Output:
            Input: `test_run_workstation_chat_loop_prompts_for_escalation()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Use installed skills when appropriate.",
        )
        input_stream = io.StringIO("Use the installed skill.\nyes\n/exit\n")
        output_stream = io.StringIO()
        with patch("workstation.llm_driver.build_workstation_openai_client", return_value=_FakeEscalationSkillClient()):
            exit_code = run_workstation_chat_loop(
                root=self.root,
                model=None,
                max_tool_rounds=8,
                input_stream=input_stream,
                output_stream=output_stream,
            )
        self.assertEqual(exit_code, 0)
        rendered = output_stream.getvalue()
        self.assertIn("Escalation requested:", rendered)
        self.assertIn("The skill completed after approval.", rendered)
        self.assertIn("Session ended.", rendered)

    def test_prompt_for_workstation_escalation_survives_keyboard_interrupt(self) -> None:
        """
        High Level Purpose:
            In circumstances like interactive workstation approval prompts, helps with verifying that Ctrl+C cancels the escalation request without terminating the surrounding shell.

        Reference to Theory:
            Verifies escalation remains a host-owned prompt boundary and treats local interruption as denial rather than shell exit.

        Example Input Output:
            Input: `test_prompt_for_workstation_escalation_survives_keyboard_interrupt()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        output_stream = io.StringIO()
        decision = _prompt_for_workstation_escalation(
            request=WorkstationDelegationEscalationRequest(
                capability="ws.skill.invoke",
                target="skills",
                skill_title="Demo Skill",
                requested_delegation=({"capability": "ws.fs.write", "target": "main"},),
                rationale="Need to write one file.",
            ),
            input_stream=_InterruptingInputStream([KeyboardInterrupt()]),
            output_stream=output_stream,
        )
        self.assertFalse(decision.approved)
        self.assertIn("Escalation canceled.", output_stream.getvalue())

    def test_cli_handler_covers_workstation_chat(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation CLI regression testing, helps with verifying that the `workstation-chat` command routes into the host-owned chat loop correctly.

        Reference to Theory:
            Verifies the workstation entry surface while keeping interactive chat outside the workstation boundary.

        Example Input Output:
            Input: `test_cli_handler_covers_workstation_chat()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        launch_argv = ["workstation-launch", "--root", str(self.root), "--workspace", str(self.workspace), "--task", "Inspect the project."]
        for capability in (*DEFAULT_WORKSTATION_CAPABILITIES, "ws.repo.tree"):
            launch_argv.extend(["--capability", capability])
        launch_args = parse_args(launch_argv)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(handle_workstation_launch_command(launch_args), 0)
        chat_args = parse_args(["workstation-chat", "--root", str(self.root)])
        fake_stdin = io.StringIO("Inspect the workspace.\n/quit\n")
        fake_stdout = io.StringIO()
        with patch("sys.stdin", fake_stdin), patch("sys.stdout", fake_stdout):
            with patch("workstation.llm_driver.build_workstation_openai_client", return_value=_FakeClient()):
                exit_code = handle_workstation_chat_command(chat_args)
        self.assertEqual(exit_code, 0)
        rendered = fake_stdout.getvalue()
        self.assertIn("workstation>", rendered)
        self.assertIn("Session ended.", rendered)
