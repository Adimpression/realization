# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import host_brokers
from host_abi import host_abi_version, wasm_skill_abi_version
from host_brokers import invoke_host_broker
from main import (
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    BSSCController,
    LearningRelation,
    SystemState,
    build_artifact_store,
    load_artifact_yaml_documents,
)
from skill_schema_io import artifact_from_skill_document
from virtual_mounts import default_virtual_mount_table
from workstation.foundation.host.host_interaction import workstation_host_interaction_context
from workstation.runtime.core.session import launch_workstation_session, load_workstation_session


def wasm_single_hostcall_module_text(request: dict[str, object]) -> str:
    def _wat_bytes(text: str) -> str:
        return "".join(f"\\{byte:02x}" for byte in text.encode("utf-8"))

    request_text = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return f"""
(module
  (import "bssc" "hostcall" (func $hostcall (param i32 i32) (result i32)))
  (import "bssc" "read_hostcall_response" (func $read_hostcall_response (param i32) (result i32)))
  (import "bssc" "write_output" (func $write_output (param i32 i32) (result i32)))
  (memory (export "memory") 1)
  (data (i32.const 0) "{_wat_bytes(request_text)}")
  (func (export "run") (result i32)
    (local $response_len i32)
    (local.set $response_len (call $hostcall (i32.const 0) (i32.const {len(request_text.encode("utf-8"))})))
    (drop (call $read_hostcall_response (i32.const 512)))
    (drop (call $write_output (i32.const 512) (local.get $response_len)))
    (i32.const 0))
)
    """.strip()


def wasm_skill_state_roundtrip_module_text() -> str:
    def _wat_bytes(text: str) -> str:
        return "".join(f"\\{byte:02x}" for byte in text.encode("utf-8"))

    put_request = json.dumps(
        {
            "broker_name": "store.skill_state",
            "arguments": {"operation": "put", "key": "greeting", "value": "hi"},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    get_request = json.dumps(
        {
            "broker_name": "store.skill_state",
            "arguments": {"operation": "get", "key": "greeting"},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"""
(module
  (import "bssc" "hostcall" (func $hostcall (param i32 i32) (result i32)))
  (import "bssc" "read_hostcall_response" (func $read_hostcall_response (param i32) (result i32)))
  (import "bssc" "write_output" (func $write_output (param i32 i32) (result i32)))
  (memory (export "memory") 1)
  (data (i32.const 0) "{_wat_bytes(put_request)}")
  (data (i32.const 256) "{_wat_bytes(get_request)}")
  (func (export "run") (result i32)
    (local $response_len i32)
    (drop (call $hostcall (i32.const 0) (i32.const {len(put_request.encode("utf-8"))})))
    (local.set $response_len (call $hostcall (i32.const 256) (i32.const {len(get_request.encode("utf-8"))})))
    (drop (call $read_hostcall_response (i32.const 512)))
    (drop (call $write_output (i32.const 512) (local.get $response_len)))
    (i32.const 0))
)
    """.strip()


class HostMediationTests(unittest.TestCase):
    def setUp(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing for mediated host brokers, helps with preparing one isolated SQLite path and temporary workspace for each test.

        Reference to Theory:
            Verifies the first brokerization step toward the bundle target while keeping filesystem and store effects confined to a temporary boundary.

        Example Input Output:
            Input: `setUp()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.tempdir = tempfile.TemporaryDirectory(prefix="host_mediation_")
        self.sqlite_path = str(Path(self.tempdir.name) / "host_mediation.sqlite3")
        self.previous_sqlite_path = os.environ.get("STATE_SQLITE_PATH")
        os.environ["STATE_SQLITE_PATH"] = self.sqlite_path

    def tearDown(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing for mediated host brokers, helps with restoring the prior SQLite environment and removing the temporary workspace after each test.

        Reference to Theory:
            Verifies broker mediation without leaking temporary persistence or files across test cases.

        Example Input Output:
            Input: `tearDown()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self.previous_sqlite_path is None:
            os.environ.pop("STATE_SQLITE_PATH", None)
        else:
            os.environ["STATE_SQLITE_PATH"] = self.previous_sqlite_path
        self.tempdir.cleanup()

    def make_governed_broker_artifact(
        self,
        *,
        title: str,
        authority: str,
        approval_class: str = "automatic",
        admitted: bool = True,
    ) -> Artifact:
        """
        High Level Purpose:
            In circumstances like regression testing of mediated broker requests, helps with creating one governed v2 ability artifact whose declaration is narrow and explicit about the requested authority.

        Reference to Theory:
            Verifies that broker access depends on declared and admitted authority rather than broad implicit host access.

        Example Input Output:
            Input: `make_governed_broker_artifact(title='Write Text File', authority='write', approval_class='automatic', admitted=True)`
            Output: Artifact(id='artifact-write-text-file', title='Write Text File', artifact_type='ability', representation='python_script')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title: Value for `title` used by `make_governed_broker_artifact`. Expected type: `str`.
            authority: Value for `authority` used by `make_governed_broker_artifact`. Expected type: `str`.
            approval_class: Value for `approval_class` used by `make_governed_broker_artifact`. Expected type: `str`. Defaults to `'automatic'`.
            admitted: Value for `admitted` used by `make_governed_broker_artifact`. Expected type: `bool`. Defaults to `True`.

        Returns:
            Artifact: Result produced by `make_governed_broker_artifact`.
        """
        status = "admitted" if admitted else "held"
        requested_authorities = ["execute"]
        if authority != "execute":
            requested_authorities.append(authority)
        authority_bounds = {
            "execute": {
                "scope": "local_executor",
                "target": "python3_skill_runtime",
                "context": "explicit_user_prompt",
                "duration": "single_invocation",
                "triggering_conditions": ["user invokes skill"],
                "approval_class": approval_class,
            }
        }
        if authority != "execute":
            authority_bounds[authority] = {
                "scope": "local_host",
                "target": title.lower().replace(" ", "_"),
                "context": "explicit_user_prompt",
                "duration": "single_invocation",
                "triggering_conditions": ["user invokes skill"],
                "approval_class": approval_class,
            }
        return Artifact(
            id=f"artifact-{title.lower().replace(' ', '-')}",
            artifact_type=ArtifactType.ABILITY,
            title=title,
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope=f"brokered host action for {title}",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            template_schema={},
            content={
                "skill_schema": "bssc_skill.v2",
                "skill_kind": "ability",
                "skill_declaration": {
                    "intent": f"Perform {title.lower()} through the mediated host broker.",
                    "inputs": {"path": "target path"},
                    "outputs": {"status": "broker status"},
                    "authorities_requested": requested_authorities,
                    "authority_bounds": authority_bounds,
                    "data_classes_touched": ["public"],
                    "side_effects": ["python runtime execution", f"{authority} via broker"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": [approval_class],
                    "risk_tier": "tier1_bounded_transform",
                },
                "skill_admission": {
                    "status": status,
                    "admitted": admitted,
                    "rationale": "" if admitted else "Skill is held and cannot use host brokers.",
                    "policy_titles": ["Local Admission Policy"] if admitted else [],
                    "required_approval_class": approval_class,
                    "evaluated_at": "2026-03-31T00:00:00Z",
                },
            },
            justification="Test governed host broker access.",
            constraints=["use only through mediated broker execution"],
        )

    def test_mediated_host_broker_can_write_and_read_text(self) -> None:
        """
        High Level Purpose:
            In circumstances like advancing from executor mediation toward named host brokers, helps with proving that read and write filesystem broker requests are both governed and operational.

        Reference to Theory:
            Verifies the brokerization step of the bundle plan by replacing raw filesystem effects with explicit broker requests under declaration-derived grants.

        Example Input Output:
            Input: `test_mediated_host_broker_can_write_and_read_text()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("write and read text")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "demo.txt"

        write_result = controller.execute_mediated_host_broker_request(
            self.make_governed_broker_artifact(title="Write Text File", authority="write"),
            broker_name="fs.write_text",
            broker_arguments={"path": str(target), "text": "hello"},
            semantic_unit="Write hello to a file.",
        )
        self.assertEqual(write_result["status"], "ok")
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), "hello")

        read_result = controller.execute_mediated_host_broker_request(
            self.make_governed_broker_artifact(title="Read Text File", authority="read"),
            broker_name="fs.read_text",
            broker_arguments={"path": str(target)},
            semantic_unit="Read hello from a file.",
        )
        self.assertEqual(read_result["status"], "ok")
        self.assertEqual(read_result["text"], "hello")
        self.assertEqual(len(state.capability_grants), 4)
        self.assertEqual(
            [grant["authority"] for grant in state.capability_grants],
            ["execute", "write", "execute", "read"],
        )
        self.assertEqual(len(state.effect_traces), 2)
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "fs.write_text")
        self.assertEqual(state.effect_traces[1]["request"]["effect_kind"], "fs.read_text")
        receipts = state.effect_traces[0].get("receipts", {})
        self.assertEqual(
            sorted(receipts),
            ["approval", "declaration", "grants", "lifecycle", "policy", "request"],
        )
        self.assertTrue(all(str(item.get("digest", "")).strip() for item in receipts.values()))

    def test_mediated_host_broker_can_query_sqlite(self) -> None:
        """
        High Level Purpose:
            In circumstances like brokerizing host persistence access, helps with proving that a bounded SQLite read can pass through the mediated store broker and return structured rows.

        Reference to Theory:
            Verifies that store access can become a named brokered effect rather than a direct library call inside skills.

        Example Input Output:
            Input: `test_mediated_host_broker_can_query_sqlite()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        db_path = Path(self.tempdir.name) / "query.sqlite3"
        connection = sqlite3.connect(str(db_path))
        try:
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE demo(value INTEGER)")
            cursor.execute("INSERT INTO demo(value) VALUES (7)")
            connection.commit()
        finally:
            connection.close()

        state = SystemState.bootstrap("query sqlite")
        controller = BSSCController(state, llm_policy="off")
        result = controller.execute_mediated_host_broker_request(
            self.make_governed_broker_artifact(title="Query SQLite Store", authority="read"),
            broker_name="store.sqlite_query",
            broker_arguments={
                "sqlite_path": str(db_path),
                "query": "SELECT value FROM demo",
                "parameters": [],
            },
            semantic_unit="Read a value from sqlite.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["value"], 7)
        self.assertEqual(len(state.effect_traces), 1)
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "store.sqlite_query")

    def test_mediated_host_broker_uses_workstation_attachment_mounts(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-interaction rollout, helps with proving that brokered runtime filesystem access can inherit workstation-backed attachment mounts without any artifact-local virtual mount declaration.

        Reference to Theory:
            Verifies the six-layer shared-substrate rule by ensuring the governed runtime consumes a real shared host-interaction seam for child worker filesystem scope instead of falling back to ambient cwd.

        Example Input Output:
            Input: `test_mediated_host_broker_uses_workstation_attachment_mounts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        workstation_root = Path(self.tempdir.name) / "ws"
        workspace_root = Path(self.tempdir.name) / "workspace"
        workspace_root.mkdir()
        (workspace_root / "mounted_note.txt").write_text("hello from workstation mount")
        launch_workstation_session(
            root_path=workstation_root,
            workspace_path=workspace_root,
            initial_task="Inspect the workspace.",
        )
        session = load_workstation_session(workstation_root)

        state = SystemState.bootstrap("read mounted workstation file")
        controller = BSSCController(
            state,
            llm_policy="off",
            host_interaction_context=workstation_host_interaction_context(session),
        )
        result = controller.execute_mediated_host_broker_request(
            self.make_governed_broker_artifact(title="Read Mounted Workstation File", authority="read"),
            broker_name="fs.read_mount",
            broker_arguments={"mount": "skill_input", "relative_path": "mounted_note.txt"},
            semantic_unit="Read the mounted workstation file.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["text"], "hello from workstation mount")
        self.assertEqual(len(state.effect_traces), 1)
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "fs.read_mount")

    def test_wasm_skill_can_use_governed_store_hostcall_subset(self) -> None:
        state = SystemState.bootstrap("wasm skill state roundtrip")
        state.controller_features.supported_executors = ["python3", "wasm_wasi"]
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-wasm-skill-state",
            artifact_type=ArtifactType.ABILITY,
            title="Wasm Skill State Roundtrip",
            representation=ArtifactRepresentation.WASM_MODULE,
            function_bit=1,
            scope="brokered wasm roundtrip for governed skill state",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            template_schema={},
            content={
                "entrypoint": "run",
                "executor_framework": "wasm_wasi",
                "script_language": "wasm",
                "output_contract": {"value": "stored skill-state value"},
                "wasm_module": wasm_skill_state_roundtrip_module_text(),
                "wasm_abi_version": wasm_skill_abi_version(),
                "wasm_format": "wat",
                "host_abi_version": host_abi_version(),
                "governed_host_brokers": ["store.skill_state"],
                "governed_authorities": ["execute", "persist"],
                "skill_schema": "bssc_skill.v2",
                "skill_declaration": {
                    "intent": "Round-trip governed skill state through a Wasm hostcall.",
                    "inputs": {},
                    "outputs": {"value": "stored skill-state value"},
                    "authorities_requested": ["execute", "persist"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "wasm_wasi_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "persist": {
                            "scope": "local_host",
                            "target": "skill_state_namespace",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["derived"],
                    "side_effects": ["wasm runtime execution", "persist skill state via broker"],
                    "persistence_behavior": "skill_state_only",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                    "executor_framework": "wasm_wasi",
                },
                "skill_admission": {
                    "status": "admitted",
                    "admitted": True,
                    "rationale": "",
                    "policy_titles": ["Local Admission Policy"],
                    "required_approval_class": "automatic",
                    "evaluated_at": "2026-04-02T00:00:00Z",
                },
            },
            justification="Test governed Wasm hostcalls through the stable store subset.",
            constraints=["use only through mediated wasm execution"],
        )

        result = controller.execute_function_artifact(
            artifact,
            semantic_unit="Round-trip governed skill state from wasm.",
            explicit_payload={},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.exit_code, 0)
        self.assertIsInstance(result.result, dict)
        self.assertEqual(result.result.get("status"), "ok")
        self.assertEqual(result.result.get("operation"), "get")
        self.assertTrue(result.result.get("found"))
        self.assertEqual(result.result.get("value"), "hi")
        self.assertGreaterEqual(len(state.effect_traces), 3)
        self.assertEqual(state.effect_traces[-1]["request"]["effect_kind"], "execute.wasm_wasi")
        wasm_broker_traces = [
            trace for trace in state.effect_traces
            if isinstance(trace, dict) and trace.get("kind") == "wasm_skill_broker"
        ]
        self.assertEqual(len(wasm_broker_traces), 2)
        self.assertTrue(all(trace.get("allowed") for trace in wasm_broker_traces))
        self.assertEqual(
            [trace.get("effect_kind") for trace in wasm_broker_traces],
            ["store.skill_state", "store.skill_state"],
        )

    def test_wasm_skill_can_invoke_governed_skill_through_hostcall_and_ingest_nested_trace(self) -> None:
        state = SystemState.bootstrap("wasm governed skill invoke")
        state.controller_features.supported_executors = ["python3", "wasm_wasi"]
        controller = BSSCController(state, llm_policy="off")
        store = build_artifact_store()
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "boundary_shape_artifacts"
            / "hi_responder.yaml"
        )
        nested_skill = load_artifact_yaml_documents(fixture_path)[0]
        store.persist_artifact(nested_skill, run_id="test_wasm_skill_invoke")
        artifact = Artifact(
            id="artifact-wasm-skill-invoke",
            artifact_type=ArtifactType.ABILITY,
            title="Wasm Skill Invoke Nested Skill",
            representation=ArtifactRepresentation.WASM_MODULE,
            function_bit=1,
            scope="brokered wasm invoke of another governed skill",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            template_schema={},
            content={
                "entrypoint": "run",
                "executor_framework": "wasm_wasi",
                "script_language": "wasm",
                "output_contract": {"answer": "nested skill answer"},
                "wasm_module": wasm_single_hostcall_module_text(
                    {
                        "broker_name": "skill.invoke",
                        "arguments": {"skill_title": "Hi Responder", "semantic_unit": "Say hi."},
                    }
                ),
                "wasm_abi_version": wasm_skill_abi_version(),
                "wasm_format": "wat",
                "host_abi_version": host_abi_version(),
                "governed_host_brokers": ["skill.invoke"],
                "governed_authorities": ["execute", "invoke"],
                "skill_schema": "bssc_skill.v2",
                "skill_declaration": {
                    "intent": "Invoke a governed nested skill through a Wasm hostcall.",
                    "inputs": {},
                    "outputs": {"answer": "nested skill answer"},
                    "authorities_requested": ["execute", "invoke"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "wasm_wasi_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "invoke": {
                            "scope": "local_host",
                            "target": "Hi Responder",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["wasm runtime execution", "invoke a governed nested skill"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": ["skill:Hi Responder"],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                    "executor_framework": "wasm_wasi",
                },
                "skill_admission": {
                    "status": "admitted",
                    "admitted": True,
                    "rationale": "",
                    "policy_titles": ["Local Admission Policy"],
                    "required_approval_class": "automatic",
                    "evaluated_at": "2026-04-02T00:00:00Z",
                },
            },
            justification="Test governed Wasm skill.invoke hostcalls and nested trace ingestion.",
            constraints=["use only through mediated wasm execution"],
        )

        result = controller.execute_function_artifact(
            artifact,
            semantic_unit="Invoke the hi responder skill from wasm.",
            explicit_payload={},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.exit_code, 0)
        self.assertIsInstance(result.result, dict)
        self.assertEqual(result.result.get("status"), "ok")
        self.assertEqual(result.result.get("skill_title"), "Hi Responder")
        self.assertEqual(result.result.get("answer"), "hi")
        wasm_broker_traces = [
            trace for trace in state.effect_traces
            if isinstance(trace, dict) and trace.get("kind") == "wasm_skill_broker"
        ]
        self.assertEqual(len(wasm_broker_traces), 1)
        self.assertEqual(wasm_broker_traces[0]["effect_kind"], "skill.invoke")
        self.assertTrue(wasm_broker_traces[0]["allowed"])
        effect_kinds = [
            trace.get("request", {}).get("effect_kind", "")
            for trace in state.effect_traces
            if isinstance(trace, dict) and isinstance(trace.get("request"), dict)
        ]
        self.assertIn("execute.python3", effect_kinds)
        self.assertIn("execute.wasm_wasi", effect_kinds)
        self.assertGreaterEqual(len(state.capability_grants), 3)

    def test_wasm_skill_can_invoke_named_tool_through_hostcall(self) -> None:
        state = SystemState.bootstrap("wasm named tool invoke")
        state.controller_features.supported_executors = ["wasm_wasi"]
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-wasm-tool-invoke",
            artifact_type=ArtifactType.ABILITY,
            title="Wasm Invoke Open Browser Tool",
            representation=ArtifactRepresentation.WASM_MODULE,
            function_bit=1,
            scope="brokered wasm invoke of a named host tool",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            template_schema={},
            content={
                "entrypoint": "run",
                "executor_framework": "wasm_wasi",
                "script_language": "wasm",
                "output_contract": {"status": "tool invocation status", "url": "opened url"},
                "wasm_module": wasm_single_hostcall_module_text(
                    {
                        "broker_name": "tool.invoke",
                        "arguments": {
                            "tool_name": "open_browser",
                            "arguments": {"url": "https://example.com"},
                        },
                    }
                ),
                "wasm_abi_version": wasm_skill_abi_version(),
                "wasm_format": "wat",
                "host_abi_version": host_abi_version(),
                "governed_host_brokers": ["tool.invoke"],
                "governed_authorities": ["execute"],
                "skill_schema": "bssc_skill.v2",
                "skill_declaration": {
                    "intent": "Invoke a named host tool through a Wasm hostcall.",
                    "inputs": {},
                    "outputs": {"status": "tool invocation status", "url": "opened url"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "wasm_wasi_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["wasm runtime execution", "invoke a named host tool"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                    "executor_framework": "wasm_wasi",
                },
                "skill_admission": {
                    "status": "admitted",
                    "admitted": True,
                    "rationale": "",
                    "policy_titles": ["Local Admission Policy"],
                    "required_approval_class": "automatic",
                    "evaluated_at": "2026-04-02T00:00:00Z",
                },
            },
            justification="Test governed Wasm tool.invoke hostcalls.",
            constraints=["use only through mediated wasm execution"],
        )

        with patch.dict(
            host_brokers.HOST_BROKER_REGISTRY,
            {"macos.open_browser": lambda **kwargs: {"status": "ok", "url": kwargs.get("url", "")}},
            clear=False,
        ):
            result = controller.execute_function_artifact(
                artifact,
                semantic_unit="Open the example site from wasm via a named tool.",
                explicit_payload={},
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.exit_code, 0)
        self.assertIsInstance(result.result, dict)
        self.assertEqual(result.result.get("status"), "ok")
        self.assertEqual(result.result.get("tool_name"), "open_browser")
        self.assertEqual(result.result.get("broker"), "macos.open_browser")
        self.assertEqual(result.result.get("url"), "https://example.com")
        wasm_broker_traces = [
            trace for trace in state.effect_traces
            if isinstance(trace, dict) and trace.get("kind") == "wasm_skill_broker"
        ]
        self.assertEqual(len(wasm_broker_traces), 1)
        self.assertEqual(wasm_broker_traces[0]["effect_kind"], "tool.invoke")
        self.assertTrue(wasm_broker_traces[0]["allowed"])
        effect_kinds = [
            trace.get("request", {}).get("effect_kind", "")
            for trace in state.effect_traces
            if isinstance(trace, dict) and isinstance(trace.get("request"), dict)
        ]
        self.assertIn("execute.wasm_wasi", effect_kinds)

    def test_virtual_mount_write_and_read_use_named_mount_surface(self) -> None:
        """
        High Level Purpose:
            In circumstances like moving governed file access away from raw paths, helps with proving that mounted file reads and writes operate through named virtual mounts.

        Reference to Theory:
            Verifies the data-governance step of the bundle plan by replacing path freedom with mount-relative reads and writes.

        Example Input Output:
            Input: `test_virtual_mount_write_and_read_use_named_mount_surface()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        mount_root = Path(self.tempdir.name) / "mount_root"
        state = SystemState.bootstrap("virtual mount read write")
        controller = BSSCController(state, llm_policy="off")

        writer = self.make_governed_broker_artifact(title="Write Mounted File", authority="write")
        writer.content["virtual_mounts"] = {
            "skill_output": {
                "root": str(mount_root),
                "permissions": ["read", "write", "list"],
                "data_class": "public",
            }
        }
        write_result = controller.execute_mediated_host_broker_request(
            writer,
            broker_name="fs.write_mount",
            broker_arguments={
                "mount": "skill_output",
                "relative_path": "results/demo.txt",
                "text": "hello",
            },
            semantic_unit="Write hello through a virtual mount.",
        )

        self.assertEqual(write_result["status"], "ok")
        self.assertTrue((mount_root / "results" / "demo.txt").exists())
        self.assertEqual((mount_root / "results" / "demo.txt").read_text(), "hello")

        reader = self.make_governed_broker_artifact(title="Read Mounted File", authority="read")
        reader.content["virtual_mounts"] = dict(writer.content["virtual_mounts"])
        read_result = controller.execute_mediated_host_broker_request(
            reader,
            broker_name="fs.read_mount",
            broker_arguments={
                "mount": "skill_output",
                "relative_path": "results/demo.txt",
            },
            semantic_unit="Read hello through a virtual mount.",
        )

        self.assertEqual(read_result["status"], "ok")
        self.assertEqual(read_result["text"], "hello")
        self.assertEqual(read_result["mount"], "skill_output")
        self.assertEqual(len(state.effect_traces), 2)
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "fs.write_mount")
        self.assertEqual(state.effect_traces[1]["request"]["effect_kind"], "fs.read_mount")

    def test_virtual_mount_list_uses_named_mount_surface(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed directory inspection through virtual mounts, helps with proving that directory listing can occur without falling back to a raw host path.

        Reference to Theory:
            Verifies the mount-oriented data surface needed by authored Python skills that should prefer named mounts over raw path parameters.

        Example Input Output:
            Input: `test_virtual_mount_list_uses_named_mount_surface()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        mount_root = Path(self.tempdir.name) / "list_mount_root"
        (mount_root / "nested").mkdir(parents=True, exist_ok=True)
        (mount_root / "nested" / "alpha.txt").write_text("a")
        (mount_root / "nested" / "beta.txt").write_text("b")

        state = SystemState.bootstrap("virtual mount list")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="List Mounted Directory", authority="read")
        artifact.content["virtual_mounts"] = {
            "skill_input": {
                "root": str(mount_root),
                "permissions": ["read", "list"],
                "data_class": "public",
            }
        }

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.list_mount",
            broker_arguments={"mount": "skill_input", "relative_path": "nested"},
            semantic_unit="List a governed mounted directory.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mount"], "skill_input")
        self.assertEqual(result["entries"], ["alpha.txt", "beta.txt"])
        self.assertEqual(len(state.effect_traces), 1)
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "fs.list_mount")

    def test_virtual_mount_find_uses_named_mount_surface(self) -> None:
        mount_root = Path(self.tempdir.name) / "find_mount_root"
        (mount_root / "trials" / "nested").mkdir(parents=True, exist_ok=True)
        (mount_root / "trials" / "README.md").write_text("root readme")
        (mount_root / "trials" / "nested" / "notes.md").write_text("nested notes")
        (mount_root / "trials" / "nested" / "skip.txt").write_text("ignore")

        state = SystemState.bootstrap("virtual mount find")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="Find Mounted Files", authority="read")
        artifact.content["virtual_mounts"] = {
            "skill_input": {
                "root": str(mount_root),
                "permissions": ["read", "list"],
                "data_class": "public",
            }
        }

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.find_mount",
            broker_arguments={
                "mount": "skill_input",
                "relative_path": "trials",
                "suffix": ".md",
            },
            semantic_unit="Find markdown files in a governed mount.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mount"], "skill_input")
        self.assertEqual(result["suffix"], ".md")
        self.assertEqual(result["matches"], ["README.md", "nested/notes.md"])
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "fs.find_mount")

    def test_virtual_mount_copy_move_and_delete_use_named_mount_surfaces(self) -> None:
        source_root = Path(self.tempdir.name) / "copy_source_mount"
        tmp_root = Path(self.tempdir.name) / "copy_tmp_mount"
        output_root = Path(self.tempdir.name) / "copy_output_mount"
        (source_root / "docs").mkdir(parents=True, exist_ok=True)
        (source_root / "docs" / "readme.txt").write_text("hello copy move delete")

        state = SystemState.bootstrap("virtual mount copy move delete")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="Copy Move Delete Mounted File", authority="write")
        artifact.content["virtual_mounts"] = {
            "skill_input": {
                "root": str(source_root),
                "permissions": ["read", "list"],
                "data_class": "public",
            },
            "skill_tmp": {
                "root": str(tmp_root),
                "permissions": ["read", "write", "list"],
                "data_class": "derived",
            },
            "skill_output": {
                "root": str(output_root),
                "permissions": ["read", "write", "list"],
                "data_class": "public",
            },
        }
        artifact.content["skill_declaration"]["data_classes_touched"] = ["public", "derived"]

        copy_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.copy_mount",
            broker_arguments={
                "source_mount": "skill_input",
                "source_relative_path": "docs/readme.txt",
                "destination_mount": "skill_tmp",
                "destination_relative_path": "copied/readme.txt",
            },
            semantic_unit="Copy a mounted file.",
        )
        self.assertEqual(copy_result["status"], "ok")
        self.assertTrue((tmp_root / "copied" / "readme.txt").exists())

        move_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.move_mount",
            broker_arguments={
                "source_mount": "skill_tmp",
                "source_relative_path": "copied/readme.txt",
                "destination_mount": "skill_output",
                "destination_relative_path": "moved/readme.txt",
            },
            semantic_unit="Move a mounted file.",
        )
        self.assertEqual(move_result["status"], "ok")
        self.assertFalse((tmp_root / "copied" / "readme.txt").exists())
        self.assertTrue((output_root / "moved" / "readme.txt").exists())

        delete_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.delete_mount",
            broker_arguments={
                "mount": "skill_output",
                "relative_path": "moved/readme.txt",
            },
            semantic_unit="Delete a mounted file.",
        )
        self.assertEqual(delete_result["status"], "ok")
        self.assertFalse((output_root / "moved" / "readme.txt").exists())
        self.assertEqual(
            [trace["request"]["effect_kind"] for trace in state.effect_traces[-3:]],
            ["fs.copy_mount", "fs.move_mount", "fs.delete_mount"],
        )

    def test_virtual_mount_create_and_extract_zip_use_named_mount_surfaces(self) -> None:
        source_root = Path(self.tempdir.name) / "zip_source_mount"
        archive_root = Path(self.tempdir.name) / "zip_archive_mount"
        output_root = Path(self.tempdir.name) / "zip_output_mount"
        (source_root / "bundle").mkdir(parents=True, exist_ok=True)
        (source_root / "bundle" / "alpha.txt").write_text("alpha")
        (source_root / "bundle" / "beta.txt").write_text("beta")

        state = SystemState.bootstrap("virtual mount zip")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="Zip Mounted Directory", authority="write")
        artifact.content["virtual_mounts"] = {
            "skill_input": {
                "root": str(source_root),
                "permissions": ["read", "list"],
                "data_class": "public",
            },
            "skill_tmp": {
                "root": str(archive_root),
                "permissions": ["read", "write", "list"],
                "data_class": "derived",
            },
            "skill_output": {
                "root": str(output_root),
                "permissions": ["read", "write", "list"],
                "data_class": "public",
            },
        }
        artifact.content["skill_declaration"]["data_classes_touched"] = ["public", "derived"]

        create_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.create_zip_mount",
            broker_arguments={
                "source_mount": "skill_input",
                "source_relative_path": "bundle",
                "destination_mount": "skill_tmp",
                "destination_relative_path": "bundle.zip",
            },
            semantic_unit="Create a mounted zip archive.",
        )
        self.assertEqual(create_result["status"], "ok")
        self.assertTrue((archive_root / "bundle.zip").exists())

        extract_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.extract_zip_mount",
            broker_arguments={
                "source_mount": "skill_tmp",
                "source_relative_path": "bundle.zip",
                "destination_mount": "skill_output",
                "destination_relative_path": "bundle-unpacked",
            },
            semantic_unit="Extract a mounted zip archive.",
        )
        self.assertEqual(extract_result["status"], "ok")
        self.assertTrue((output_root / "bundle-unpacked" / "alpha.txt").exists())
        self.assertTrue((output_root / "bundle-unpacked" / "beta.txt").exists())
        self.assertEqual(
            [trace["request"]["effect_kind"] for trace in state.effect_traces[-2:]],
            ["fs.create_zip_mount", "fs.extract_zip_mount"],
        )

    def test_mediated_network_text_read_uses_named_host_surface(self) -> None:
        state = SystemState.bootstrap("network text read")
        controller = BSSCController(state, llm_policy="off")

        result = controller.execute_mediated_host_broker_request(
            self.make_governed_broker_artifact(title="Fetch Text Resource", authority="communicate"),
            broker_name="net.http_get_text",
            broker_arguments={"url": "data:text/plain,hello%20world"},
            semantic_unit="Fetch text through the governed network broker.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["text"], "hello world")
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "net.http_get_text")

    def test_virtual_mount_denies_undeclared_data_class(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed access to mounted files, helps with proving that mount data classes must be covered by the declared and granted data classes.

        Reference to Theory:
            Verifies the new data-governance boundary by denying a mount whose data class is outside the skill declaration.

        Example Input Output:
            Input: `test_virtual_mount_denies_undeclared_data_class()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        mount_root = Path(self.tempdir.name) / "secret_mount"
        mount_root.mkdir(parents=True, exist_ok=True)
        (mount_root / "secret.txt").write_text("nope")

        state = SystemState.bootstrap("virtual mount denied data class")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="Read Secret Mounted File", authority="read")
        artifact.content["virtual_mounts"] = {
            "user_selected": {
                "root": str(mount_root),
                "permissions": ["read", "list"],
                "data_class": "secret",
            }
        }
        artifact.content["skill_declaration"]["data_classes_touched"] = ["public"]

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.read_mount",
            broker_arguments={
                "mount": "user_selected",
                "relative_path": "secret.txt",
            },
            semantic_unit="Try to read secret data through a mount.",
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("requires data classes secret", result["error"])
        self.assertEqual(len(state.effect_traces), 1)
        self.assertFalse(state.effect_traces[0]["result"]["ok"])

    def test_named_query_uses_registered_query_and_data_class(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed store reads, helps with proving that SQLite access can occur through a registered named query instead of raw SQL.

        Reference to Theory:
            Verifies bundle-style named-query access by pairing a read authority with an internal data-class-bound query registry.

        Example Input Output:
            Input: `test_named_query_uses_registered_query_and_data_class()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection = sqlite3.connect(self.sqlite_path)
        try:
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE demo(value INTEGER)")
            cursor.execute("INSERT INTO demo(value) VALUES (7)")
            connection.commit()
        finally:
            connection.close()

        state = SystemState.bootstrap("named query")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="Named Query Reader", authority="read")
        artifact.content["skill_declaration"]["data_classes_touched"] = ["internal"]
        artifact.content["named_queries"] = {
            "demo_value": {
                "sql": "SELECT value FROM demo WHERE value = ?",
                "parameter_order": ["wanted"],
                "data_class": "internal",
            }
        }

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="store.named_query",
            broker_arguments={
                "query_name": "demo_value",
                "parameters": {"wanted": 7},
            },
            semantic_unit="Read demo value through a named query.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["value"], 7)
        self.assertEqual(result["data_class"], "internal")
        self.assertEqual(len(state.effect_traces), 1)
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "store.named_query")

    def test_skill_state_persists_namespaced_values(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed per-skill state, helps with proving that a skill can persist and reload namespaced JSON-safe state through the host-owned SQLite surface.

        Reference to Theory:
            Verifies bundle-style namespaced skill-local persistence instead of exposing arbitrary database handles to the skill.

        Example Input Output:
            Input: `test_skill_state_persists_namespaced_values()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("skill state")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="Persist Skill State", authority="persist")
        artifact.content["skill_declaration"]["data_classes_touched"] = ["derived"]

        put_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="store.skill_state",
            broker_arguments={
                "operation": "put",
                "key": "last_answer",
                "value": {"answer": 12},
            },
            semantic_unit="Persist a derived answer in namespaced skill state.",
        )
        self.assertEqual(put_result["status"], "ok")

        get_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="store.skill_state",
            broker_arguments={
                "operation": "get",
                "key": "last_answer",
            },
            semantic_unit="Reload derived answer from namespaced skill state.",
        )
        self.assertEqual(get_result["status"], "ok")
        self.assertTrue(get_result["found"])
        self.assertEqual(get_result["value"], {"answer": 12})
        self.assertEqual(get_result["data_class"], "derived")

        keys_result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="store.skill_state",
            broker_arguments={"operation": "list_keys"},
            semantic_unit="List persisted keys in namespaced skill state.",
        )
        self.assertEqual(keys_result["status"], "ok")
        self.assertEqual(keys_result["keys"], ["last_answer"])

    def test_denied_host_broker_request_emits_denial_trace(self) -> None:
        """
        High Level Purpose:
            In circumstances like held governed skills attempting to use host brokers, helps with proving that mediation records a denial trace instead of silently allowing the effect.

        Reference to Theory:
            Verifies policy-before-effect for the new broker surface just as it already exists for executor-backed skill execution.

        Example Input Output:
            Input: `test_denied_host_broker_request_emits_denial_trace()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("denied host broker")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "blocked.txt"

        result = controller.execute_mediated_host_broker_request(
            self.make_governed_broker_artifact(title="Blocked Write", authority="write", admitted=False),
            broker_name="fs.write_text",
            broker_arguments={"path": str(target), "text": "blocked"},
            semantic_unit="Try to write blocked text.",
        )

        self.assertEqual(result["status"], "error")
        self.assertFalse(target.exists())
        self.assertEqual(state.capability_grants, [])
        self.assertEqual(len(state.effect_traces), 1)
        self.assertFalse(state.effect_traces[0]["decision"]["allowed"])
        self.assertIn("held", state.effect_traces[0]["decision"]["rationale"].lower())

    def test_inactive_lifecycle_denies_host_broker_request(self) -> None:
        """
        High Level Purpose:
            In circumstances like admitted governed skills that were later deactivated, helps with proving that lifecycle activation blocks host broker use even when admission remains admitted.

        Reference to Theory:
            Verifies open governance section 9 by making activation a current invocation gate rather than an export-only metadata field.

        Example Input Output:
            Input: `test_inactive_lifecycle_denies_host_broker_request()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("inactive host broker")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "inactive.txt"
        artifact = self.make_governed_broker_artifact(title="Inactive Write", authority="write", admitted=True)
        artifact.content["skill_lifecycle"] = {
            "review_status": "pending_review",
            "admission_status": "admitted",
            "installation_status": "installed",
            "activation_status": "inactive",
            "trust_status": "trusted",
            "quarantine_status": "clear",
            "status_reason": "Temporarily disabled for maintenance.",
            "updated_at": "2026-03-31T12:00:00+00:00",
        }

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.write_text",
            broker_arguments={"path": str(target), "text": "blocked"},
            semantic_unit="Try to write blocked text from an inactive skill.",
        )

        self.assertEqual(result["status"], "error")
        self.assertFalse(target.exists())
        self.assertEqual(len(state.effect_traces), 1)
        self.assertFalse(state.effect_traces[0]["decision"]["allowed"])
        self.assertIn("activation status is inactive", state.effect_traces[0]["decision"]["rationale"].lower())

    def test_current_approval_revocation_denies_even_if_stored_admission_is_admitted(self) -> None:
        """
        High Level Purpose:
            In circumstances like approval records being revoked after a skill was previously admitted, helps with proving that invocation re-checks current approval state instead of trusting only the stored admission snapshot.

        Reference to Theory:
            Verifies activation-time approval re-evaluation by denying a broker effect when the current approval artifact is revoked even though the skill still carries an admitted import-time record.

        Example Input Output:
            Input: `test_current_approval_revocation_denies_even_if_stored_admission_is_admitted()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("approval revoked broker")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "revoked.txt"
        artifact = self.make_governed_broker_artifact(
            title="Approval Gated Write",
            authority="write",
            approval_class="operator_approved",
            admitted=True,
        )
        artifact.content["skill_declaration"]["risk_tier"] = "tier3_sensitive"
        artifact.content["skill_declaration"]["approval_requirements"] = ["operator_approved"]
        artifact.content["skill_admission"]["status"] = "admitted"
        artifact.content["skill_admission"]["admitted"] = True

        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Admission Policy",
                "policy": {
                    "intent": "Require operator approval for sensitive brokered writes.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "write"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {
                        "tier3_sensitive": "operator_approved",
                    },
                },
            }
        )
        revoked_approval = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "approval",
                "title": "Revoked Approval For Approval Gated Write",
                "approval": {
                    "intent": "Previously approved this write, but it is now revoked.",
                    "approval_class": "operator_approved",
                    "subject_titles": ["Approval Gated Write"],
                    "subject_kinds": ["ability"],
                    "approved_authorities": ["execute", "write"],
                    "approved_risk_tiers": ["tier3_sensitive"],
                    "issued_by": "operator://local-admin",
                    "rationale": "Approval revoked after review.",
                    "status": "revoked",
                },
            }
        )
        controller.artifact_store.load_all_artifacts = lambda: [policy_artifact, revoked_approval]  # type: ignore[method-assign]

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.write_text",
            broker_arguments={"path": str(target), "text": "blocked"},
            semantic_unit="Try to write with revoked approval.",
        )

        self.assertEqual(result["status"], "error")
        self.assertFalse(target.exists())
        self.assertEqual(len(state.effect_traces), 1)
        self.assertFalse(state.effect_traces[0]["decision"]["allowed"])
        self.assertIn("requires explicit approval class operator_approved", state.effect_traces[0]["decision"]["rationale"])
        self.assertEqual(state.effect_traces[0]["admission"]["status"], "held")

    def test_current_approval_grant_allows_even_if_stored_admission_is_held(self) -> None:
        """
        High Level Purpose:
            In circumstances like a skill receiving a later approval after initial import, helps with proving that invocation re-checks current approval state and can allow use without relying only on the stale held admission snapshot.

        Reference to Theory:
            Verifies activation-time approval re-evaluation by allowing a broker effect when current installed policy and approval now satisfy the governed requirement.

        Example Input Output:
            Input: `test_current_approval_grant_allows_even_if_stored_admission_is_held()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("approval granted broker")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "approved.txt"
        artifact = self.make_governed_broker_artifact(
            title="Later Approved Write",
            authority="write",
            approval_class="operator_approved",
            admitted=False,
        )
        artifact.content["skill_declaration"]["risk_tier"] = "tier3_sensitive"
        artifact.content["skill_declaration"]["approval_requirements"] = ["operator_approved"]
        artifact.content["skill_admission"]["status"] = "held"
        artifact.content["skill_admission"]["admitted"] = False
        artifact.content["skill_admission"]["rationale"] = "Policy requires explicit approval class operator_approved before admission."

        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Admission Policy",
                "policy": {
                    "intent": "Require operator approval for sensitive brokered writes.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "write"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {
                        "tier3_sensitive": "operator_approved",
                    },
                },
            }
        )
        current_approval = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "approval",
                "title": "Operator Approval For Later Approved Write",
                "approval": {
                    "intent": "Approve the named write skill.",
                    "approval_class": "operator_approved",
                    "subject_titles": ["Later Approved Write"],
                    "subject_kinds": ["ability"],
                    "approved_authorities": ["execute", "write"],
                    "approved_risk_tiers": ["tier3_sensitive"],
                    "issued_by": "operator://local-admin",
                    "rationale": "Operator approved the write.",
                    "status": "approved",
                },
            }
        )
        controller.artifact_store.load_all_artifacts = lambda: [policy_artifact, current_approval]  # type: ignore[method-assign]

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.write_text",
            broker_arguments={"path": str(target), "text": "allowed"},
            semantic_unit="Write after later approval.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), "allowed")
        self.assertGreaterEqual(len(state.effect_traces), 1)
        self.assertTrue(state.effect_traces[0]["decision"]["allowed"])
        self.assertEqual(state.effect_traces[0]["admission"]["status"], "admitted")
        self.assertEqual(
            state.effect_traces[0]["admission"]["approval_titles"],
            ["Operator Approval For Later Approved Write"],
        )

    def test_active_revocation_record_denies_current_use(self) -> None:
        state = SystemState.bootstrap("revoked broker")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "revoked-by-record.txt"
        artifact = self.make_governed_broker_artifact(title="Revoked Write", authority="write", admitted=True)
        revocation = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "revocation",
                "title": "Revoke Revoked Write",
                "revocation": {
                    "intent": "Revoke the named write skill.",
                    "subject_titles": ["Revoked Write"],
                    "subject_kinds": ["ability"],
                    "trust_status": "revoked",
                    "quarantine_status": "clear",
                    "activation_status": "inactive",
                    "installation_status": "blocked",
                    "status": "active",
                    "issued_by": "operator://local-admin",
                    "rationale": "This skill is revoked pending review.",
                },
            }
        )
        controller.artifact_store.load_all_artifacts = lambda: [revocation]  # type: ignore[method-assign]

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.write_text",
            broker_arguments={"path": str(target), "text": "blocked"},
            semantic_unit="Write with an active revocation record.",
        )

        self.assertEqual(result["status"], "error")
        self.assertFalse(target.exists())
        self.assertEqual(len(state.effect_traces), 1)
        self.assertFalse(state.effect_traces[0]["decision"]["allowed"])
        self.assertEqual(state.effect_traces[0]["lifecycle"]["trust_status"], "revoked")
        self.assertEqual(state.effect_traces[0]["lifecycle"]["activation_status"], "inactive")

    def test_open_quarantine_incident_denies_current_use(self) -> None:
        state = SystemState.bootstrap("incident quarantined broker")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "incident-quarantined.txt"
        artifact = self.make_governed_broker_artifact(title="Incident Write", authority="write", admitted=True)
        incident = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "incident",
                "title": "Quarantine Incident For Incident Write",
                "incident": {
                    "intent": "Quarantine the named write skill during an incident.",
                    "subject_titles": ["Incident Write"],
                    "subject_kinds": ["ability"],
                    "severity": "critical",
                    "enforcement_action": "quarantine",
                    "status": "open",
                    "issued_by": "operator://local-admin",
                    "rationale": "The skill is quarantined during the incident.",
                },
            }
        )
        controller.artifact_store.load_all_artifacts = lambda: [incident]  # type: ignore[method-assign]

        result = controller.execute_mediated_host_broker_request(
            artifact,
            broker_name="fs.write_text",
            broker_arguments={"path": str(target), "text": "blocked"},
            semantic_unit="Write with an open quarantine incident.",
        )

        self.assertEqual(result["status"], "error")
        self.assertFalse(target.exists())
        self.assertEqual(len(state.effect_traces), 1)
        self.assertFalse(state.effect_traces[0]["decision"]["allowed"])
        self.assertEqual(state.effect_traces[0]["lifecycle"]["quarantine_status"], "quarantined")
        self.assertEqual(state.effect_traces[0]["lifecycle"]["activation_status"], "inactive")

    def test_python_skill_can_use_governed_broker_api_for_file_write(self) -> None:
        """
        High Level Purpose:
            In circumstances like adopting broker-aware Python skills while preserving normal ability execution, helps with proving that a Python skill can call the governed broker API and that the parent runtime ingests the emitted child sub-effect trace.

        Reference to Theory:
            Verifies the first skill-side adoption step of the bundle plan by keeping filesystem effects brokered inside a Python skill rather than using raw file I/O.

        Example Input Output:
            Input: `test_python_skill_can_use_governed_broker_api_for_file_write()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("python broker adoption")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "brokered.txt"
        python_script = controller.callable_snippet_ability_script(
            title="Brokered File Write",
            scope="reuse for brokered file writes",
            justification="test",
            python_code="""
from python_skill_host import broker_request

def main(path: str, text: str, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:
    return broker_request("fs.write_text", path=path, text=text)
            """.strip(),
            function_name="main",
            argument_names=["path", "text"],
        )
        artifact = self.make_governed_broker_artifact(title="Brokered File Write", authority="write")
        artifact.content.update(
            {
                "python_script": python_script,
                "entrypoint": "main",
                "script_language": "python",
                "input_contract": {"path": "target file path", "text": "text to write"},
                "output_contract": {"status": "broker status", "bytes_written": "written byte count"},
            }
        )

        execution = controller.execute_function_artifact(
            artifact,
            explicit_payload={"path": str(target), "text": "governed"},
            semantic_unit="Write governed text to a file.",
        )

        self.assertTrue(execution.ok)
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), "governed")
        self.assertGreaterEqual(len(state.effect_traces), 2)
        self.assertEqual(state.effect_traces[-1]["request"]["effect_kind"], "execute.python3")
        self.assertEqual(state.effect_traces[-1]["host_abi_version"], host_abi_version())
        child_traces = [trace for trace in state.effect_traces if trace.get("kind") == "python_skill_broker"]
        self.assertEqual(len(child_traces), 1)
        self.assertEqual(child_traces[0]["effect_kind"], "fs.write_text")
        self.assertTrue(child_traces[0]["allowed"])
        self.assertEqual(child_traces[0]["host_abi_version"], host_abi_version())

    def test_legacy_python_skill_can_use_governed_broker_api_for_file_write(self) -> None:
        """
        High Level Purpose:
            In circumstances like legacy learned Python abilities that now call governed brokers, helps with proving that legacy implicit admission still permits child broker use.

        Reference to Theory:
            Verifies that brokerized legacy skills remain usable while governance v2 is phased in, instead of being rejected only because their admission status string is `legacy_implicit_admit`.

        Example Input Output:
            Input: `test_legacy_python_skill_can_use_governed_broker_api_for_file_write()`
            Output: None
        """
        state = SystemState.bootstrap("legacy python broker adoption")
        controller = BSSCController(state, llm_policy="off")
        target = Path(self.tempdir.name) / "legacy-brokered.txt"
        python_script = controller.callable_snippet_ability_script(
            title="Legacy Brokered File Write",
            scope="reuse for legacy brokered file writes",
            justification="test",
            python_code="""
from python_skill_host import broker_request

def main(path: str, text: str, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:
    return broker_request("fs.write_text", path=path, text=text)
            """.strip(),
            function_name="main",
            argument_names=["path", "text"],
        )
        artifact = Artifact(
            id="artifact-legacy-brokered-file-write",
            artifact_type=ArtifactType.ABILITY,
            title="Legacy Brokered File Write",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for legacy brokered file writes",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": python_script,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {"path": "target file path", "text": "text to write"},
                "output_contract": {"status": "broker status", "bytes_written": "written byte count"},
            },
            justification="A legacy brokered file-write ability.",
        )

        execution = controller.execute_function_artifact(
            artifact,
            explicit_payload={"path": str(target), "text": "legacy governed"},
            semantic_unit="Write legacy governed text to a file.",
        )

        self.assertTrue(execution.ok)
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), "legacy governed")
        child_traces = [trace for trace in state.effect_traces if trace.get("kind") == "python_skill_broker"]
        self.assertEqual(len(child_traces), 1)
        self.assertEqual(child_traces[0]["effect_kind"], "fs.write_text")
        self.assertTrue(child_traces[0]["allowed"])

    def test_named_tool_invoke_dispatches_through_registered_tool_surface(self) -> None:
        state = SystemState.bootstrap("invoke a named tool")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_governed_broker_artifact(title="Open Browser Tool", authority="execute")

        with patch.dict(
            host_brokers.HOST_BROKER_REGISTRY,
            {"macos.open_browser": lambda **kwargs: {"status": "ok", "url": kwargs.get("url", "")}},
            clear=False,
        ):
            result = controller.execute_mediated_host_broker_request(
                artifact,
                broker_name="tool.invoke",
                broker_arguments={
                    "tool_name": "open_browser",
                    "arguments": {"url": "https://example.com"},
                },
                semantic_unit="Open the example site in a browser.",
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["tool_name"], "open_browser")
        self.assertEqual(result["broker"], "macos.open_browser")
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(len(state.effect_traces), 1)
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "tool.invoke")
        self.assertTrue(state.effect_traces[0]["decision"]["allowed"])

    def test_skill_invoke_broker_executes_installed_skill_and_ingests_nested_trace(self) -> None:
        state = SystemState.bootstrap("invoke another governed skill")
        controller = BSSCController(state, llm_policy="off")
        store = build_artifact_store()
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "boundary_shape_artifacts"
            / "hi_responder.yaml"
        )
        artifact = load_artifact_yaml_documents(fixture_path)[0]
        store.persist_artifact(artifact, run_id="test_skill_invoke")

        caller = self.make_governed_broker_artifact(title="Invoke Nested Skill", authority="invoke")
        caller.content["skill_declaration"]["composition_rights"] = ["skill:Hi Responder"]
        result = controller.execute_mediated_host_broker_request(
            caller,
            broker_name="skill.invoke",
            broker_arguments={"skill_title": "Hi Responder", "semantic_unit": "Say hi."},
            semantic_unit="Invoke the hi responder skill.",
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["skill_title"], "Hi Responder")
        self.assertEqual(result["answer"], "hi")
        self.assertGreaterEqual(len(state.effect_traces), 2)
        effect_kinds = [trace.get("request", {}).get("effect_kind", "") for trace in state.effect_traces]
        self.assertIn("skill.invoke", effect_kinds)
        self.assertIn("execute.python3", effect_kinds)
        self.assertGreaterEqual(len(state.capability_grants), 3)

    def test_skill_invoke_broker_denies_unbound_nested_skill_title(self) -> None:
        state = SystemState.bootstrap("invoke unbound governed skill")
        controller = BSSCController(state, llm_policy="off")
        store = build_artifact_store()
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "boundary_shape_artifacts"
            / "hi_responder.yaml"
        )
        artifact = load_artifact_yaml_documents(fixture_path)[0]
        store.persist_artifact(artifact, run_id="test_skill_invoke_denied")

        caller = self.make_governed_broker_artifact(title="Invoke Nested Skill", authority="invoke")
        caller.content["skill_declaration"]["composition_rights"] = ["skill:Different Skill"]
        result = controller.execute_mediated_host_broker_request(
            caller,
            broker_name="skill.invoke",
            broker_arguments={"skill_title": "Hi Responder", "semantic_unit": "Say hi."},
            semantic_unit="Invoke the hi responder skill.",
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("do not bind this skill", result["error"])

    def test_host_broker_invocation_rejects_unknown_argument_under_host_abi(self) -> None:
        result = invoke_host_broker(
            "fs.read_mount",
            arguments={"mount": "skill_input", "relative_path": "docs", "unexpected": "value"},
            governance_context={
                "virtual_mounts": {
                    "skill_input": {
                        "root": self.tempdir.name,
                        "permissions": ["read"],
                        "data_class": "public",
                    }
                }
            },
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("does not declare arguments", result["error"])

    def test_host_broker_invocation_rejects_missing_required_argument_under_host_abi(self) -> None:
        result = invoke_host_broker(
            "macos.open_browser",
            arguments={"browser": "Safari"},
            governance_context={},
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("requires arguments: url", result["error"])

    def test_default_skill_tmp_mount_is_shared_by_store_boundary(self) -> None:
        first = default_virtual_mount_table(
            artifact_id="artifact-one",
            workspace_root=self.tempdir.name,
            sqlite_path=self.sqlite_path,
        )
        second = default_virtual_mount_table(
            artifact_id="artifact-two",
            workspace_root=self.tempdir.name,
            sqlite_path=self.sqlite_path,
        )

        self.assertEqual(first["skill_tmp"]["root"], second["skill_tmp"]["root"])
