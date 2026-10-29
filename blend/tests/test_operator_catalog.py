from __future__ import annotations

from types import SimpleNamespace
import unittest

from realized_blend.context import BlendContext
from realized_blend.operators import (
    BlendOperator,
    BlendOperatorProvider,
    BlendOperatorRecord,
    list_blend_operator_summaries,
    resolve_blend_operator_record,
    resolve_blend_operator_record_for_workflow_step,
)


class BlendOperatorCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = BlendContext(
            attachments=(),
            visible_mounts=("main",),
            writable_mounts=("main",),
            granted_capabilities=("ws.fs.read",),
        )

    def _record(
        self,
        *,
        operator_id: str,
        name: str,
        handle: object,
        source_kind: str,
        actor_visibility: tuple[str, ...] = ("ai_chat",),
    ) -> BlendOperatorRecord:
        return BlendOperatorRecord(
            operator=handle,
            operator_source={"source_kind": source_kind, "source_target": "main"},
            operator_descriptor=BlendOperator(
                operator_id=operator_id,
                operator_kind="capability",
                display_name=name,
                execution_adapter="test.capability",
                semantic_description=f"Read with {name}",
                actor_visibility=actor_visibility,
            ),
        )

    def test_record_exposes_but_does_not_interpret_opaque_invocation_handle(self) -> None:
        handle = object()
        record = self._record(
            operator_id="capability:read",
            name="ws.fs.read",
            handle=handle,
            source_kind="first",
        )

        self.assertIs(record.invocation_handle, handle)
        self.assertIs(record.operator, handle)
        self.assertNotIn("operator", record.to_summary())
        self.assertNotIn("invocation_handle", record.to_summary())

    def test_listing_filters_sorts_and_preserves_first_provider_for_duplicate_id(self) -> None:
        first = self._record(
            operator_id="capability:read",
            name="Zeta Read",
            handle="first-handle",
            source_kind="first-source",
            actor_visibility=("ai_chat", "hitl_review"),
        )
        duplicate = self._record(
            operator_id="capability:read",
            name="Ignored Duplicate",
            handle="second-handle",
            source_kind="second-source",
        )
        alpha = self._record(
            operator_id="capability:alpha",
            name="Alpha Read",
            handle="alpha-handle",
            source_kind="first-source",
        )
        providers = (
            BlendOperatorProvider(
                provider_id="first",
                list_operators=lambda _context: (first, alpha),
                resolve_operator=lambda _name, _kind, _context: None,
            ),
            BlendOperatorProvider(
                provider_id="second",
                list_operators=lambda _context: (duplicate,),
                resolve_operator=lambda _name, _kind, _context: None,
            ),
        )

        items = list_blend_operator_summaries(
            context=self.context,
            providers=providers,
            operator_kind=" CAPABILITY ",
            query="read!",
            limit=20,
        )

        self.assertEqual(["Alpha Read", "Zeta Read"], [item["operator_name"] for item in items])
        self.assertEqual("first", items[1]["provider_id"])
        self.assertEqual("first-source", items[1]["source_kind"])
        self.assertEqual(["ai_chat", "hitl_review"], items[1]["actor_visibility"])

    def test_resolution_preserves_first_provider_precedence(self) -> None:
        first = self._record(
            operator_id="capability:read:first",
            name="ws.fs.read",
            handle="first-handle",
            source_kind="first",
        )
        second = self._record(
            operator_id="capability:read:second",
            name="ws.fs.read",
            handle="second-handle",
            source_kind="second",
        )
        providers = (
            BlendOperatorProvider(
                provider_id="first",
                list_operators=lambda _context: (),
                resolve_operator=lambda _name, _kind, _context: first,
            ),
            BlendOperatorProvider(
                provider_id="second",
                list_operators=lambda _context: (),
                resolve_operator=lambda _name, _kind, _context: second,
            ),
        )

        resolved = resolve_blend_operator_record(
            operator_name=" ws.fs.read ",
            operator_kind="capability",
            context=self.context,
            providers=providers,
        )

        self.assertIs(resolved, first)

    def test_step_aware_resolution_precedes_generic_resolution_across_providers(self) -> None:
        generic = self._record(
            operator_id="capability:read:generic",
            name="ws.fs.read",
            handle="generic-handle",
            source_kind="generic",
        )
        step_specific = self._record(
            operator_id="capability:read:step",
            name="ws.fs.read",
            handle="step-handle",
            source_kind="step",
        )
        providers = (
            BlendOperatorProvider(
                provider_id="generic-first",
                list_operators=lambda _context: (),
                resolve_operator=lambda _name, _kind, _context: generic,
            ),
            BlendOperatorProvider(
                provider_id="step-second",
                list_operators=lambda _context: (),
                resolve_operator=lambda _name, _kind, _context: None,
                resolve_workflow_step=lambda _step, _context: step_specific,
            ),
        )

        resolved = resolve_blend_operator_record_for_workflow_step(
            SimpleNamespace(operator_name="ws.fs.read", operator_kind="capability"),
            context=self.context,
            providers=providers,
        )

        self.assertIs(resolved, step_specific)


if __name__ == "__main__":
    unittest.main()
