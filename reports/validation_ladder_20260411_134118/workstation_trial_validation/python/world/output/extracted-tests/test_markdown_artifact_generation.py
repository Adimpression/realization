# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import unittest
from pathlib import Path
import tempfile

from learning_context import (
    LearningContext,
    load_learning_context,
    load_learning_delta,
    load_learning_source,
    persist_learning_context,
)
from main import (
    BSSCController,
    ProposalGovernanceStatus,
    ProposalObject,
    ProposalType,
    SemanticNode,
    SupplementMode,
    SystemState,
    markdown_learning_encounter_view,
)
from markdown_ir import parse_markdown_document_ir
from semantic_text import titleize_semantic_unit


class MarkdownArtifactGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling setUp.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `setUp()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.controller = BSSCController(SystemState.bootstrap("markdown artifact generation"), llm_policy="off")
        self.node = SemanticNode(id="node_markdown", semantic_unit="learn from markdown", role="root")

    def test_knowledge_artifact_uses_encounter_context_and_strips_prompt_examples(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing knowledge artifact uses encounter context and strips prompt examples.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_knowledge_artifact_uses_encounter_context_and_strips_prompt_examples()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Example Knowledge

## 1. Identify First

If you cannot tell which item you are holding, do not use it yet.

The next step is to identify it from a reliable label or marker:

* the label
* the visible marker

Canonical prompt forms:

* I have two similar items in my hand and cannot tell which is which. What should I do?

Reusable answer pattern:

* do not use it yet
* identify it first
"""
        document = parse_markdown_document_ir(markdown, source_path="example.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("example.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "1. Identify First",
                "semantic_unit": "1. Identify First",
                "question": "What is 1. Identify First?",
                "answer": "If you cannot tell which item you are holding, do not use it yet. Canonical prompt forms: Key points: example prompt",
                "sections": ["1. Identify First"],
            },
        )
        self.assertIsNotNone(artifact)
        content = artifact.content
        self.assertEqual(
            content.get("question"),
            "I have two similar items in my hand and cannot tell which is which. What should I do?",
        )
        answer = str(content.get("answer", "")).lower()
        self.assertIn("do not use it yet", answer)
        self.assertIn("identify it from a reliable label or marker", answer)
        self.assertNotIn("canonical prompt forms", answer)
        self.assertNotIn("reusable answer pattern", answer)

    def test_derive_markdown_current_identity_uses_non_generic_path_segment(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over markdown-learned artifacts, helps with checking that a generic local heading such as `Executable Python relation` repairs to a more semantic parent path segment instead of surviving as the learned identity.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_derive_markdown_current_identity_uses_non_generic_path_segment()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        encounter = {
            "heading": "Executable Python relation",
            "path": [
                "Launch Browser At Specific URL",
                "Executable Python relation",
            ],
            "paragraphs": [],
            "bullets": [],
        }
        current_identity = self.controller.derive_markdown_current_identity_from_encounter(
            encounter=encounter,
            proposed_title="Launch Browser At Specific URL / Executable Python Relation",
        )
        self.assertEqual(current_identity, titleize_semantic_unit("Launch Browser At Specific URL"))

    def test_markdown_learning_artifact_uses_formal_title_as_identity_source(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning artifact uses formal title as identity source.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_learning_artifact_uses_formal_title_as_identity_source()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Cylinder Measures

## Total Surface Area

The total surface area of a cylinder can be computed from radius and height.
"""
        document = parse_markdown_document_ir(markdown, source_path="cylinder.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("cylinder.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "Geometry / Cylinder / Total Surface Area From Radius And Height",
                "semantic_unit": "Total surface area of a cylinder from radius and height",
                "question": "What is the total surface area of a cylinder given radius and height?",
                "answer": "Use the cylinder surface-area formula with radius and height.",
                "sections": ["Total Surface Area"],
            },
        )
        self.assertIsNotNone(artifact)
        structured = artifact.content.get("structured_learning", {})
        self.assertEqual(
            structured.get("title_identity"),
            "Geometry / Cylinder / Total Surface Area From Radius And Height",
        )
        self.assertEqual(
            structured.get("title_depth_prefixes"),
            [
                "Geometry",
                "Geometry / Cylinder",
                "Geometry / Cylinder / Total Surface Area From Radius And Height",
            ],
        )
        self.assertEqual(
            artifact.content.get("title_current_identity"),
            "",
        )

    def test_markdown_learning_ability_avoids_doc_title_collision_with_framework_child_identity(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over markdown-learned executable abilities, helps with checking that the actual markdown-learning pipeline keeps a reusable Python ability distinct from the document-level family title instead of collapsing it onto the same identity.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_learning_ability_avoids_doc_title_collision_with_framework_child_identity()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Device User Capabilities 01 — Launch Browser At Specific URL

## Executable Python relation

This capability is a parameterized executable template and should be learned as an ability artifact.

The reusable function name is `main`.

The reusable function signature is `main(url: str, *, browser: str = "Google Chrome", __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`.

Within `main`:

* import `subprocess`
* run `subprocess.run(["open", "-a", browser, url], check=True)`
* return `{"status": "opened", "browser": browser, "url": url}`
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "browser.md"
            path.write_text(markdown, encoding="utf-8")
            self.controller.state.controller_features.supported_executors = ["bash", "python3"]
            report = self.controller.learn_from_markdown_document(path, max_artifacts=6)
        ability_titles = [
            str(item.get("title", "")).strip()
            for item in report.get("learned_artifacts", [])
            if item.get("artifact_type") == "ability"
        ]
        self.assertIn(
            "Device User Capabilities 01 — Launch Browser At Specific URL / Python Function",
            ability_titles,
        )

    def test_markdown_expression_ability_normalizes_equation_surface_for_execution(self) -> None:
        """
        High Level Purpose:
            In circumstances like markdown-learned executable abilities that surface equations as identities, helps with proving that an equation-shaped compute expression is normalized into an executable form while preserving the output field.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_markdown_expression_ability_normalizes_equation_surface_for_execution()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Newton's Laws of Motion

## Second Law: Law of Acceleration

The reusable formula is:

* input: m
* input: a
* output: F

$$ F = m * a $$
"""
        document = parse_markdown_document_ir(markdown, source_path="newton.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("newton.md"),
            payload={
                "artifact_type": "ability",
                "title": "Newton's Laws of Motion / Force-Mass-Acceleration Relationship",
                "semantic_unit": "Force from mass and acceleration",
                "question": "How do you calculate F from m, a?",
                "sections": ["Second Law: Law of Acceleration"],
                "content": {
                    "compute_expression": "F = m * a",
                    "output_field": "F",
                    "input_contract": {"m": "number", "a": "number"},
                    "output_contract": {"F": "number"},
                },
            },
        )
        self.assertIsNotNone(artifact)
        self.assertEqual(artifact.content.get("compute_expression"), "m * a")
        self.assertEqual(artifact.content.get("output_field"), "F")
        self.assertIn("EXPRESSION = 'm * a'", str(artifact.content.get("python_script", "")))

        execution = self.controller.execute_function_artifact(
            artifact,
            semantic_unit="Calculate force for mass=3 and acceleration=4.",
        )
        self.assertTrue(execution.ok)
        self.assertEqual(execution.answer, "12")

    def test_markdown_learning_prompt_allows_minimally_sufficient_segmented_titles(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning prompt allows minimally sufficient segmented titles.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_learning_prompt_allows_minimally_sufficient_segmented_titles()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Cylinder Measures

## Total Surface Area

Use radius and height to compute total surface area.
"""
        document = parse_markdown_document_ir(markdown, source_path="cylinder.md")
        captured: dict[str, str] = {}

        def fake_request_proposal(**kwargs):
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake request proposal.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

            Example Input Output:
                Input: `fake_request_proposal()`
                Output: 'F = m * a'

            Args:
                **kwargs: Additional keyword arguments forwarded by the caller.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            captured["instructions"] = kwargs["instructions"]
            return ProposalObject(
                id="proposal-markdown-learning",
                proposal_type=ProposalType.MARKDOWN_LEARNING,
                target_scope=document.title,
                originating_not_id=self.node.id,
                mode=SupplementMode.DEEP,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload=kwargs["fallback_payload"],
                source="heuristic",
            )

        self.controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        self.controller.propose_markdown_learning(self.node, document, max_artifacts=4)

        instructions = captured["instructions"]
        self.assertIn("title is the final formal semantic identity of the artifact", instructions)
        self.assertIn("Bounded structural ir fragments", instructions)
        self.assertIn("title_broader_category", instructions)
        self.assertIn("title_current_identity", instructions)
        self.assertIn("title_downward_decomposition", instructions)
        self.assertIn("broader category", instructions)
        self.assertIn("minimal sufficient determination", instructions)
        self.assertIn("title_similies", instructions)
        self.assertIn("question_title_separation", instructions)
        self.assertIn("related_titles", instructions)
        self.assertIn("organizational or meta", instructions)
        self.assertIn("one primary semantic burden", instructions)
        self.assertIn("ontological commitments", instructions)
        self.assertIn("broader reusable substrate", instructions)

    def test_markdown_ingestion_bootstrap_skips_root_not_elaboration_before_ir_learning(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown ingestion bootstrap skips root not elaboration before ir learning.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_ingestion_bootstrap_skips_root_not_elaboration_before_ir_learning()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Cylinder Measures

## Total Surface Area

Use radius and height to compute total surface area.
"""
        state = SystemState.bootstrap(
            "Learn from markdown: cylinder.md",
            bootstrap_mode="markdown_ingestion",
        )
        controller = BSSCController(state, llm_policy="off")
        captured: list[ProposalType] = []

        class _StopAfterFirstProposal(RuntimeError):
            pass

        def fake_request_proposal(**kwargs):
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake request proposal.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

            Example Input Output:
                Input: `fake_request_proposal()`
                Output: 'F = m * a'

            Args:
                **kwargs: Additional keyword arguments forwarded by the caller.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            captured.append(kwargs["proposal_type"])
            raise _StopAfterFirstProposal

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        with tempfile.TemporaryDirectory(prefix="markdown_ingestion_bootstrap_") as tempdir:
            markdown_path = Path(tempdir) / "cylinder.md"
            markdown_path.write_text(markdown)
            with self.assertRaises(_StopAfterFirstProposal):
                controller.learn_from_markdown_document(markdown_path, max_artifacts=4)

        self.assertEqual(captured, [ProposalType.MARKDOWN_LEARNING])

    def test_markdown_learning_artifact_composes_title_from_broader_category_and_downward_segments(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning artifact composes title from broader category and downward segments.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_learning_artifact_composes_title_from_broader_category_and_downward_segments()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Cylinder Measures

## Total Surface Area

Use radius and height to compute total surface area.
"""
        document = parse_markdown_document_ir(markdown, source_path="cylinder.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("cylinder.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "2. Total Surface Area",
                "title_broader_category": "Geometry",
                "title_current_identity": "Cylinder Surface Measure",
                "title_downward_decomposition": [
                    "Total Surface Area From Radius And Height",
                ],
                "title_similies": [
                    "Cylinder total surface area from radius and height",
                    "Surface area of a cylinder from radius and height",
                ],
                "title_construction_rationale": "Ground with geometry, identify the cylinder-surface family, then narrow to the exact measure from the required inputs.",
                "title_collision_rationale": "Avoids collision with broader cylinder-measure identities.",
                "question_title_separation": "The title is the reusable identity; the question is the caller-facing invocation.",
                "semantic_unit": "Total surface area of a cylinder from radius and height",
                "question": "What is the total surface area of a cylinder given radius and height?",
                "answer": "Use the cylinder surface-area formula with radius and height.",
                "sections": ["Total Surface Area"],
            },
        )
        self.assertIsNotNone(artifact)
        self.assertEqual(
            artifact.title,
            "Geometry / Cylinder Surface Measure / Total Surface Area From Radius And Height",
        )
        self.assertEqual(artifact.content.get("title_broader_category"), "Geometry")
        self.assertEqual(artifact.content.get("title_current_identity"), "Cylinder Surface Measure")
        self.assertEqual(
            artifact.content.get("title_downward_decomposition"),
            ["Total Surface Area From Radius And Height"],
        )
        self.assertIn(
            "Cylinder total surface area from radius and height",
            artifact.content.get("aliases", []),
        )

    def test_markdown_learning_batches_store_persistence(self) -> None:
        """
        High Level Purpose:
            In circumstances like markdown-learning persistence across multiple learned artifacts, helps with proving that the pipeline uses batched store persistence instead of reconnecting and indexing one artifact at a time.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity while preserving bounded persistence overhead.

        Example Input Output:
            Input: `test_markdown_learning_batches_store_persistence()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """

        class _BatchOnlyArtifactStore:
            def __init__(self) -> None:
                self.persist_artifacts_calls: list[tuple[tuple[str, ...], str]] = []

            def persist_artifacts(self, artifacts, *, run_id: str = "artifact_import") -> dict[str, object]:
                artifact_list = list(artifacts)
                self.persist_artifacts_calls.append(
                    (tuple(str(getattr(item, "id", "")).strip() for item in artifact_list), run_id)
                )
                return {
                    "status": "persisted",
                    "reason": "",
                    "timings": {"total_seconds": 0.0},
                    "reports": [
                        {
                            "artifact_id": str(getattr(item, "id", "")).strip(),
                            "status": "persisted",
                        }
                        for item in artifact_list
                    ],
                }

            def persist_artifact(self, artifact, *, run_id: str = "artifact_import") -> dict[str, object]:
                raise AssertionError("markdown learning should batch persistence through persist_artifacts")

        markdown = """# Newton's Laws of Motion

Bodies remain at rest or in uniform motion unless acted upon by a net force.

## First Law

Bodies remain at rest or in uniform motion unless acted upon by a net force.

## Second Law

Force is proportional to mass and acceleration.
"""
        store = _BatchOnlyArtifactStore()
        previous_store = self.controller.artifact_store
        previous_relation_step = self.controller.apply_markdown_batch_relations
        try:
            self.controller.artifact_store = store
            self.controller.apply_markdown_batch_relations = lambda artifacts: []  # type: ignore[method-assign]
            with tempfile.TemporaryDirectory(prefix="markdown_batch_persist_") as tmpdir:
                markdown_path = Path(tmpdir) / "newton.md"
                markdown_path.write_text(markdown, encoding="utf-8")
                result = self.controller.learn_from_markdown_document(markdown_path, max_artifacts=6)
        finally:
            self.controller.artifact_store = previous_store
            self.controller.apply_markdown_batch_relations = previous_relation_step

        self.assertEqual(len(store.persist_artifacts_calls), 1)
        persisted_ids, run_id = store.persist_artifacts_calls[0]
        self.assertEqual(run_id, self.controller.state.run_id)
        learned_ids = tuple(
            str(item.get("artifact_id", "")).strip()
            for item in result.get("learned_artifacts", [])
            if str(item.get("artifact_id", "")).strip()
        )
        self.assertEqual(persisted_ids, learned_ids)
        self.assertEqual(len(result.get("artifact_persistence", [])), len(learned_ids))

    def test_markdown_learning_persists_source_delta_and_learning_context(self) -> None:
        markdown = """# Newton's Laws of Motion

## First Law

Bodies remain at rest or in uniform motion unless acted upon by a net force.

## Second Law

Force is proportional to mass and acceleration.
"""

        with tempfile.TemporaryDirectory(prefix="markdown_learning_context_") as tmpdir:
            markdown_path = Path(tmpdir) / "newton.md"
            markdown_path.write_text(markdown, encoding="utf-8")
            result = self.controller.learn_from_markdown_document(markdown_path, max_artifacts=6)

            context_report = dict(result.get("learning_context", {}))
            subject_id = str(context_report.get("subject_id", "")).strip()
            source_id = str(context_report.get("source_id", "")).strip()
            delta_id = str(context_report.get("delta_id", "")).strip()

            self.assertEqual(subject_id, "newton-s-laws-of-motion")
            self.assertTrue(Path(str(context_report.get("context_path", ""))).is_file())
            self.assertTrue(Path(str(context_report.get("source_record_path", ""))).is_file())
            self.assertTrue(Path(str(context_report.get("delta_path", ""))).is_file())

            context = load_learning_context(Path(tmpdir), subject_id)
            source = load_learning_source(Path(tmpdir), subject_id, source_id)
            delta = load_learning_delta(Path(tmpdir), subject_id, delta_id)

            self.assertEqual(context.canonical_title, "Newton's Laws of Motion")
            self.assertEqual(source.title, "Newton's Laws of Motion")
            self.assertEqual(source.source_ref, str(markdown_path.resolve()))
            self.assertEqual(delta.evidence_refs, (source_id,))
            self.assertGreaterEqual(len(context.units), 1)
            self.assertEqual(set(delta.deprecated_unit_ids), set())
            self.assertEqual(len(delta.operations), len(delta.proposed_units))
            self.assertTrue(all(item.operation_kind == "initiate" for item in delta.operations))
            self.assertEqual(
                {item.proposed_unit_ids for item in delta.operations},
                {(unit.unit_id,) for unit in delta.proposed_units},
            )

    def test_markdown_learning_honors_explicit_subject_metadata(self) -> None:
        markdown = """# Motion Notes

- Subject: Kinematics
- Subject Family: Physics
- Aliases: Motion Notes; Equations of Motion
- Summary: Core motion relations.

## Velocity

Velocity is the rate of change of position.
"""

        with tempfile.TemporaryDirectory(prefix="markdown_learning_subject_metadata_") as tmpdir:
            markdown_path = Path(tmpdir) / "motion_notes.md"
            markdown_path.write_text(markdown, encoding="utf-8")

            result = self.controller.learn_from_markdown_document(markdown_path, max_artifacts=4)

            context_report = dict(result.get("learning_context", {}))
            self.assertEqual(context_report.get("subject_id"), "kinematics")
            self.assertEqual(context_report.get("canonical_title"), "Kinematics")
            self.assertEqual(context_report.get("subject_family"), "Physics")

            context = load_learning_context(Path(tmpdir), "kinematics")
            self.assertEqual(context.canonical_title, "Kinematics")
            self.assertEqual(context.subject_family, "Physics")
            self.assertEqual(context.summary, "Core motion relations.")
            self.assertIn("Motion Notes", context.aliases)
            self.assertIn("Equations of Motion", context.aliases)

    def test_markdown_learning_reuses_existing_context_on_exact_alias_match(self) -> None:
        with tempfile.TemporaryDirectory(prefix="markdown_learning_existing_subject_") as tmpdir:
            root = Path(tmpdir)
            persist_learning_context(
                root,
                LearningContext(
                    subject_id="kinematics",
                    canonical_title="Kinematics",
                    aliases=("Kinematics", "Motion Notes"),
                    subject_family="Physics",
                    governance_status="active",
                ),
            )
            markdown_path = root / "motion_notes.md"
            markdown_path.write_text(
                """# Motion Notes

## Velocity

Velocity is the rate of change of position.
""",
                encoding="utf-8",
            )

            result = self.controller.learn_from_markdown_document(markdown_path, max_artifacts=4)

            context_report = dict(result.get("learning_context", {}))
            self.assertEqual(context_report.get("subject_id"), "kinematics")
            self.assertEqual(context_report.get("canonical_title"), "Kinematics")
            self.assertEqual(context_report.get("matched_existing_subject_id"), "kinematics")

            context = load_learning_context(root, "kinematics")
            self.assertEqual(context.canonical_title, "Kinematics")
            self.assertEqual(context.subject_family, "Physics")
            self.assertEqual(len(context.applied_delta_ids), 1)

    def test_reusable_substrate_heading_prefers_relation_family_identity(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that a generic reusable-substrate heading is repaired into the reusable family identity named by the encounter itself.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_reusable_substrate_heading_prefers_relation_family_identity()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        source = Path("/Users/ravindranathakila/service/realized/trials/chemistry/02_LEARN_CHEMISTRY_RELATIONS_MOLE.md")
        document = parse_markdown_document_ir(source.read_text(), source_path=str(source))
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=source,
            payload={
                "artifact_type": "knowledge",
                "title": "1. Reusable substrate",
                "semantic_unit": "Reusable substrate",
                "question": "What is reusable substrate?",
                "answer": "Grouped counting is the broader reusable substrate.",
                "sections": ["1. Reusable substrate"],
                "encounter_id": "cluster_1",
            },
        )
        self.assertIsNotNone(artifact)
        self.assertEqual(
            artifact.title,
            "Chemistry Relations 02 — Mole as Counting Conversion / Grouped Counting",
        )
        self.assertEqual(artifact.content.get("title_current_identity"), "Grouped Counting")

    def test_prolog_mode_synthesizes_chemistry_formal_identity_and_executes(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that Prolog mode can synthesize a structural chemistry identity from a readable title and then execute the learned ability from a normal prompt.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_prolog_mode_synthesizes_chemistry_formal_identity_and_executes()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        previous_mode = os.environ.get("BSSC_TITLE_REPRESENTATION")
        os.environ["BSSC_TITLE_REPRESENTATION"] = "prolog"
        try:
            source = Path("/Users/ravindranathakila/service/realized/trials/chemistry/02_LEARN_CHEMISTRY_RELATIONS_MOLE.md")
            document = parse_markdown_document_ir(source.read_text(), source_path=str(source))
            artifact = self.controller.build_markdown_learning_artifact(
                node=self.node,
                document=document,
                source_path=source,
                payload={
                    "artifact_type": "ability",
                    "title": "2. Particles from moles",
                    "semantic_unit": "Particles from moles",
                    "question": "How do you calculate N from n and N_A?",
                    "question_title_separation": "The title is the reusable identity; the question is the caller-facing invocation.",
                    "sections": ["2. Particles from moles"],
                    "encounter_id": "cluster_2",
                    "content": {},
                },
            )
        finally:
            if previous_mode is None:
                os.environ.pop("BSSC_TITLE_REPRESENTATION", None)
            else:
                os.environ["BSSC_TITLE_REPRESENTATION"] = previous_mode
        self.assertIsNotNone(artifact)
        self.assertEqual(artifact.content.get("input_contract"), {"n": "number", "N_A": "number"})
        self.assertEqual(artifact.content.get("output_contract"), {"N": "number"})
        self.assertEqual(artifact.content.get("compute_expression"), "n * N_A")
        formal_title_identity = str(artifact.content.get("formal_title_identity", "")).strip()
        self.assertTrue(formal_title_identity.startswith("chemistry_relation_02_mole_as_count_conversion:"))
        self.assertIn("particle_from_mole(", formal_title_identity)
        execution = self.controller.execute_function_artifact(
            artifact,
            semantic_unit="Calculate N from n=2 and N_A=3.",
        )
        self.assertTrue(execution.ok)
        self.assertEqual(execution.answer, "6")

    def test_markdown_learning_adds_direct_expression_ability_even_when_llm_payload_is_knowledge_only(self) -> None:
        """
        High Level Purpose:
            In circumstances like markdown learning over equation-bearing encounters, helps with proving that the controller deterministically emits an executable ability artifact from the parsed encounter even if the LLM only returns a knowledge-shaped payload.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_learning_adds_direct_expression_ability_even_when_llm_payload_is_knowledge_only()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Chemistry Relations 08 — Ideal Gas State Relation

## Pressure from amount, temperature, and volume

* input: n
* input: R
* input: T
* input: V
* output: P

$$ P = n * R * T / V $$
"""
        previous_sqlite_path = os.environ.get("STATE_SQLITE_PATH")
        try:
            with tempfile.TemporaryDirectory(prefix="markdown_direct_expression_") as tempdir:
                os.environ["STATE_SQLITE_PATH"] = str(Path(tempdir) / "state.sqlite3")
                markdown_path = Path(tempdir) / "ideal_gas.md"
                markdown_path.write_text(markdown)
                document = parse_markdown_document_ir(markdown, source_path=str(markdown_path))

            def fake_markdown_learning(_node, _document, *, max_artifacts):
                """
                High Level Purpose:
                    In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake markdown learning.

                Reference to Theory:
                    Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

                Example Input Output:
                    Input: `fake_markdown_learning(_node=SemanticNode(id='node_markdown', semantic_unit='learn from markdown'), _document=MarkdownDocumentIR(title='Chemistry Relations 08 — Ideal Gas State Relation'), max_artifacts=4)`
                    Output: ProposalObject(id='proposal-markdown-learning', proposal_type='MARKDOWN_LEARNING')

                Args:
                    _node: Value for `_node` used by `fake_markdown_learning`. Expected type: `Any`.
                    _document: Value for `_document` used by `fake_markdown_learning`. Expected type: `Any`.
                    max_artifacts: Value for `max_artifacts` used by `fake_markdown_learning`. Expected type: `int`.

                Returns:
                    Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
                """
                return ProposalObject(
                    id="proposal-markdown-learning",
                    proposal_type=ProposalType.MARKDOWN_LEARNING,
                    target_scope=_document.title,
                    originating_not_id=self.node.id,
                    mode=SupplementMode.DEEP,
                    prompt_state_reference="test",
                    revision_count=0,
                    governance_status=ProposalGovernanceStatus.SUGGESTED,
                    payload={
                        "artifacts": [
                            {
                                "artifact_type": "knowledge",
                                "title": "Pressure from amount, temperature, and volume",
                                "semantic_unit": "Pressure from amount, temperature, and volume",
                                "question": "What is pressure from amount, temperature, and volume?",
                                "answer": "Pressure depends on amount, temperature, and volume through the ideal-gas relation.",
                                "sections": ["Pressure from amount, temperature, and volume"],
                                "encounter_id": "cluster_1",
                            }
                        ]
                    },
                    source="heuristic",
                )

            def fake_markdown_ability_learning(_node, _document, *, max_artifacts):
                """
                High Level Purpose:
                    In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake markdown ability learning.

                Reference to Theory:
                    Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

                Example Input Output:
                    Input: `fake_markdown_ability_learning(_node=SemanticNode(id='node_markdown', semantic_unit='learn from markdown'), _document=MarkdownDocumentIR(title='Chemistry Relations 08 — Ideal Gas State Relation'), max_artifacts=4)`
                    Output: ProposalObject(id='proposal-markdown-ability-learning', proposal_type='MARKDOWN_ABILITY_LEARNING')

                Args:
                    _node: Value for `_node` used by `fake_markdown_ability_learning`. Expected type: `Any`.
                    _document: Value for `_document` used by `fake_markdown_ability_learning`. Expected type: `Any`.
                    max_artifacts: Value for `max_artifacts` used by `fake_markdown_ability_learning`. Expected type: `int`.

                Returns:
                    Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
                """
                return ProposalObject(
                    id="proposal-markdown-ability-learning",
                    proposal_type=ProposalType.MARKDOWN_ABILITY_LEARNING,
                    target_scope=_document.title,
                    originating_not_id=self.node.id,
                    mode=SupplementMode.DEEP,
                    prompt_state_reference="test",
                    revision_count=0,
                    governance_status=ProposalGovernanceStatus.SUGGESTED,
                    payload={"encounters": markdown_learning_encounter_view(_document)},
                    source="heuristic",
                )

            def fake_markdown_functionalization(_node, _document, *, encounters, max_artifacts):
                """
                High Level Purpose:
                    In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake markdown functionalization.

                Reference to Theory:
                    Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

                Example Input Output:
                    Input: `fake_markdown_functionalization(_node=SemanticNode(id='node_markdown', semantic_unit='learn from markdown'), _document=MarkdownDocumentIR(title='Chemistry Relations 08 — Ideal Gas State Relation'), encounters=[{'encounter_id': 'cluster_1'}], max_artifacts=4)`
                    Output: ProposalObject(id='proposal-markdown-functionalization', proposal_type='MARKDOWN_FUNCTIONALIZATION')

                Args:
                    _node: Value for `_node` used by `fake_markdown_functionalization`. Expected type: `Any`.
                    _document: Value for `_document` used by `fake_markdown_functionalization`. Expected type: `Any`.
                    encounters: Value for `encounters` used by `fake_markdown_functionalization`. Expected type: `Any`.
                    max_artifacts: Value for `max_artifacts` used by `fake_markdown_functionalization`. Expected type: `int`.

                Returns:
                    Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
                """
                return ProposalObject(
                    id="proposal-markdown-functionalization",
                    proposal_type=ProposalType.MARKDOWN_FUNCTIONALIZATION,
                    target_scope=_document.title,
                    originating_not_id=self.node.id,
                    mode=SupplementMode.DEEP,
                    prompt_state_reference="test",
                    revision_count=0,
                    governance_status=ProposalGovernanceStatus.SUGGESTED,
                    payload={"artifacts": []},
                    source="heuristic",
                )

                self.controller.propose_markdown_learning = fake_markdown_learning  # type: ignore[method-assign]
                self.controller.propose_markdown_ability_learning = fake_markdown_ability_learning  # type: ignore[method-assign]
                self.controller.propose_markdown_functionalization = fake_markdown_functionalization  # type: ignore[method-assign]

                result = self.controller.learn_from_markdown_document(markdown_path, max_artifacts=4)
                learned_abilities = [
                    artifact
                    for artifact in self.controller.state.learned_artifacts.values()
                    if str(artifact.artifact_type) == "ability"
                ]
                self.assertTrue(learned_abilities)
                pressure_ability = next(
                    artifact
                    for artifact in learned_abilities
                    if artifact.content.get("output_field") == "P"
                )
                self.assertEqual(pressure_ability.content.get("compute_expression"), "n * R * T / V")
                self.assertIn(pressure_ability.id, [item["artifact_id"] for item in result["learned_artifacts"]])
        finally:
            if previous_sqlite_path is None:
                os.environ.pop("STATE_SQLITE_PATH", None)
            else:
                os.environ["STATE_SQLITE_PATH"] = previous_sqlite_path

    def test_markdown_learning_prefers_encounter_expression_when_llm_formula_is_malformed(self) -> None:
        """
        High Level Purpose:
            In circumstances like markdown-learned executable math laws whose LLM proposal preserves the right symbols but corrupts exponent syntax, helps with proving that the controller trusts the encounter's direct executable relation over the malformed proposal surface.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_learning_prefers_encounter_expression_when_llm_formula_is_malformed()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        source = Path("/Users/ravindranathakila/service/realized/trials/GAIN_PYTHOGOREAN_THEORM.md")
        document = parse_markdown_document_ir(source.read_text(), source_path=str(source))
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=source,
            payload={
                "artifact_type": "ability",
                "title": "2. The core rule",
                "semantic_unit": "The core rule",
                "question": "What is the length of the hypotenuse c given side lengths a and b?",
                "sections": ["2. The core rule"],
                "encounter_id": "cluster_2",
                "content": {
                    "compute_expression": "( a 2 + b 2 ) 0.5",
                    "output_field": "c",
                    "input_contract": {"a": "number", "b": "number"},
                    "output_contract": {"c": "number"},
                    "python_script": "",
                },
            },
        )
        self.assertIsNotNone(artifact)
        self.assertEqual(artifact.content.get("compute_expression"), "( a ** 2 + b ** 2 ) ** 0.5")
        execution = self.controller.execute_function_artifact(
            artifact,
            semantic_unit="What is the length of the hypotenuse when a=3 and b=4?",
        )
        self.assertTrue(execution.ok)
        self.assertEqual(execution.answer, "5")

    def test_markdown_learning_artifact_repairs_heading_like_knowledge_title(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning artifact repairs heading like knowledge title.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_learning_artifact_repairs_heading_like_knowledge_title()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Cylinder Measures

## 2. Total Surface Area of a Cylinder

The total surface area includes the top, bottom, and curved side.

* input: r
* input: h
* output: A
"""
        document = parse_markdown_document_ir(markdown, source_path="cylinder.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("cylinder.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "2. Total Surface Area of a Cylinder",
                "semantic_unit": "2. Total Surface Area of a Cylinder",
                "question": "What is 2. Total Surface Area of a Cylinder?",
                "answer": "Use the cylinder surface-area relation.",
                "sections": ["2. Total Surface Area of a Cylinder"],
            },
        )
        self.assertIsNotNone(artifact)
        self.assertEqual(
            artifact.title,
            "Cylinder Measures / Total Surface Area of a Cylinder",
        )
        self.assertEqual(
            artifact.content.get("title_broader_category"),
            "Cylinder Measures",
        )
        self.assertEqual(
            artifact.content.get("title_current_identity"),
            "Total Surface Area of a Cylinder",
        )
        self.assertEqual(
            artifact.content.get("question"),
            "What is Total Surface Area of a Cylinder?",
        )

    def test_markdown_learning_artifact_anchors_flat_title_under_document_title(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning artifact anchors flat title under document title.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_learning_artifact_anchors_flat_title_under_document_title()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Newton's Laws of Motion

## First Law: Law of Inertia

An object remains at rest or in uniform motion unless acted upon by an external force.
"""
        document = parse_markdown_document_ir(markdown, source_path="newton.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("newton.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "First Law: Law of Inertia",
                "semantic_unit": "First law of inertia",
                "question": "What is Newton's first law of motion?",
                "answer": "An object remains at rest or in uniform motion unless acted upon by an external force.",
                "sections": ["First Law: Law of Inertia"],
            },
        )
        self.assertIsNotNone(artifact)
        assert artifact is not None
        self.assertEqual(
            artifact.title,
            "Newton's Laws of Motion / First Law: Law of Inertia",
        )
        self.assertEqual(
            artifact.content.get("title_broader_category"),
            "Newton's Laws of Motion",
        )

    def test_markdown_learning_repairs_corrupted_broader_category_echo(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning repairs corrupted broader category echo.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_learning_repairs_corrupted_broader_category_echo()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Probability Relations 01 — Additive Combination

## 1. Reusable substrate

When one quantity is obtained by adding two named input quantities, the reusable family is additive combination.
"""
        document = parse_markdown_document_ir(markdown, source_path="probability01.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("probability01.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "Probability Relations 01 0 4 0 0 0 0 0 / T From X And Y",
                "title_broader_category": "Probability Relations 01 0 4 0 0 0 0 0",
                "title_current_identity": "T From X And Y",
                "semantic_unit": "T from x and y",
                "question": "What is T From X And Y?",
                "answer": "T is formed by adding x and y.",
                "sections": [],
            },
        )
        self.assertIsNotNone(artifact)
        assert artifact is not None
        self.assertEqual(
            artifact.title,
            "Probability Relations 01 — Additive Combination / T From X And Y",
        )
        self.assertEqual(
            artifact.content.get("title_broader_category"),
            "Probability Relations 01 — Additive Combination",
        )

    def test_markdown_learning_repairs_digit_letter_broader_category_echo(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning repairs digit letter broader category echo.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_learning_repairs_digit_letter_broader_category_echo()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Probability Relations 02 — Ratio Formation

## 4. Distinguishing the relation

Probability and raw count are not the same kind of quantity.
"""
        document = parse_markdown_document_ir(markdown, source_path="probability02.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("probability02.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "Probability Relations 02 4atio Formation / Count Is An Absolute Amount",
                "title_broader_category": "Probability Relations 02 4atio Formation",
                "title_current_identity": "Count Is An Absolute Amount",
                "semantic_unit": "Count is an absolute amount",
                "question": "What is Count Is An Absolute Amount?",
                "answer": "Count is an absolute amount.",
                "sections": ["4. Distinguishing the relation"],
            },
        )
        self.assertIsNotNone(artifact)
        assert artifact is not None
        self.assertEqual(
            artifact.title,
            "Probability Relations 02 — Ratio Formation / Count Is An Absolute Amount",
        )
        self.assertEqual(
            artifact.content.get("title_broader_category"),
            "Probability Relations 02 — Ratio Formation",
        )

    def test_markdown_learning_repairs_single_letter_broader_category_noise(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning repairs single letter broader category noise.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_learning_repairs_single_letter_broader_category_noise()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Probability Relations 01 — Additive Combination

## 3. Distinguishing the relation

Additive combination is about composition into a total.
"""
        document = parse_markdown_document_ir(markdown, source_path="probability01b.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("probability01b.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "Probability Relations 01 d Additive Combination / Additive Combination Is About Composition Into A Total",
                "title_broader_category": "Probability Relations 01 d Additive Combination",
                "title_current_identity": "Additive Combination Is About Composition Into A Total",
                "semantic_unit": "Additive combination is about composition into a total",
                "question": "What is 3. Distinguishing the relation?",
                "answer": "Additive combination is about composition into a total.",
                "sections": ["3. Distinguishing the relation"],
            },
        )
        self.assertIsNotNone(artifact)
        assert artifact is not None
        self.assertEqual(
            artifact.title,
            "Probability Relations 01 — Additive Combination / Additive Combination Is About Composition Into A Total",
        )
        self.assertEqual(
            artifact.content.get("title_broader_category"),
            "Probability Relations 01 — Additive Combination",
        )

    def test_markdown_learning_artifact_resolves_related_titles_to_prior_artifacts(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning artifact resolves related titles to prior artifacts.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_learning_artifact_resolves_related_titles_to_prior_artifacts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Physics Math Relations

## 1. Reusable substrate

The reusable arithmetic family is multiplicative combination.

$$ P = x * y $$

* input: `x`
* input: `y`
* output: `P`

## 2. Force from mass and acceleration

Force reuses the earlier multiplicative-combination family.

$$ F = m * a $$

* input: `m`
* input: `a`
* output: `F`
"""
        document = parse_markdown_document_ir(markdown, source_path="physics_math_relations.md")
        substrate = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("physics_math_relations.md"),
            payload={
                "artifact_type": "ability",
                "title": "Math / Multiplicative Combination / Product From Two Factors",
                "title_broader_category": "Math",
                "title_current_identity": "Multiplicative Combination",
                "title_downward_decomposition": ["Product From Two Factors"],
                "semantic_unit": "Product from two factors",
                "question": "How do you calculate P from x and y?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "x * y",
                    "output_field": "P",
                    "input_contract": {"x": "number", "y": "number"},
                    "output_contract": {"P": "number"},
                },
            },
        )
        self.assertIsNotNone(substrate)
        dependent = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("physics_math_relations.md"),
            payload={
                "artifact_type": "ability",
                "title": "Physics / Force / Force From Mass And Acceleration",
                "title_broader_category": "Physics",
                "title_current_identity": "Force",
                "title_downward_decomposition": ["Force From Mass And Acceleration"],
                "semantic_unit": "Force from mass and acceleration",
                "question": "How do you calculate F from m and a?",
                "related_titles": [
                    "Math / Multiplicative Combination / Product From Two Factors",
                ],
                "sections": ["2. Force from mass and acceleration"],
                "content": {
                    "compute_expression": "m * a",
                    "output_field": "F",
                    "input_contract": {"m": "number", "a": "number"},
                    "output_contract": {"F": "number"},
                },
            },
        )
        self.assertIsNotNone(dependent)
        self.controller.state.learned_artifacts[substrate.id] = substrate
        self.controller.state.learned_artifacts[dependent.id] = dependent
        changed = self.controller.apply_markdown_batch_relations([substrate, dependent])
        self.assertEqual([artifact.id for artifact in changed], [dependent.id])
        self.assertIn(substrate.id, dependent.related_artifact_ids)
        self.assertEqual(
            dependent.content.get("related_titles"),
            [
                "Math / Multiplicative Combination / Product From Two Factors",
                "Multiplicative Combination",
            ],
        )

    def test_generic_python_ability_keeps_family_hint_out_of_title_similies(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with checking that a generic executor wrapper keeps reusable-family hints in relation metadata instead of promoting them into title-similarity scaffolding.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_generic_python_ability_keeps_family_hint_out_of_title_similies()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Probability Relations 01 — Additive Combination

## 1. Reusable substrate

When one quantity is obtained by adding two named input quantities, the reusable family is additive combination.

$$ T = x + y $$

* input: `x`
* input: `y`
* output: `T`
"""
        document = parse_markdown_document_ir(markdown, source_path="probability_relations_01.md")
        artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("probability_relations_01.md"),
            payload={
                "artifact_type": "ability",
                "title": "Python Ability",
                "semantic_unit": "python ability",
                "question": "What is Python Ability?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "x + y",
                    "output_field": "T",
                    "input_contract": {"x": "number", "y": "number"},
                    "output_contract": {"T": "number"},
                },
            },
        )
        self.assertIsNotNone(artifact)
        assert artifact is not None
        self.assertNotIn("Additive Combination", artifact.content.get("title_similies", []))
        self.assertIn("Additive Combination", artifact.content.get("relation_family_hints", []))

    def test_markdown_text_relation_hints_capture_probability_reuse_phrases(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with checking that markdown relation hints cover the probability/information reuse phrasings used in the validation curriculum.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_text_relation_hints_capture_probability_reuse_phrases()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        hints = self.controller.markdown_text_relation_hints("The term P(A) may itself come from ratio formation:")
        self.assertIn("Ratio Formation", hints)

        hints = self.controller.markdown_text_relation_hints("expectation for both centers")
        self.assertIn("Expectation", hints)

        hints = self.controller.markdown_text_relation_hints("weighted aggregation over probability")
        self.assertIn("Weighted Aggregation", hints)

        hints = self.controller.markdown_text_relation_hints("expectation-like structure remains, because the terms are weighted by p_i")
        self.assertIn("Expectation", hints)

    def test_relation_resolution_penalizes_generic_python_ability_for_family_hint(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with checking that generic executor wrappers do not win semantic-family relation resolution over the actual reusable substrate.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_relation_resolution_penalizes_generic_python_ability_for_family_hint()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Probability Relations 05 — Bayes Update

## 1. Reusable substrate

When one conditional quantity is transformed into its reverse-direction counterpart through a shared joint relation, the reusable family is inverse conditional update.

$$ u = (l * p) / e $$

* input: `l`
* input: `p`
* input: `e`
* output: `u`
"""
        document = parse_markdown_document_ir(markdown, source_path="bayes.md")
        substrate = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("bayes.md"),
            payload={
                "artifact_type": "knowledge",
                "title": "Inverse Conditional Update",
                "semantic_unit": "inverse conditional update",
                "question": "What is inverse conditional update?",
                "answer": "Inverse conditional update reverses conditional direction through a shared joint relation.",
                "sections": ["1. Reusable substrate"],
            },
        )
        python_ability = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=document,
            source_path=Path("bayes.md"),
            payload={
                "artifact_type": "ability",
                "title": "Python Ability",
                "semantic_unit": "python ability",
                "question": "What is Python Ability?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "(l * p) / e",
                    "output_field": "u",
                    "input_contract": {"l": "number", "p": "number", "e": "number"},
                    "output_contract": {"u": "number"},
                },
            },
        )
        self.assertIsNotNone(substrate)
        self.assertIsNotNone(python_ability)
        assert substrate is not None and python_ability is not None

        resolved = self.controller.resolve_related_artifact_ids_from_title_hints(
            related_titles=["Inverse Conditional Update"],
            pool=[python_ability, substrate],
            exclude_artifact_id="",
        )
        self.assertEqual(resolved, [substrate.id])

    def test_markdown_learning_infers_related_titles_from_reusing_earlier_lessons(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning infers related titles from reusing earlier lessons.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_learning_infers_related_titles_from_reusing_earlier_lessons()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        ratio_markdown = """# Probability Relations 02 — Ratio Formation

## 1. Reusable substrate

When one quantity is obtained by comparing a part to a total, the reusable family is ratio formation.

$$ r = x / T $$

* input: `x`
* input: `T`
* output: `r`
"""
        bayes_markdown = """# Probability Relations 05 — Bayes Update

## 1. Reusable substrate

When one conditional quantity is transformed into its reverse-direction counterpart through a shared joint relation, the reusable family is inverse conditional update.

$$ u = (l * p) / e $$

* input: `l`
* input: `p`
* input: `e`
* output: `u`

## 2. Bayes theorem

Bayes theorem is an inverse-conditional-update relation.

$$ post = (likelihood * prior) / evidence $$

* input: `likelihood`
* input: `prior`
* input: `evidence`
* output: `post`

## 3. Reusing earlier lessons

* likelihood is itself a conditional-restriction relation
* prior and evidence may be formed through ratio relations
"""
        ratio_document = parse_markdown_document_ir(ratio_markdown, source_path="ratio.md")
        bayes_document = parse_markdown_document_ir(bayes_markdown, source_path="bayes.md")
        ratio_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=ratio_document,
            source_path=Path("ratio.md"),
            payload={
                "artifact_type": "ability",
                "title": "R From X And T",
                "semantic_unit": "r from x and t",
                "question": "How do you calculate r from x and T?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "x / T",
                    "output_field": "r",
                    "input_contract": {"x": "number", "T": "number"},
                    "output_contract": {"r": "number"},
                },
            },
        )
        self.assertIsNotNone(ratio_artifact)
        bayes_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=bayes_document,
            source_path=Path("bayes.md"),
            payload={
                "artifact_type": "ability",
                "title": "Posterior From Likelihood Prior And Evidence",
                "semantic_unit": "posterior from likelihood prior and evidence",
                "question": "How do you calculate posterior from likelihood, prior, and evidence?",
                "sections": ["2. Bayes theorem"],
                "content": {
                    "compute_expression": "(likelihood * prior) / evidence",
                    "output_field": "post",
                    "input_contract": {
                        "likelihood": "number",
                        "prior": "number",
                        "evidence": "number",
                    },
                    "output_contract": {"post": "number"},
                },
            },
        )
        self.assertIsNotNone(bayes_artifact)
        assert ratio_artifact is not None and bayes_artifact is not None
        self.assertIn("Ratio Formation", bayes_artifact.content.get("related_titles", []))
        self.controller.state.learned_artifacts[ratio_artifact.id] = ratio_artifact
        self.controller.state.learned_artifacts[bayes_artifact.id] = bayes_artifact
        changed = self.controller.apply_markdown_batch_relations([bayes_artifact])
        self.assertEqual([artifact.id for artifact in changed], [bayes_artifact.id])
        self.assertIn(ratio_artifact.id, bayes_artifact.related_artifact_ids)

    def test_markdown_learning_extracts_reusable_family_from_summary_clause(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning extracts reusable family from summary clause.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_markdown_learning_extracts_reusable_family_from_summary_clause()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        additive_markdown = """# Probability Relations 01 — Additive Combination

## 1. Reusable substrate

When one quantity is obtained by adding two named input quantities, the reusable family is additive combination.

$$ T = x + y $$

* input: `x`
* input: `y`
* output: `T`
"""
        ratio_markdown = """# Probability Relations 02 — Ratio Formation

## 1. Reusable substrate

When one quantity is obtained by comparing a part to a total, the reusable family is ratio formation.

$$ r = x / T $$

* input: `x`
* input: `T`
* output: `r`

## 2. Probability from favorable count and total count

Probability is a ratio-formation relation.

$$ P(A) = n(A) / n(S) $$

* input: `n(A)`
* input: `n(S)`
* output: `P(A)`

## 3. Reusing the earlier lesson

The denominator often comes from additive combination.

For example, if the sample space is formed from two disjoint groups:

$$ n(S) = a + b $$

Then probability may reuse both lessons:

$$ P(A) = n(A) / (a + b) $$

## 5. One-sentence summary

Ratio formation is a reusable substrate for probability, and it often depends on totals previously formed by additive combination.
"""
        additive_document = parse_markdown_document_ir(additive_markdown, source_path="additive.md")
        ratio_document = parse_markdown_document_ir(ratio_markdown, source_path="ratio.md")

        additive_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=additive_document,
            source_path=Path("additive.md"),
            payload={
                "artifact_type": "ability",
                "title": "T From X And Y",
                "semantic_unit": "t from x and y",
                "question": "How do you calculate T from x and y?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "x + y",
                    "output_field": "T",
                    "input_contract": {"x": "number", "y": "number"},
                    "output_contract": {"T": "number"},
                },
            },
        )
        ratio_probability_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=ratio_document,
            source_path=Path("ratio.md"),
            payload={
                "artifact_type": "ability",
                "title": "Probability From Favorable Count And Total Count",
                "semantic_unit": "probability from favorable count and total count",
                "question": "How do you calculate probability from favorable count and total count?",
                "sections": ["2. Probability from favorable count and total count"],
                "content": {
                    "compute_expression": "n_A / n_S",
                    "output_field": "P(A)",
                    "input_contract": {"n_A": "number", "n_S": "number"},
                    "output_contract": {"P(A)": "number"},
                },
            },
        )
        self.assertIsNotNone(additive_artifact)
        self.assertIsNotNone(ratio_probability_artifact)
        assert additive_artifact is not None and ratio_probability_artifact is not None

        self.assertIn("Additive Combination", ratio_probability_artifact.content.get("related_titles", []))

        self.controller.state.learned_artifacts[additive_artifact.id] = additive_artifact
        self.controller.state.learned_artifacts[ratio_probability_artifact.id] = ratio_probability_artifact
        changed = self.controller.apply_markdown_batch_relations([ratio_probability_artifact])
        self.assertEqual([artifact.id for artifact in changed], [ratio_probability_artifact.id])
        self.assertIn(additive_artifact.id, ratio_probability_artifact.related_artifact_ids)

    def test_markdown_batch_relations_consult_recent_store_artifacts(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown batch relations consult recent store artifacts.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_markdown_batch_relations_consult_recent_store_artifacts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        additive_markdown = """# Probability Relations 01 — Additive Combination

## 1. Reusable substrate

When one quantity is obtained by adding two named input quantities, the reusable family is additive combination.
"""
        ratio_markdown = """# Probability Relations 02 — Ratio Formation

## 2. Probability from favorable count and total count

Probability is a ratio-formation relation.

## 5. One-sentence summary

Ratio formation is a reusable substrate for probability, and it often depends on totals previously formed by additive combination.
"""
        additive_document = parse_markdown_document_ir(additive_markdown, source_path="additive.md")
        ratio_document = parse_markdown_document_ir(ratio_markdown, source_path="ratio.md")
        additive_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=additive_document,
            source_path=Path("additive.md"),
            payload={
                "artifact_type": "ability",
                "title": "T From X And Y",
                "semantic_unit": "t from x and y",
                "question": "How do you calculate T from x and y?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "x + y",
                    "output_field": "T",
                    "input_contract": {"x": "number", "y": "number"},
                    "output_contract": {"T": "number"},
                },
            },
        )
        ratio_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=ratio_document,
            source_path=Path("ratio.md"),
            payload={
                "artifact_type": "ability",
                "title": "Probability From Favorable Count And Total Count",
                "semantic_unit": "probability from favorable count and total count",
                "question": "How do you calculate probability from favorable count and total count?",
                "sections": ["2. Probability from favorable count and total count"],
                "content": {
                    "compute_expression": "n_A / n_S",
                    "output_field": "P(A)",
                    "input_contract": {"n_A": "number", "n_S": "number"},
                    "output_contract": {"P(A)": "number"},
                },
            },
        )
        self.assertIsNotNone(additive_artifact)
        self.assertIsNotNone(ratio_artifact)
        assert additive_artifact is not None and ratio_artifact is not None

        self.controller.artifact_store.load_recent_artifacts = lambda limit=512: [additive_artifact]  # type: ignore[method-assign]
        changed = self.controller.apply_markdown_batch_relations([ratio_artifact])
        self.assertEqual([artifact.id for artifact in changed], [ratio_artifact.id])
        self.assertIn(additive_artifact.id, ratio_artifact.related_artifact_ids)

    def test_relation_resolution_prefers_identity_match_over_hint_only_match(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing relation resolution prefers identity match over hint only match.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_relation_resolution_prefers_identity_match_over_hint_only_match()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        additive_document = parse_markdown_document_ir(
            "# Probability Relations 01 — Additive Combination\n\n## 1. Reusable substrate\n\nThe reusable family is additive combination.\n",
            source_path="additive.md",
        )
        ratio_document = parse_markdown_document_ir(
            "# Probability Relations 02 — Ratio Formation\n\n## 1. Reusable substrate\n\nThe reusable family is ratio formation.\n\n## 5. One-sentence summary\n\nRatio formation often depends on additive combination.\n",
            source_path="ratio.md",
        )
        additive_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=additive_document,
            source_path=Path("additive.md"),
            payload={
                "artifact_type": "ability",
                "title": "T From X And Y",
                "semantic_unit": "t from x and y",
                "question": "How do you calculate T from x and y?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "x + y",
                    "output_field": "T",
                    "input_contract": {"x": "number", "y": "number"},
                    "output_contract": {"T": "number"},
                },
            },
        )
        ratio_artifact = self.controller.build_markdown_learning_artifact(
            node=self.node,
            document=ratio_document,
            source_path=Path("ratio.md"),
            payload={
                "artifact_type": "ability",
                "title": "R From X And T",
                "semantic_unit": "r from x and t",
                "question": "How do you calculate r from x and T?",
                "sections": ["1. Reusable substrate"],
                "content": {
                    "compute_expression": "x / T",
                    "output_field": "r",
                    "input_contract": {"x": "number", "T": "number"},
                    "output_contract": {"r": "number"},
                },
            },
        )
        self.assertIsNotNone(additive_artifact)
        self.assertIsNotNone(ratio_artifact)
        assert additive_artifact is not None and ratio_artifact is not None

        resolved = self.controller.resolve_related_artifact_ids_from_title_hints(
            related_titles=["Additive Combination"],
            pool=[ratio_artifact, additive_artifact],
            exclude_artifact_id="",
        )
        self.assertEqual(resolved, [additive_artifact.id])


if __name__ == "__main__":
    unittest.main()
