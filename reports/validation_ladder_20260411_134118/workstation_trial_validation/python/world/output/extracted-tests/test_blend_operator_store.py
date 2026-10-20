import unittest

from applied_theory_types import Artifact
from blend_context import BlendContext
from blend_operator import BlendOperator
from blend_operator_store import (
    BlendOperatorProvider,
    BlendOperatorRecord,
    blend_capability_operator_record,
    get_blend_operator_summary,
    list_blend_operator_summaries,
    new_blend_capability_operator_provider,
    new_blend_skill_operator_provider,
    resolve_blend_operator_record,
    resolve_blend_operator_record_for_workflow_step,
)


class BlendOperatorStoreTests(unittest.TestCase):
    def _context(self) -> BlendContext:
        return BlendContext(
            attachments=(),
            visible_mounts=("main", "skills"),
            writable_mounts=("main", "skills"),
            granted_capabilities=("ws.skill.invoke", "ws.fs.read"),
            task_focus="Inspect operators",
            world_id="bworld_demo",
            world_root="/tmp/world",
            world_mounts=("main", "scratch", "output"),
        )

    def _record(self, *, operator_kind: str, name: str, source_kind: str) -> BlendOperatorRecord:
        return BlendOperatorRecord(
            operator={"name": name},
            operator_source={"source_kind": source_kind, "source_target": "skills" if operator_kind == "skill" else "main"},
            operator_descriptor=BlendOperator(
                operator_id=f"{operator_kind}:{name}",
                operator_kind=operator_kind,
                display_name=name,
                execution_adapter=f"test.{operator_kind}",
                semantic_description=f"{name} operator",
                context_requirements={"required_capabilities": ["ws.skill.invoke"]} if operator_kind == "skill" else {"required_capabilities": ["ws.fs.read"]},
                target_resolution={"default_target": "skills" if operator_kind == "skill" else "main"},
            ),
        )

    def _artifact(self, title: str) -> Artifact:
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
                    "skill_declaration": {
                        "intent": f"Execute {title}.",
                        "authorities_requested": ["execute"],
                        "executor_framework": "python3",
                    },
                },
            }
        )

    def test_list_blend_operator_summaries_filters_and_limits(self) -> None:
        provider = BlendOperatorProvider(
            provider_id="demo",
            list_operators=lambda _context: [
                self._record(operator_kind="skill", name="Emit Text", source_kind="attached_skill_store"),
                self._record(operator_kind="capability", name="ws.fs.read", source_kind="workstation_capability"),
            ],
            resolve_operator=lambda _name, _kind, _context: None,
        )
        items = list_blend_operator_summaries(
            context=self._context(),
            providers=(provider,),
            operator_kind="skill",
            query="emit",
            limit=5,
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["operator_name"], "Emit Text")
        self.assertEqual(items[0]["provider_id"], "demo")

    def test_resolve_blend_operator_record_uses_provider_resolution(self) -> None:
        record = self._record(operator_kind="capability", name="ws.fs.read", source_kind="workstation_capability")
        provider = BlendOperatorProvider(
            provider_id="demo",
            list_operators=lambda _context: [],
            resolve_operator=lambda name, kind, _context: record if name == "ws.fs.read" and kind == "capability" else None,
        )
        resolved = resolve_blend_operator_record(
            operator_name="ws.fs.read",
            operator_kind="capability",
            context=self._context(),
            providers=(provider,),
        )
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.operator_descriptor.display_name, "ws.fs.read")
        summary = get_blend_operator_summary(
            context=self._context(),
            providers=(provider,),
            operator_name="ws.fs.read",
            operator_kind="capability",
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["source_kind"], "workstation_capability")

    def test_new_blend_skill_operator_provider_projects_dynamic_skill_artifacts(self) -> None:
        artifact = self._artifact("Emit Text")
        provider = new_blend_skill_operator_provider(
            provider_id="dynamic_skills",
            list_skill_names=lambda _context: ["Emit Text"],
            resolve_skill=lambda name, _context: (
                (artifact, {"source_kind": "test_skill_store", "source_target": "skills"})
                if name == "Emit Text"
                else None
            ),
            visible_targets=("skills",),
            execution_adapter="test.skill_invoke",
        )
        items = list_blend_operator_summaries(
            context=self._context(),
            providers=(provider,),
            operator_kind="skill",
            query="emit",
            limit=10,
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["operator_name"], "Emit Text")
        self.assertEqual(items[0]["execution_adapter"], "test.skill_invoke")
        self.assertEqual(items[0]["source_kind"], "test_skill_store")

    def test_resolve_blend_operator_record_for_workflow_step_prefers_step_aware_provider_resolution(self) -> None:
        provider = new_blend_capability_operator_provider(
            provider_id="dynamic_capabilities",
            list_capability_names=lambda _context: ["ws.fs.read"],
            resolve_capability_record=lambda name, _context: (
                blend_capability_operator_record(
                    capability_name=name,
                    operator={"capability": name},
                    operator_source={"source_kind": "test_capability", "source_target": "main"},
                    input_shape={"path": "path"},
                    output_shape={"content": "content"},
                    required_capabilities=(name,),
                    required_visible_mounts=("main",),
                    default_target="main",
                    allowed_targets=("main",),
                    execution_adapter="test.capability",
                )
                if name == "ws.fs.read"
                else None
            ),
            resolve_workflow_step_record=lambda workflow_step, _context: blend_capability_operator_record(
                capability_name=workflow_step.operator_name,
                operator={"capability": workflow_step.operator_name},
                operator_source={
                    "source_kind": "test_capability",
                    "source_target": workflow_step.metadata.get("target", ""),
                },
                input_shape={"path": "path"},
                output_shape={"content": "content"},
                required_capabilities=(workflow_step.operator_name,),
                required_visible_mounts=(workflow_step.metadata.get("target", ""),),
                default_target=workflow_step.metadata.get("target", ""),
                allowed_targets=(workflow_step.metadata.get("target", ""),),
                execution_adapter="test.capability",
            ),
        )
        resolved = resolve_blend_operator_record_for_workflow_step(
            type(
                "Step",
                (),
                {
                    "operator_name": "ws.fs.read",
                    "operator_kind": "capability",
                    "metadata": {"target": "scratch"},
                },
            )(),
            context=self._context(),
            providers=(provider,),
        )
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.operator_source["source_target"], "scratch")
        self.assertEqual(
            resolved.operator_descriptor.target_resolution.get("default_target"),
            "scratch",
        )


if __name__ == "__main__":
    unittest.main()
