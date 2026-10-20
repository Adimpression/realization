import tempfile
import unittest
from pathlib import Path

from applied_theory_types import Artifact
from blend_context import BlendContext
from blend_operator import BlendOperator
from blend_operator_store import new_blend_skill_operator_provider
from blend_workflow import BlendWorkflowPlan, blend_workflow_plan_from_skill_compose_arguments, load_blend_workflow_run
from blend_workflow_execution import (
    execute_blend_skill_workflow,
    resolve_blend_skill_workflow_steps,
    resolve_blend_workflow_steps_from_providers,
)


def _canonical_skill(title: str, *, input_path: str, output_path: str) -> dict:
    return {
        "artifact_id": f"artifact-{title.lower().replace(' ', '-')}",
        "kind": "ability",
        "title": title,
        "schema": "bssc_skill.v2",
        "normalization": {
            "regions": {
                "a": {
                    "boundary_term": "a*",
                    "leaves": [
                        {
                            "region": "a*",
                            "path": input_path,
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
                            "path": output_path,
                            "carrier_kind": "value",
                            "data_type": "String",
                            "semantic_label": "text",
                            "leaf_class": "scalar",
                        }
                    ],
                },
            }
        },
    }


class BlendWorkflowExecutionTests(unittest.TestCase):
    def _context(self, *, capabilities=("ws.skill.invoke",), visible_mounts=("skills",), writable_mounts=()) -> BlendContext:
        return BlendContext(
            attachments=(),
            visible_mounts=tuple(visible_mounts),
            writable_mounts=tuple(writable_mounts),
            granted_capabilities=tuple(capabilities),
            task_focus="Run workflow",
        )

    def _operator(self, name: str) -> BlendOperator:
        return BlendOperator(
            operator_id=f"skill:{name.lower().replace(' ', '_')}",
            operator_kind="skill",
            display_name=name,
            execution_adapter="test.skill.invoke",
            semantic_description=name,
            input_shape={"text": "text input"},
            output_shape={"text": "text output"},
            policy_requirements=("execute",),
            actor_visibility=("ai_chat",),
            context_requirements={
                "required_capabilities": ["ws.skill.invoke"],
                "required_visible_mounts": ["skills"],
            },
            target_resolution={
                "default_target": "skills",
                "allowed_targets": ["skills"],
                "require_visible": True,
            },
        )

    def _artifact(self, title: str, *, input_path: str, output_path: str) -> Artifact:
        return Artifact.from_dict(
            {
                "id": f"artifact-{title.lower().replace(' ', '-')}",
                "artifact_type": "ability",
                "title": title,
                "representation": "python_script",
                "function_bit": 1,
                "scope": "local_executor",
                "provenance": [],
                "reusability": "local_reuse",
                "admissibility": "candidate",
                "template_schema": {},
                "learning_relation": "new_family",
                "related_artifact_ids": [],
                "content": {
                    "input_contract": {"text": "text input"},
                    "output_contract": {"text": "text output"},
                    "normalization": {
                        "regions": {
                            "a": {
                                "boundary_term": "a*",
                                "leaves": [
                                    {
                                        "region": "a*",
                                        "path": input_path,
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
                                        "path": output_path,
                                        "carrier_kind": "value",
                                        "data_type": "String",
                                        "semantic_label": "text",
                                        "leaf_class": "scalar",
                                    }
                                ],
                            },
                        }
                    },
                    "skill_declaration": {
                        "intent": f"Execute {title}.",
                        "authorities_requested": ["execute"],
                        "executor_framework": "python3",
                    },
                },
            }
        )

    def _capability_operator(self, name: str, *, target: str = "main") -> BlendOperator:
        return BlendOperator(
            operator_id=f"capability:{name}:{target}",
            operator_kind="capability",
            display_name=name,
            execution_adapter="test.capability",
            semantic_description=name,
            input_shape={"path": "path input"},
            output_shape={"content": "content output"},
            policy_requirements=("read",),
            actor_visibility=("ai_chat",),
            context_requirements={
                "required_capabilities": [name],
                "required_visible_mounts": [target],
            },
            target_resolution={
                "default_target": target,
                "allowed_targets": [target],
                "require_visible": True,
            },
        )

    def test_resolve_blend_skill_workflow_steps_resolves_typed_plan(self) -> None:
        plan = blend_workflow_plan_from_skill_compose_arguments(
            {
                "steps": [
                    {"step_id": "emit", "skill_title": "Emit Text"},
                    {"step_id": "consume", "skill_title": "Consume Text"},
                ]
            }
        )
        resolved_steps, ordered_titles = resolve_blend_skill_workflow_steps(
            plan,
            context=self._context(),
            resolve_operator=lambda step, _context: (
                _canonical_skill(step.operator_name, input_path="/a/text", output_path="/d/text"),
                {"source_kind": "test"},
                self._operator(step.operator_name),
            ),
        )
        self.assertEqual(ordered_titles, ["Emit Text", "Consume Text"])
        self.assertEqual([item.step_id for item in resolved_steps], ["emit", "consume"])
        self.assertEqual(resolved_steps[0].operator_name, "Emit Text")
        self.assertEqual(resolved_steps[0].operator_source["source_kind"], "test")
        self.assertEqual(resolved_steps[0].operator_descriptor.display_name, "Emit Text")
        self.assertEqual(resolved_steps[0].resolved_target, "skills")
        self.assertEqual(resolved_steps[0].context_applicability["status"], "applicable")

    def test_resolve_blend_skill_workflow_steps_blocks_when_context_lacks_required_capability(self) -> None:
        plan = blend_workflow_plan_from_skill_compose_arguments(
            {"steps": [{"step_id": "emit", "skill_title": "Emit Text"}]}
        )
        with self.assertRaises(ValueError) as exc:
            resolve_blend_skill_workflow_steps(
                plan,
                context=self._context(capabilities=()),
                resolve_operator=lambda step, _context: (
                    _canonical_skill(step.operator_name, input_path="/a/text", output_path="/d/text"),
                    {"source_kind": "test"},
                    self._operator(step.operator_name),
                ),
            )
        self.assertIn("not applicable", str(exc.exception))

    def test_resolve_blend_skill_workflow_steps_accepts_capability_operator_kind(self) -> None:
        plan = BlendWorkflowPlan.from_dict(
            {
                "workflow_kind": "workflow",
                "steps": [
                    {
                        "step_id": "read",
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
                    }
                ],
                "root_inputs": {"path": "README.md"},
                "final_output_step": "read",
            }
        )
        resolved_steps, ordered_titles = resolve_blend_skill_workflow_steps(
            plan,
            context=self._context(capabilities=("ws.fs.read",), visible_mounts=("main",)),
            resolve_operator=lambda step, _context: (
                _canonical_skill(step.operator_name, input_path="/a/path", output_path="/d/content"),
                {"source_kind": "test_capability", "source_target": "main"},
                self._capability_operator(step.operator_name),
            ),
        )
        self.assertEqual(ordered_titles, ["ws.fs.read"])
        self.assertEqual(resolved_steps[0].operator_descriptor.operator_kind, "capability")
        self.assertEqual(resolved_steps[0].resolved_target, "main")

    def test_resolve_blend_workflow_steps_from_providers_uses_shared_provider_surface(self) -> None:
        plan = blend_workflow_plan_from_skill_compose_arguments(
            {
                "steps": [
                    {"step_id": "emit", "skill_title": "Emit Text"},
                    {"step_id": "consume", "skill_title": "Consume Text"},
                ]
            }
        )
        provider = new_blend_skill_operator_provider(
            provider_id="dynamic_skills",
            list_skill_names=lambda _context: ["Emit Text", "Consume Text"],
            resolve_skill=lambda name, _context: (
                (
                    self._artifact(name, input_path="/a/text", output_path="/d/text"),
                    {"source_kind": "dynamic_skill_store", "source_target": "skills"},
                )
                if name in {"Emit Text", "Consume Text"}
                else None
            ),
            visible_targets=("skills",),
            execution_adapter="test.skill.invoke",
        )
        resolved_steps, ordered_titles = resolve_blend_workflow_steps_from_providers(
            plan,
            context=self._context(),
            providers=(provider,),
        )
        self.assertEqual(ordered_titles, ["Emit Text", "Consume Text"])
        self.assertEqual([item.operator_name for item in resolved_steps], ["Emit Text", "Consume Text"])
        self.assertEqual(resolved_steps[0].operator_source["source_kind"], "dynamic_skill_store")
        self.assertEqual(resolved_steps[0].operator_descriptor.execution_adapter, "test.skill.invoke")

    def test_execute_blend_skill_workflow_persists_plan_and_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            plan = blend_workflow_plan_from_skill_compose_arguments(
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
                    "root_inputs": {"text": "hello shared workflow"},
                    "final_output_step": "consume",
                }
            )
            resolved_steps, _ = resolve_blend_skill_workflow_steps(
                plan,
                context=self._context(),
                resolve_operator=lambda step, _context: (
                    _canonical_skill(
                        step.operator_name,
                        input_path="/a/text",
                        output_path="/d/text" if step.operator_name == "Emit Text" else "/d/result",
                    ),
                    {"source_kind": "test"},
                    self._operator(step.operator_name),
                ),
            )

            seen_invocations = []

            def invoke_step(resolved_step, invocation) -> dict:
                seen_invocations.append(invocation)
                if resolved_step.operator_name == "Emit Text":
                    text = str(invocation.inputs.get("text", ""))
                    return {
                        "status": "ok",
                        "answer": text,
                        "result_payload": {"text": text},
                        "parsed_output": {"text": text},
                    }
                text = str(invocation.inputs.get("text", ""))
                return {
                    "status": "ok",
                    "answer": f"consumed:{text}",
                    "result_payload": {"result": f"consumed:{text}"},
                    "parsed_output": {"result": f"consumed:{text}"},
                }

            result = execute_blend_skill_workflow(
                root_path=root,
                session_id="ws_demo",
                context=self._context(),
                workflow_plan=plan,
                resolved_steps=resolved_steps,
                capability_name="ws.workflow.run",
                target_name="skills",
                invoke_step=invoke_step,
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["final_output"], {"result": "consumed:hello shared workflow"})
            self.assertTrue(result["workflow_id"].startswith("bwf_plan_"))
            self.assertTrue(result["workflow_run_id"].startswith("bwf_run_"))
            self.assertTrue(Path(result["workflow_store"]["plan_path"]).exists())
            self.assertTrue(Path(result["workflow_store"]["run_path"]).exists())
            persisted_run = load_blend_workflow_run(root, result["workflow_run_id"])
            self.assertEqual(persisted_run.status, "ok")
            self.assertEqual(persisted_run.final_output, {"result": "consumed:hello shared workflow"})
            self.assertEqual(seen_invocations[0].resolved_target, "skills")
            self.assertEqual(seen_invocations[0].context.granted_capabilities, ("ws.skill.invoke",))
            self.assertEqual(result["steps"][0]["operator"]["display_name"], "Emit Text")
            self.assertEqual(result["steps"][0]["context_applicability"]["status"], "applicable")

    def test_execute_blend_skill_workflow_persists_approval_required_halt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            plan = blend_workflow_plan_from_skill_compose_arguments(
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
                            "step_id": "write",
                            "skill_title": "Write Text",
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
                    "root_inputs": {"text": "hello"},
                }
            )
            resolved_steps, _ = resolve_blend_skill_workflow_steps(
                plan,
                context=self._context(),
                resolve_operator=lambda step, _context: (
                    _canonical_skill(
                        step.operator_name,
                        input_path="/a/text",
                        output_path="/d/text",
                    ),
                    {"source_kind": "test"},
                    self._operator(step.operator_name),
                ),
            )

            def invoke_step(resolved_step, _invocation) -> dict:
                if resolved_step.operator_name == "Emit Text":
                    return {
                        "status": "ok",
                        "answer": "hello",
                        "result_payload": {"text": "hello"},
                        "parsed_output": {"text": "hello"},
                    }
                return {
                    "status": "approval_required",
                    "answer": "Need write approval.",
                    "requested_delegation": [
                        {
                            "capability": "write",
                            "target": "main",
                            "rationale": "write output file",
                        }
                    ],
                }

            result = execute_blend_skill_workflow(
                root_path=root,
                session_id="ws_demo",
                context=self._context(),
                workflow_plan=plan,
                resolved_steps=resolved_steps,
                capability_name="ws.workflow.run",
                target_name="skills",
                invoke_step=invoke_step,
            )
            self.assertEqual(result["status"], "approval_required")
            self.assertEqual(result["blocked_step_id"], "write")
            self.assertEqual(result["blocked_skill_title"], "Write Text")
            self.assertEqual(result["requested_delegation"][0]["capability"], "write")
            persisted_run = load_blend_workflow_run(root, result["workflow_run_id"])
            self.assertEqual(persisted_run.status, "approval_required")

    def test_execute_blend_skill_workflow_publishes_successful_step_lifecycle_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            plan = blend_workflow_plan_from_skill_compose_arguments(
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
                    "root_inputs": {"text": "hello events"},
                    "final_output_step": "consume",
                }
            )
            resolved_steps, _ = resolve_blend_skill_workflow_steps(
                plan,
                context=self._context(),
                resolve_operator=lambda step, _context: (
                    _canonical_skill(
                        step.operator_name,
                        input_path="/a/text",
                        output_path="/d/text" if step.operator_name == "Emit Text" else "/d/result",
                    ),
                    {"source_kind": "test"},
                    self._operator(step.operator_name),
                ),
            )
            seen_events = []

            def _observer(event) -> None:
                seen_events.append(event)

            def invoke_step(resolved_step, invocation) -> dict:
                text = str(invocation.inputs.get("text", ""))
                if resolved_step.operator_name == "Emit Text":
                    return {
                        "status": "ok",
                        "answer": text,
                        "result_payload": {"text": text},
                        "parsed_output": {"text": text},
                    }
                return {
                    "status": "ok",
                    "answer": f"consumed:{text}",
                    "result_payload": {"result": f"consumed:{text}"},
                    "parsed_output": {"result": f"consumed:{text}"},
                }

            result = execute_blend_skill_workflow(
                root_path=root,
                session_id="ws_demo",
                context=self._context(),
                workflow_plan=plan,
                resolved_steps=resolved_steps,
                capability_name="ws.workflow.run",
                target_name="skills",
                invoke_step=invoke_step,
                execution_observer=_observer,
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(
                [event.kind for event in seen_events],
                [
                    "blend_workflow_started",
                    "blend_step_started",
                    "blend_step_completed",
                    "blend_step_started",
                    "blend_step_completed",
                    "blend_workflow_completed",
                    "blend_workflow_persisted",
                ],
            )
            self.assertTrue(all(event.workflow_execution_id for event in seen_events))
            self.assertEqual(len({event.workflow_execution_id for event in seen_events}), 1)
            self.assertEqual(seen_events[1].step_id, "emit")
            self.assertEqual(seen_events[1].operator_name, "Emit Text")
            self.assertEqual(seen_events[2].status, "ok")
            self.assertEqual(seen_events[-1].workflow_run_id, result["workflow_run_id"])

    def test_execute_blend_skill_workflow_publishes_skipped_step_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            plan = blend_workflow_plan_from_skill_compose_arguments(
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
                            "run_if": [
                                {
                                    "source_step_id": "emit",
                                    "source_region": "d",
                                    "source_path": "/d/text",
                                    "operator": "equals",
                                    "expected_value": "never matches",
                                }
                            ],
                        },
                    ],
                    "root_inputs": {"text": "hello"},
                }
            )
            resolved_steps, _ = resolve_blend_skill_workflow_steps(
                plan,
                context=self._context(),
                resolve_operator=lambda step, _context: (
                    _canonical_skill(step.operator_name, input_path="/a/text", output_path="/d/text"),
                    {"source_kind": "test"},
                    self._operator(step.operator_name),
                ),
            )
            seen_events = []

            def invoke_step(_resolved_step, invocation) -> dict:
                text = str(invocation.inputs.get("text", ""))
                return {
                    "status": "ok",
                    "answer": text,
                    "result_payload": {"text": text},
                    "parsed_output": {"text": text},
                }

            result = execute_blend_skill_workflow(
                root_path=root,
                session_id="ws_demo",
                context=self._context(),
                workflow_plan=plan,
                resolved_steps=resolved_steps,
                capability_name="ws.workflow.run",
                target_name="skills",
                invoke_step=invoke_step,
                execution_observer=lambda event: seen_events.append(event),
            )
            self.assertEqual(result["status"], "ok")
            self.assertIn("blend_step_skipped", [event.kind for event in seen_events])
            skipped_event = next(event for event in seen_events if event.kind == "blend_step_skipped")
            self.assertEqual(skipped_event.step_id, "consume")
            self.assertEqual(skipped_event.status, "skipped")
            self.assertEqual(seen_events[-2].kind, "blend_workflow_completed")
            self.assertEqual(seen_events[-1].kind, "blend_workflow_persisted")

    def test_execute_blend_skill_workflow_publishes_blocked_and_failed_step_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            blocked_plan = blend_workflow_plan_from_skill_compose_arguments(
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
                            "step_id": "write",
                            "skill_title": "Write Text",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/text",
                                    "source_step_id": "emit",
                                    "source_region": "d",
                                    "source_path": "/d/text",
                                }
                            ],
                        },
                    ],
                    "root_inputs": {"text": "hello"},
                }
            )
            blocked_steps, _ = resolve_blend_skill_workflow_steps(
                blocked_plan,
                context=self._context(),
                resolve_operator=lambda step, _context: (
                    _canonical_skill(step.operator_name, input_path="/a/text", output_path="/d/text"),
                    {"source_kind": "test"},
                    self._operator(step.operator_name),
                ),
            )
            blocked_events = []

            def blocked_invoke_step(resolved_step, _invocation) -> dict:
                if resolved_step.operator_name == "Emit Text":
                    return {
                        "status": "ok",
                        "answer": "hello",
                        "result_payload": {"text": "hello"},
                        "parsed_output": {"text": "hello"},
                    }
                return {
                    "status": "approval_required",
                    "answer": "Need write approval.",
                    "requested_delegation": [{"capability": "write", "target": "main"}],
                }

            blocked_result = execute_blend_skill_workflow(
                root_path=root,
                session_id="ws_demo",
                context=self._context(),
                workflow_plan=blocked_plan,
                resolved_steps=blocked_steps,
                capability_name="ws.workflow.run",
                target_name="skills",
                invoke_step=blocked_invoke_step,
                execution_observer=lambda event: blocked_events.append(event),
            )
            self.assertEqual(blocked_result["status"], "approval_required")
            self.assertIn("blend_step_blocked", [event.kind for event in blocked_events])
            self.assertEqual(blocked_events[-2].kind, "blend_workflow_failed")
            self.assertEqual(blocked_events[-2].status, "approval_required")
            self.assertEqual(blocked_events[-1].kind, "blend_workflow_persisted")

            failed_plan = blend_workflow_plan_from_skill_compose_arguments(
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
                        }
                    ],
                    "root_inputs": {"text": "hello"},
                }
            )
            failed_steps, _ = resolve_blend_skill_workflow_steps(
                failed_plan,
                context=self._context(),
                resolve_operator=lambda step, _context: (
                    _canonical_skill(step.operator_name, input_path="/a/text", output_path="/d/text"),
                    {"source_kind": "test"},
                    self._operator(step.operator_name),
                ),
            )
            failed_events = []

            failed_result = execute_blend_skill_workflow(
                root_path=root,
                session_id="ws_demo",
                context=self._context(),
                workflow_plan=failed_plan,
                resolved_steps=failed_steps,
                capability_name="ws.workflow.run",
                target_name="skills",
                invoke_step=lambda _resolved_step, _invocation: (_ for _ in ()).throw(RuntimeError("boom")),
                execution_observer=lambda event: failed_events.append(event),
            )
            self.assertEqual(failed_result["status"], "error")
            self.assertIn("blend_step_failed", [event.kind for event in failed_events])
            self.assertEqual(failed_events[-2].kind, "blend_workflow_failed")
            self.assertEqual(failed_events[-2].status, "error")
            self.assertEqual(failed_events[-1].kind, "blend_workflow_persisted")


if __name__ == "__main__":
    unittest.main()
