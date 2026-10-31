import unittest

from realized_blend.context import BlendContext
from realized_blend.operators import (
    BlendOperator,
    blend_operator_applicability,
    new_blend_operator_invocation,
    resolve_blend_operator_target,
)


class BlendOperatorTests(unittest.TestCase):
    def _context(
        self,
        *,
        capabilities=("ws.skill.invoke",),
        visible_mounts=("skills",),
        writable_mounts=("skills",),
        world_id="",
        world_root="",
        world_mounts=(),
    ) -> BlendContext:
        return BlendContext(
            attachments=(),
            visible_mounts=tuple(visible_mounts),
            writable_mounts=tuple(writable_mounts),
            granted_capabilities=tuple(capabilities),
            task_focus="Run operator",
            world_id=world_id,
            world_root=world_root,
            world_mounts=tuple(world_mounts),
        )

    def _operator(
        self,
        *,
        require_writable: bool = False,
        allowed_targets: tuple[str, ...] = ("skills",),
    ) -> BlendOperator:
        return BlendOperator(
            operator_id="skill:demo_operator",
            operator_kind="skill",
            display_name="Demo Operator",
            execution_adapter="test.skill.invoke",
            semantic_description="Demo operator",
            input_shape={"text": "text input"},
            output_shape={"result": "result output"},
            policy_requirements=("execute",),
            actor_visibility=("ai_chat", "automation_api"),
            context_requirements={
                "required_capabilities": ["ws.skill.invoke"],
                "required_visible_mounts": ["skills"],
                "required_writable_mounts": ["skills"] if require_writable else [],
            },
            target_resolution={
                "default_target": "skills",
                "allowed_targets": list(allowed_targets),
                "require_visible": True,
                "require_writable": require_writable,
            },
        )

    def test_blend_operator_applicability_reports_applicable_context(self) -> None:
        applicability = blend_operator_applicability(
            self._operator(),
            self._context(),
        )
        self.assertEqual(applicability["status"], "applicable")
        self.assertEqual(applicability["missing_capabilities"], [])
        self.assertEqual(applicability["missing_visible_mounts"], [])
        self.assertEqual(applicability["missing_writable_mounts"], [])
        self.assertEqual(applicability["missing_world_mounts"], [])
        self.assertFalse(applicability["missing_shared_world"])

    def test_blend_operator_applicability_reports_missing_requirements(self) -> None:
        applicability = blend_operator_applicability(
            self._operator(require_writable=True),
            self._context(capabilities=(), visible_mounts=("other",), writable_mounts=()),
        )
        self.assertEqual(applicability["status"], "blocked")
        self.assertEqual(applicability["missing_capabilities"], ["ws.skill.invoke"])
        self.assertEqual(applicability["missing_visible_mounts"], ["skills"])
        self.assertEqual(applicability["missing_writable_mounts"], ["skills"])
        self.assertEqual(applicability["missing_world_mounts"], [])
        self.assertFalse(applicability["missing_shared_world"])

    def test_blend_operator_applicability_reports_missing_world_requirements(self) -> None:
        operator = BlendOperator(
            operator_id="capability:shared_world_reader",
            operator_kind="capability",
            display_name="Shared World Reader",
            execution_adapter="test.capability",
            context_requirements={
                "require_shared_world": True,
                "required_world_mounts": ["scratch"],
            },
            target_resolution={},
        )
        applicability = blend_operator_applicability(
            operator,
            self._context(),
        )
        self.assertEqual(applicability["status"], "blocked")
        self.assertTrue(applicability["missing_shared_world"])
        self.assertEqual(applicability["missing_world_mounts"], ["scratch"])

    def test_resolve_blend_operator_target_uses_visible_default(self) -> None:
        target = resolve_blend_operator_target(
            self._operator(),
            self._context(visible_mounts=("skills", "main")),
        )
        self.assertEqual(target, "skills")

    def test_resolve_blend_operator_target_rejects_non_allowed_or_non_writable_target(self) -> None:
        self.assertEqual(
            resolve_blend_operator_target(
                self._operator(allowed_targets=("skills", "main")),
                self._context(visible_mounts=("skills", "main")),
                requested_target="exports",
            ),
            "",
        )
        self.assertEqual(
            resolve_blend_operator_target(
                self._operator(require_writable=True, allowed_targets=("skills", "main")),
                self._context(visible_mounts=("skills", "main"), writable_mounts=("skills",)),
                requested_target="main",
            ),
            "",
        )

    def test_new_blend_operator_invocation_captures_context_and_target(self) -> None:
        context = self._context()
        operator = self._operator()
        invocation = new_blend_operator_invocation(
            operator=operator,
            session_id="ws_demo",
            workflow_id="bwf_plan_demo",
            step_id="emit",
            context=context,
            inputs={"text": "hello"},
            resolved_target="skills",
            policy_state={"requested_delegation": ["execute"]},
            metadata={"semantic_unit": "Emit hello"},
        )
        self.assertTrue(invocation.invocation_id.startswith("bop_inv_"))
        self.assertEqual(invocation.operator.display_name, "Demo Operator")
        self.assertEqual(invocation.context.task_focus, "Run operator")
        self.assertEqual(invocation.inputs, {"text": "hello"})
        self.assertEqual(invocation.resolved_target, "skills")
        self.assertEqual(invocation.policy_state["requested_delegation"], ["execute"])
        self.assertEqual(invocation.metadata["semantic_unit"], "Emit hello")


if __name__ == "__main__":
    unittest.main()
