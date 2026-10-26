# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from pathlib import Path
import unittest

from skill_compiler import compile_skill_document
from skill_composition import (
    SkillCompositionBinding,
    SkillCompositionCondition,
    SkillCompositionMapper,
    execute_skill_composition_plan,
    SkillCompositionStep,
    analyze_skill_composition_plan,
    propose_skill_leaf_bindings,
)
from skill_schema_io import load_skill_yaml_payload_documents


REPO_ROOT = Path(__file__).resolve().parents[1]


def _ability_document(
    *,
    title: str,
    inputs: dict[str, str],
    outputs: dict[str, str],
    normalization: dict[str, object],
    authorities_requested: list[str] | None = None,
) -> dict[str, object]:
    requested = authorities_requested or ["execute"]
    authority_bounds = {
        authority: {
            "scope": "local_executor",
            "target": "python3_skill_runtime",
            "context": "explicit_user_prompt",
            "duration": "single_invocation",
            "triggering_conditions": ["user invokes skill"],
            "approval_class": "automatic",
        }
        for authority in requested
    }
    return {
        "schema": "bssc_skill.v2",
        "kind": "ability",
        "title": title,
        "executor": "python3",
        "inputs": inputs,
        "outputs": outputs,
        "python": "def main(**kwargs):\n    return kwargs\n",
        "declaration": {
            "intent": f"Execute {title}.",
            "inputs": inputs,
            "outputs": outputs,
            "authorities_requested": requested,
            "authority_bounds": authority_bounds,
            "data_classes_touched": ["public"],
            "side_effects": ["local executor invocation"],
            "persistence_behavior": "none",
            "invocation_rights": ["direct_user_invocation"],
            "composition_rights": [],
            "escalation_rights": [],
            "approval_requirements": ["automatic"],
            "risk_tier": "tier1_bounded_transform",
        },
        "normalization": normalization,
    }


class SkillCompositionTests(unittest.TestCase):
    def _compiled_ir(self, payload: dict[str, object]) -> dict[str, object]:
        return compile_skill_document(payload).canonical_ir

    def _trial_ability(self, bundle_path: str, title_prefix: str) -> dict[str, object]:
        documents = load_skill_yaml_payload_documents(REPO_ROOT / bundle_path)
        for document in documents:
            if document.get("kind") == "ability" and str(document.get("title", "")).startswith(title_prefix):
                return compile_skill_document(document).canonical_ir
        raise AssertionError(f"Did not find ability starting with {title_prefix!r} in {bundle_path!r}")

    def test_historical_artifact_steps_remain_accepted_by_root_adapter(self) -> None:
        compiled = compile_skill_document(
            _ability_document(
                title="Emit Status",
                inputs={},
                outputs={"status": "status output"},
                normalization={
                    "regions": {
                        "d": {
                            "boundary_term": "d*",
                            "leaves": [
                                {
                                    "region": "d*",
                                    "path": "/d/status",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "status",
                                    "value": "ok",
                                    "leaf_class": "scalar",
                                }
                            ],
                        }
                    }
                },
            )
        )

        analysis = analyze_skill_composition_plan(
            [SkillCompositionStep(step_id="emit", skill=compiled.artifact)]
        )

        self.assertFalse(analysis.blocked)
        self.assertEqual("emit", analysis.steps[0]["step_id"])

    def test_propose_skill_leaf_bindings_finds_exact_value_mapping(self) -> None:
        source = self._compiled_ir(
            _ability_document(
                title="Emit Text",
                inputs={},
                outputs={"text": "text output"},
                normalization={
                    "regions": {
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
                        }
                    }
                },
            )
        )
        target = self._compiled_ir(
            _ability_document(
                title="Consume Text",
                inputs={"text": "text input"},
                outputs={"status": "status output"},
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
                        }
                    }
                },
            )
        )

        candidates = propose_skill_leaf_bindings(source, target)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].status, "exact")
        self.assertEqual(candidates[0].source_path, "/d/text")
        self.assertEqual(candidates[0].target_path, "/a/text")

    def test_propose_skill_leaf_bindings_requires_mapper_for_repeated_to_singular(self) -> None:
        source = self._compiled_ir(
            _ability_document(
                title="Emit Lines",
                inputs={},
                outputs={"lines": "line outputs"},
                normalization={
                    "regions": {
                        "d": {
                            "boundary_term": "d*",
                            "leaves": [
                                {
                                    "region": "d*",
                                    "path": "/d/lines",
                                    "carrier_kind": "value",
                                    "data_type": "Strings",
                                    "semantic_label": "lines",
                                    "value": ["a", "b"],
                                    "leaf_class": "collection",
                                }
                            ],
                        }
                    }
                },
            )
        )
        target = self._compiled_ir(
            _ability_document(
                title="Consume Line",
                inputs={"line": "line input"},
                outputs={"status": "status output"},
                normalization={
                    "regions": {
                        "a": {
                            "boundary_term": "a*",
                            "leaves": [
                                {
                                    "region": "a*",
                                    "path": "/a/line",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "line",
                                    "value": "line input",
                                    "leaf_class": "scalar",
                                }
                            ],
                        }
                    }
                },
            )
        )

        candidates = propose_skill_leaf_bindings(source, target)

        self.assertEqual(candidates[0].status, "mapper_required")
        self.assertIn("multiplicity", candidates[0].reason)

    def test_analyze_skill_composition_plan_supports_root_bindings_and_mapper_required_edge(self) -> None:
        read_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 02 — Read Text File")
        write_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 03 — Write Text File")

        analysis = analyze_skill_composition_plan(
            [
                SkillCompositionStep(
                    step_id="read",
                    skill=read_skill,
                    bindings=(
                        SkillCompositionBinding(target_region="a", target_path="/a/mount", source_root_name="mount", source_root_region="a"),
                        SkillCompositionBinding(target_region="a", target_path="/a/relative_path", source_root_name="relative_path", source_root_region="a"),
                    ),
                ),
                SkillCompositionStep(
                    step_id="write",
                    skill=write_skill,
                    bindings=(
                        SkillCompositionBinding(target_region="a", target_path="/a/mount", source_root_name="mount", source_root_region="a"),
                        SkillCompositionBinding(target_region="a", target_path="/a/relative_path", constant_value="copied.txt", source_region="a"),
                        SkillCompositionBinding(
                            target_region="a",
                            target_path="/a/text",
                            source_step_id="read",
                            source_region="d",
                            source_path="/d/result",
                        ),
                    ),
                ),
            ],
            root_inputs={
                "mount": "String",
                "relative_path": "String",
            },
        )

        self.assertFalse(analysis.blocked)
        self.assertEqual(analysis.unresolved_targets, [])
        write_step = next(item for item in analysis.steps if item["step_id"] == "write")
        text_binding = next(item for item in write_step["bindings"] if item["target_path"] == "/a/text")
        self.assertEqual(text_binding["status"], "mapper_required")
        self.assertEqual(text_binding["source_step_id"], "read")
        self.assertEqual(text_binding["source_path"], "/d/result")

    def test_analyze_skill_composition_plan_tracks_conditions_iteration_and_permissions(self) -> None:
        decide_skill = self._compiled_ir(
            _ability_document(
                title="Decide Status",
                inputs={},
                outputs={"status": "status output", "has_more": "has_more output"},
                normalization={
                    "regions": {
                        "d": {
                            "boundary_term": "d*",
                            "leaves": [
                                {
                                    "region": "d*",
                                    "path": "/d/status",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "status",
                                    "value": "ok",
                                    "leaf_class": "scalar",
                                },
                                {
                                    "region": "d*",
                                    "path": "/d/has_more",
                                    "carrier_kind": "value",
                                    "data_type": "Boolean",
                                    "semantic_label": "has_more",
                                    "value": True,
                                    "leaf_class": "scalar",
                                },
                            ],
                        }
                    }
                },
                authorities_requested=["execute", "read"],
            )
        )
        branch_skill = self._compiled_ir(
            _ability_document(
                title="Handle Ok",
                inputs={"status": "status input"},
                outputs={"result": "result output"},
                normalization={
                    "regions": {
                        "a": {
                            "boundary_term": "a*",
                            "leaves": [
                                {
                                    "region": "a*",
                                    "path": "/a/status",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "status",
                                    "value": "status input",
                                    "leaf_class": "scalar",
                                }
                            ],
                        }
                    }
                },
                authorities_requested=["execute", "write"],
            )
        )

        analysis = analyze_skill_composition_plan(
            [
                SkillCompositionStep(step_id="decide", skill=decide_skill),
                SkillCompositionStep(
                    step_id="handle_ok",
                    skill=branch_skill,
                    bindings=(
                        SkillCompositionBinding(
                            target_region="a",
                            target_path="/a/status",
                            source_step_id="decide",
                            source_region="d",
                            source_path="/d/status",
                        ),
                    ),
                    run_if=(
                        SkillCompositionCondition(
                            source_step_id="decide",
                            source_region="d",
                            source_path="/d/status",
                            operator="equals",
                            expected_value="ok",
                        ),
                    ),
                    iterate_until=(
                        SkillCompositionCondition(
                            source_step_id="decide",
                            source_region="d",
                            source_path="/d/has_more",
                            operator="equals",
                            expected_value=False,
                        ),
                    ),
                    branch_label="ok",
                ),
            ]
        )

        self.assertFalse(analysis.blocked)
        self.assertEqual(analysis.plan_authorities, ["execute", "read", "write"])
        handle_step = next(item for item in analysis.steps if item["step_id"] == "handle_ok")
        self.assertEqual(len(handle_step["conditions"]), 2)
        self.assertTrue(all(item["status"] == "exact" for item in handle_step["conditions"]))

    def test_trial_python_read_to_write_is_explicitly_mapper_required_not_exact(self) -> None:
        read_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 02 — Read Text File")
        write_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 03 — Write Text File")

        candidates = propose_skill_leaf_bindings(read_skill, write_skill)
        text_candidates = [
            item
            for item in candidates
            if item.source_path == "/d/result" and item.target_path == "/a/text"
        ]

        self.assertEqual(len(text_candidates), 1)
        self.assertEqual(text_candidates[0].status, "mapper_required")
        self.assertIn("generic semantic label", text_candidates[0].reason)

    def test_execute_skill_composition_plan_feeds_output_into_input_via_exact_mapping(self) -> None:
        source = self._compiled_ir(
            _ability_document(
                title="Emit Text",
                inputs={},
                outputs={"text": "text output"},
                normalization={
                    "regions": {
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
                        }
                    }
                },
            )
        )
        target = self._compiled_ir(
            _ability_document(
                title="Consume Text",
                inputs={"text": "text input"},
                outputs={"status": "status output"},
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
                        }
                    }
                },
            )
        )
        seen_payloads: list[tuple[str, dict[str, object]]] = []

        def invoker(step_id: str, _skill_ir: dict[str, object], payload: dict[str, object]) -> object:
            seen_payloads.append((step_id, dict(payload)))
            if step_id == "emit":
                return {"text": "hello world"}
            if step_id == "consume":
                return {"status": f"consumed:{payload['text']}"}
            raise AssertionError(step_id)

        result = execute_skill_composition_plan(
            [
                SkillCompositionStep(step_id="emit", skill=source),
                SkillCompositionStep(
                    step_id="consume",
                    skill=target,
                    bindings=(
                        SkillCompositionBinding(
                            target_region="a",
                            target_path="/a/text",
                            source_step_id="emit",
                            source_region="d",
                            source_path="/d/text",
                        ),
                    ),
                ),
            ],
            invoker=invoker,
        )

        self.assertEqual(seen_payloads, [("emit", {}), ("consume", {"text": "hello world"})])
        self.assertEqual(result.final_outputs_by_step["consume"], {"status": "consumed:hello world"})
        consume_record = next(item for item in result.steps if item["step_id"] == "consume")
        self.assertEqual(consume_record["binding_receipts"][0]["mapper_kind"], "identity")
        self.assertEqual(consume_record["binding_receipts"][0]["mapped_value"], "hello world")

    def test_execute_skill_composition_plan_uses_explicit_rename_mapper_for_trial_skills(self) -> None:
        read_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 02 — Read Text File")
        write_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 03 — Write Text File")
        seen_payloads: list[tuple[str, dict[str, object]]] = []

        def invoker(step_id: str, _skill_ir: dict[str, object], payload: dict[str, object]) -> object:
            seen_payloads.append((step_id, dict(payload)))
            if step_id == "read":
                return {"result": "hello from read"}
            if step_id == "write":
                self.assertEqual(payload["mount"], "skill_tmp")
                self.assertEqual(payload["relative_path"], "copied.txt")
                self.assertEqual(payload["text"], "hello from read")
                return {"result": "written"}
            raise AssertionError(step_id)

        result = execute_skill_composition_plan(
            [
                SkillCompositionStep(
                    step_id="read",
                    skill=read_skill,
                    bindings=(
                        SkillCompositionBinding(target_region="a", target_path="/a/mount", source_root_name="mount", source_root_region="a"),
                        SkillCompositionBinding(target_region="a", target_path="/a/relative_path", source_root_name="relative_path", source_root_region="a"),
                    ),
                ),
                SkillCompositionStep(
                    step_id="write",
                    skill=write_skill,
                    bindings=(
                        SkillCompositionBinding(target_region="a", target_path="/a/mount", source_root_name="write_mount", source_root_region="a"),
                        SkillCompositionBinding(target_region="a", target_path="/a/relative_path", constant_value="copied.txt", source_region="a"),
                        SkillCompositionBinding(
                            target_region="a",
                            target_path="/a/text",
                            source_step_id="read",
                            source_region="d",
                            source_path="/d/result",
                            mapper_kind="rename",
                        ),
                    ),
                ),
            ],
            invoker=invoker,
            root_inputs={
                "mount": "skill_input",
                "relative_path": "trials/python/README.md",
                "write_mount": "skill_tmp",
            },
        )

        self.assertEqual(seen_payloads[0][1], {"mount": "skill_input", "relative_path": "trials/python/README.md"})
        self.assertEqual(seen_payloads[1][1]["text"], "hello from read")
        write_record = next(item for item in result.steps if item["step_id"] == "write")
        text_binding = next(item for item in write_record["binding_receipts"] if item["target_path"] == "/a/text")
        self.assertEqual(text_binding["mapper_kind"], "rename")
        self.assertEqual(text_binding["mapped_value"], "hello from read")

    def test_execute_skill_composition_plan_accepts_mapping_steps_and_mapping_mapper_specs(self) -> None:
        read_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 02 — Read Text File")
        write_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 03 — Write Text File")
        seen_payloads: list[tuple[str, dict[str, object]]] = []

        def invoker(step_id: str, _skill_ir: dict[str, object], payload: dict[str, object]) -> object:
            seen_payloads.append((step_id, dict(payload)))
            if step_id == "read":
                return {"result": "hello from dict plan"}
            if step_id == "write":
                self.assertEqual(payload["text"], "hello from dict plan")
                return {"result": "written from dict plan"}
            raise AssertionError(step_id)

        result = execute_skill_composition_plan(
            [
                {
                    "step_id": "read",
                    "skill": read_skill,
                    "bindings": [
                        {"target_region": "a", "target_path": "/a/mount", "source_root_name": "mount", "source_root_region": "a"},
                        {"target_region": "a", "target_path": "/a/relative_path", "source_root_name": "relative_path", "source_root_region": "a"},
                    ],
                },
                {
                    "step_id": "write",
                    "skill": write_skill,
                    "bindings": [
                        {"target_region": "a", "target_path": "/a/mount", "source_root_name": "write_mount", "source_root_region": "a"},
                        {"target_region": "a", "target_path": "/a/relative_path", "constant_value": "copied.txt", "source_region": "a"},
                        {
                            "target_region": "a",
                            "target_path": "/a/text",
                            "source_step_id": "read",
                            "source_region": "d",
                            "source_path": "/d/result",
                            "mapper": {"kind": "rename"},
                        },
                    ],
                },
            ],
            invoker=invoker,
            root_inputs={
                "mount": "skill_input",
                "relative_path": "trials/python/README.md",
                "write_mount": "skill_tmp",
            },
        )

        self.assertEqual(seen_payloads[1][1]["text"], "hello from dict plan")
        write_record = next(item for item in result.steps if item["step_id"] == "write")
        text_binding = next(item for item in write_record["binding_receipts"] if item["target_path"] == "/a/text")
        self.assertEqual(text_binding["mapper_kind"], "rename")
        self.assertEqual(text_binding["mapped_value"], "hello from dict plan")

    def test_execute_skill_composition_plan_projects_field_from_generic_result_leaf(self) -> None:
        read_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 02 — Read Text File")
        write_skill = self._trial_ability("trials/python/skill.yaml", "Python Commands 03 — Write Text File")
        seen_payloads: list[tuple[str, dict[str, object]]] = []

        def invoker(step_id: str, _skill_ir: dict[str, object], payload: dict[str, object]) -> object:
            seen_payloads.append((step_id, dict(payload)))
            if step_id == "read":
                return {
                    "result": {
                        "status": "read",
                        "mount": "main",
                        "relative_path": "src/demo.py",
                        "text": "hello from projected field",
                    }
                }
            if step_id == "write":
                self.assertEqual(payload["text"], "hello from projected field")
                return {"result": "written from projected field"}
            raise AssertionError(step_id)

        result = execute_skill_composition_plan(
            [
                SkillCompositionStep(
                    step_id="read",
                    skill=read_skill,
                    bindings=(
                        SkillCompositionBinding(target_region="a", target_path="/a/mount", source_root_name="mount", source_root_region="a"),
                        SkillCompositionBinding(target_region="a", target_path="/a/relative_path", source_root_name="relative_path", source_root_region="a"),
                    ),
                ),
                SkillCompositionStep(
                    step_id="write",
                    skill=write_skill,
                    bindings=(
                        SkillCompositionBinding(target_region="a", target_path="/a/mount", source_root_name="write_mount", source_root_region="a"),
                        SkillCompositionBinding(target_region="a", target_path="/a/relative_path", constant_value="copied.txt", source_region="a"),
                        SkillCompositionBinding(
                            target_region="a",
                            target_path="/a/text",
                            source_step_id="read",
                            source_region="d",
                            source_path="/d/result",
                            mapper=SkillCompositionMapper(kind="project_field", field="text"),
                        ),
                    ),
                ),
            ],
            invoker=invoker,
            root_inputs={
                "mount": "main",
                "relative_path": "src/demo.py",
                "write_mount": "skill_tmp",
            },
        )

        self.assertEqual(seen_payloads[1][1]["text"], "hello from projected field")
        write_record = next(item for item in result.steps if item["step_id"] == "write")
        text_binding = next(item for item in write_record["binding_receipts"] if item["target_path"] == "/a/text")
        self.assertEqual(text_binding["mapper_kind"], "project_field")
        self.assertEqual(text_binding["mapper_field"], "text")
        self.assertEqual(text_binding["mapped_value"], "hello from projected field")

    def test_execute_skill_composition_plan_prefers_explicit_mapper_object_over_legacy_mapper_kind(self) -> None:
        source = self._compiled_ir(
            _ability_document(
                title="Emit Lines",
                inputs={},
                outputs={"lines": "line outputs"},
                normalization={
                    "regions": {
                        "d": {
                            "boundary_term": "d*",
                            "leaves": [
                                {
                                    "region": "d*",
                                    "path": "/d/lines",
                                    "carrier_kind": "value",
                                    "data_type": "Strings",
                                    "semantic_label": "lines",
                                    "value": ["a", "b"],
                                    "leaf_class": "collection",
                                }
                            ],
                        }
                    }
                },
            )
        )
        target = self._compiled_ir(
            _ability_document(
                title="Consume Line",
                inputs={"line": "line input"},
                outputs={"status": "status output"},
                normalization={
                    "regions": {
                        "a": {
                            "boundary_term": "a*",
                            "leaves": [
                                {
                                    "region": "a*",
                                    "path": "/a/line",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "line",
                                    "value": "line input",
                                    "leaf_class": "scalar",
                                }
                            ],
                        }
                    }
                },
            )
        )

        result = execute_skill_composition_plan(
            [
                SkillCompositionStep(step_id="emit", skill=source),
                SkillCompositionStep(
                    step_id="consume",
                    skill=target,
                    bindings=(
                        SkillCompositionBinding(
                            target_region="a",
                            target_path="/a/line",
                            source_step_id="emit",
                            source_region="d",
                            source_path="/d/lines",
                            mapper=SkillCompositionMapper(kind="first_item"),
                            mapper_kind="identity",
                        ),
                    ),
                ),
            ],
            invoker=lambda step_id, _skill_ir, _payload: {"lines": ["first", "second"]} if step_id == "emit" else {"status": "ok"},
        )

        consume_record = next(item for item in result.steps if item["step_id"] == "consume")
        self.assertEqual(consume_record["binding_receipts"][0]["mapper_kind"], "first_item")
        self.assertEqual(consume_record["binding_receipts"][0]["mapped_value"], "first")

    def test_execute_skill_composition_plan_skips_branch_when_condition_fails(self) -> None:
        decide_skill = self._compiled_ir(
            _ability_document(
                title="Decide Status",
                inputs={},
                outputs={"status": "status output"},
                normalization={
                    "regions": {
                        "d": {
                            "boundary_term": "d*",
                            "leaves": [
                                {
                                    "region": "d*",
                                    "path": "/d/status",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "status",
                                    "value": "status output",
                                    "leaf_class": "scalar",
                                }
                            ],
                        }
                    }
                },
            )
        )
        branch_skill = self._compiled_ir(
            _ability_document(
                title="Handle Ok",
                inputs={"status": "status input"},
                outputs={"result": "result output"},
                normalization={
                    "regions": {
                        "a": {
                            "boundary_term": "a*",
                            "leaves": [
                                {
                                    "region": "a*",
                                    "path": "/a/status",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "status",
                                    "value": "status input",
                                    "leaf_class": "scalar",
                                }
                            ],
                        }
                    }
                },
            )
        )
        seen_steps: list[str] = []

        def invoker(step_id: str, _skill_ir: dict[str, object], _payload: dict[str, object]) -> object:
            seen_steps.append(step_id)
            if step_id == "decide":
                return {"status": "error"}
            raise AssertionError(step_id)

        result = execute_skill_composition_plan(
            [
                SkillCompositionStep(step_id="decide", skill=decide_skill),
                SkillCompositionStep(
                    step_id="handle_ok",
                    skill=branch_skill,
                    bindings=(
                        SkillCompositionBinding(
                            target_region="a",
                            target_path="/a/status",
                            source_step_id="decide",
                            source_region="d",
                            source_path="/d/status",
                        ),
                    ),
                    run_if=(
                        SkillCompositionCondition(
                            source_step_id="decide",
                            source_region="d",
                            source_path="/d/status",
                            operator="equals",
                            expected_value="ok",
                        ),
                    ),
                    branch_label="ok",
                ),
            ],
            invoker=invoker,
        )

        self.assertEqual(seen_steps, ["decide"])
        skipped = next(item for item in result.steps if item["step_id"] == "handle_ok")
        self.assertEqual(skipped["status"], "skipped")

    def test_execute_skill_composition_plan_iterates_until_condition_is_met(self) -> None:
        poll_skill = self._compiled_ir(
            _ability_document(
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
            )
        )
        call_count = 0

        def invoker(_step_id: str, _skill_ir: dict[str, object], _payload: dict[str, object]) -> object:
            nonlocal call_count
            call_count += 1
            return {"has_more": call_count < 3}

        result = execute_skill_composition_plan(
            [
                SkillCompositionStep(
                    step_id="poll",
                    skill=poll_skill,
                    iterate_until=(
                        SkillCompositionCondition(
                            source_step_id="poll",
                            source_region="d",
                            source_path="/d/has_more",
                            operator="equals",
                            expected_value=False,
                        ),
                    ),
                )
            ],
            invoker=invoker,
        )

        self.assertEqual(call_count, 3)
        poll_records = [item for item in result.steps if item["step_id"] == "poll"]
        self.assertEqual(len(poll_records), 3)
        self.assertEqual(result.final_outputs_by_step["poll"], {"has_more": False})


if __name__ == "__main__":
    unittest.main()
