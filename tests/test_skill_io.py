# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from main import Artifact, ArtifactAdmission, ArtifactRepresentation, ArtifactReuse, ArtifactType, LearningRelation, build_artifact_store, load_artifact_yaml_documents
from host_abi import host_abi_version, wasm_skill_abi_version
from governed_skill_installation import handle_import_skill_command
from skill_export_projection import (
    batch_skill_export_filename,
    export_skill_bundle_text,
    skill_export_document,
    skill_kind_from_artifact,
)
from realized_skill_application.projection import (
    skill_kind_from_artifact as packaged_skill_kind_from_artifact,
)
from skill_governance import (
    artifact_admitted_for_use,
    evaluate_skill_admission,
)
from skill_schema_io import artifact_from_skill_document, resolve_import_skill_files, stable_skill_artifact_id
from skill_registry import skill_registry_document


class SkillIOTests(unittest.TestCase):
    def test_skill_kind_projection_has_one_application_owner(self) -> None:
        self.assertIs(skill_kind_from_artifact, packaged_skill_kind_from_artifact)
        for kind in ("knowledge", "ability"):
            payload: dict[str, object] = {
                "schema": "bssc_skill.v1",
                "kind": kind,
                "title": f"Projection {kind}",
            }
            if kind == "knowledge":
                payload["answer"] = "A deterministic answer."
            elif kind == "ability":
                payload.update(
                    {
                        "executor": "python3",
                        "python": "def main(): return {'status': 'ok'}\n",
                    }
                )
            artifact = artifact_from_skill_document(payload)
            with self.subTest(kind=kind):
                self.assertEqual(kind, packaged_skill_kind_from_artifact(artifact))

    def setUp(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed skill import tests that need isolated persistence, helps with creating one temporary SQLite store boundary per test.

        Reference to Theory:
            Verifies the skill-kernel and governance-envelope split together with governed admission in an isolated store so policy state does not leak across tests.

        Example Input Output:
            Input: `setUp()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.tempdir = tempfile.TemporaryDirectory(prefix="skill_io_")
        self.sqlite_path = str(Path(self.tempdir.name) / "skill_io.sqlite3")
        self.previous_sqlite_path = os.environ.get("STATE_SQLITE_PATH")
        os.environ["STATE_SQLITE_PATH"] = self.sqlite_path

    def tearDown(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed skill import tests that need isolated persistence, helps with restoring the previous SQLite environment after each test.

        Reference to Theory:
            Verifies the skill-kernel and governance-envelope split together with governed admission without leaking policy state across tests.

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

    def test_resolve_import_skill_files_deduplicates_absolute_paths(self) -> None:
        """
        High Level Purpose:
            In circumstances like exchange-layer schema import normalization, helps with verifying that repeated skill-file arguments collapse to one absolute path without depending on runtime composition helpers.

        Reference to Theory:
            Verifies that portable skill import file resolution stays on root helper normalization surfaces rather than `main.py` reach-throughs.

        Example Input Output:
            Input: `test_resolve_import_skill_files_deduplicates_absolute_paths()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        skill_path = Path(self.tempdir.name) / "demo-skill.yaml"
        skill_path.write_text("schema: bssc_skill.v1\ntitle: Demo\nkind: knowledge\nanswer: hi\n")
        args = argparse.Namespace(
            skill_file=[str(skill_path), str(skill_path.resolve())],
            skill_files_file=None,
            skill_dir=None,
        )

        resolved = resolve_import_skill_files(args)

        self.assertEqual(resolved, [skill_path.resolve()])

    def test_minimal_knowledge_skill_import_survives(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over the compact skill interface, helps with verifying that the minimal knowledge kernel is enough for import survival.

        Reference to Theory:
            Verifies the skill-kernel and governance-envelope split so import can survive with the compact kernel while governance remains optional.

        Example Input Output:
            Input: `test_minimal_knowledge_skill_import_survives()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = {
            "schema": "bssc_skill.v1",
            "kind": "knowledge",
            "title": "What Is Force?",
            "answer": "Force equals mass times acceleration.",
        }

        artifact = artifact_from_skill_document(payload)

        self.assertEqual(artifact.id, stable_skill_artifact_id("What Is Force?"))
        self.assertEqual(artifact.artifact_type, ArtifactType.KNOWLEDGE)
        self.assertEqual(artifact.title, "What Is Force?")
        self.assertEqual(artifact.content.get("answer"), "Force equals mass times acceleration.")

    def test_minimal_python_ability_skill_import_survives(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over the compact skill interface, helps with verifying that the minimal Python ability kernel is enough for import survival and execution metadata recovery.

        Reference to Theory:
            Verifies the skill-kernel and governance-envelope split so executable abilities can survive import with only their compact kernel plus executor information.

        Example Input Output:
            Input: `test_minimal_python_ability_skill_import_survives()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = {
            "schema": "bssc_skill.v1",
            "kind": "ability",
            "title": "Open Browser URL",
            "executor": "python3",
            "inputs": {
                "browser": "browser application name",
                "url": "target URL",
            },
            "outputs": {
                "status": "open status",
            },
            "dependencies": ["requests"],
            "python": (
                "def main(browser: str, url: str, __dependencies__: tuple[str, ...] = ()):\n"
                "    import webbrowser\n"
                "    webbrowser.open(url)\n"
                "    return {'status': 'opened', 'browser': browser, 'url': url}\n"
            ),
        }

        artifact = artifact_from_skill_document(payload)

        self.assertEqual(artifact.artifact_type, ArtifactType.ABILITY)
        self.assertEqual(artifact.representation, ArtifactRepresentation.PYTHON_SCRIPT)
        self.assertEqual(artifact.content.get("entrypoint"), "main")
        self.assertIn("requests", artifact.content.get("dependencies", []))
        self.assertIn("msgspec", artifact.content.get("dependencies", []))
        self.assertEqual(artifact.content.get("executor_framework"), "python3")
        self.assertIn("python_script", artifact.content)
        self.assertIn("skill_normalization", artifact.content)
        normalization = dict(artifact.content.get("skill_normalization", {}))
        self.assertEqual(normalization.get("normalization_version"), "bssc.skill.normalization.v1")
        self.assertIn("a", normalization.get("regions", {}))
        self.assertIn("d", normalization.get("regions", {}))

    def test_minimal_wasm_ability_skill_import_survives(self) -> None:
        payload = {
            "schema": "bssc_skill.v1",
            "kind": "ability",
            "title": "Wasm Hi",
            "executor": "wasm_wasi",
            "inputs": {},
            "outputs": {
                "greeting": "reply text",
            },
            "wasm": (
                "(module\n"
                "  (import \"bssc\" \"input_len\" (func $input_len (result i32)))\n"
                "  (import \"bssc\" \"read_input\" (func $read_input (param i32) (result i32)))\n"
                "  (import \"bssc\" \"write_output\" (func $write_output (param i32 i32) (result i32)))\n"
                "  (memory (export \"memory\") 1)\n"
                "  (func (export \"run\") (result i32)\n"
                "    i32.const 0))"
            ),
            "wasm_abi_version": wasm_skill_abi_version(),
            "wasm_format": "wat",
        }

        artifact = artifact_from_skill_document(payload)

        self.assertEqual(artifact.artifact_type, ArtifactType.ABILITY)
        self.assertEqual(artifact.representation, ArtifactRepresentation.WASM_MODULE)
        self.assertEqual(artifact.content.get("entrypoint"), "run")
        self.assertEqual(artifact.content.get("executor_framework"), "wasm_wasi")
        self.assertEqual(artifact.content.get("wasm_abi_version"), wasm_skill_abi_version())
        self.assertEqual(artifact.content.get("wasm_format"), "wat")
        self.assertIn("wasm_module", artifact.content)

    def test_governance_is_optional_and_cannot_override_kernel(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over the compact skill interface, helps with verifying that the optional governance envelope can enrich import without overriding the kernel identity or kind.

        Reference to Theory:
            Verifies the skill-kernel and governance-envelope split so governance remains secondary to the portable kernel during import.

        Example Input Output:
            Input: `test_governance_is_optional_and_cannot_override_kernel()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = {
            "schema": "bssc_skill.v1",
            "kind": "knowledge",
            "title": "What Is Momentum?",
            "answer": "Momentum equals mass times velocity.",
            "governance": {
                "artifact_id": "artifact-evil",
                "artifact_type": "ability",
                "scope": "custom scope from governance",
                "reusability": "broad_reuse",
            },
        }

        artifact = artifact_from_skill_document(payload)

        self.assertEqual(artifact.id, stable_skill_artifact_id("What Is Momentum?"))
        self.assertEqual(artifact.artifact_type, ArtifactType.KNOWLEDGE)
        self.assertEqual(artifact.scope, "custom scope from governance")
        self.assertEqual(artifact.content.get("answer"), "Momentum equals mass times velocity.")

    def test_skill_export_document_defaults_to_v2_and_synthesizes_declaration(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over governed skill export for legacy artifacts, helps with verifying that export defaults to v2 and synthesizes a declaration when one was never stored.

        Reference to Theory:
            Verifies the declaration-first export rule so older artifacts can leave the system in governed form without requiring that they were originally imported as v2 skills.

        Example Input Output:
            Input: `test_skill_export_document_defaults_to_v2_and_synthesizes_declaration()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "knowledge",
                "title": "What Is Power?",
                "question": "What is power?",
                "answer": "Power is work per unit time.",
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(exported["schema"], "bssc_skill.v2")
        self.assertEqual(exported["kind"], "knowledge")
        self.assertEqual(exported["title"], "What Is Power?")
        self.assertEqual(exported["answer"], "Power is work per unit time.")
        self.assertIn("declaration", exported)
        self.assertEqual(exported["declaration"]["authorities_requested"], ["read"])
        self.assertEqual(exported["declaration"]["risk_tier"], "tier0_passive")
        self.assertIn("governance", exported)
        self.assertEqual(exported["governance"]["scope"], artifact.scope)
        self.assertIn("normalization", exported)
        self.assertEqual(exported["normalization"]["normalization_version"], "bssc.skill.normalization.v1")

    def test_skill_import_and_export_round_trip_aliases_and_family_metadata(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
                "aliases": ["Read Text File"],
                "family": {"label": "Python Commands"},
                "executor": "python3",
                "inputs": {
                    "mount": "required input value",
                    "relative_path": "required input value",
                },
                "outputs": {"result": "execution result"},
                "python": (
                    "def main(mount: str, relative_path: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    return {'status': 'read', 'mount': mount, 'relative_path': relative_path}\n"
                ),
            }
        )

        self.assertEqual(
            artifact.content.get("aliases"),
            ["Read Text File", "Python Commands 02 Read Text File"],
        )
        self.assertEqual(
            artifact.content.get("skill_family"),
            {
                "label": "Python Commands",
                "key": "python commands",
            },
        )

        exported = skill_export_document(artifact)
        self.assertEqual(
            exported.get("aliases"),
            ["Read Text File", "Python Commands 02 Read Text File"],
        )
        self.assertEqual(
            exported.get("family"),
            {
                "label": "Python Commands",
                "key": "python commands",
            },
        )

    def test_skill_import_and_export_round_trip_explicit_normalization_metadata(self) -> None:
        payload = {
            "schema": "bssc_skill.v2",
            "kind": "ability",
            "title": "Explicit Normalization Example",
            "executor": "python3",
            "inputs": {"url": "target URL"},
            "outputs": {"status": "open status"},
            "python": (
                "def main(url: str, __dependencies__: tuple[str, ...] = ()):\n"
                "    return {'status': 'ok', 'url': url}\n"
            ),
            "declaration": {
                "intent": "Open a URL.",
                "inputs": {"url": "target URL"},
                "outputs": {"status": "open status"},
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
            },
            "normalization": {
                "normalization_version": "bssc.skill.normalization.v1",
                "path_notation_version": "bssc.skill.path.v1",
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "carrier_kind": "value",
                        "reconstructible": True,
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/url",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "url",
                                "value": "target URL",
                                "leaf_class": "scalar",
                            }
                        ],
                    }
                },
            },
        }

        artifact = artifact_from_skill_document(payload)
        exported = skill_export_document(artifact)

        self.assertIn("skill_normalization", artifact.content)
        self.assertEqual(
            artifact.content["skill_normalization"]["regions"]["a"]["leaves"][0]["path"],
            "/a/url",
        )
        self.assertIn("normalization", exported)
        self.assertEqual(
            exported["normalization"]["regions"]["a"]["leaves"][0]["path"],
            "/a/url",
        )

    def test_skill_import_and_export_round_trip_compatibility_metadata(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Repo Search",
                "description": ["Search the repository for a symbol."],
                "inputs": {
                    "symbol": "required symbol to find",
                    "root": "workspace root",
                },
                "compatibility": {
                    "adapters": [
                        {
                            "direction": "import",
                            "format": "openai_tool",
                            "surface": "function",
                            "name": "repo_search",
                        }
                    ]
                },
            }
        )

        self.assertEqual(
            artifact.content.get("skill_compatibility"),
            {
                "adapters": [
                    {
                        "direction": "import",
                        "format": "openai_tool",
                        "surface": "function",
                        "name": "repo_search",
                    }
                ]
            },
        )

        exported = skill_export_document(artifact)

        self.assertEqual(
            exported.get("compatibility"),
            {
                "adapters": [
                    {
                        "direction": "import",
                        "format": "openai_tool",
                        "surface": "function",
                        "name": "repo_search",
                    }
                ]
            },
        )

    def test_skill_export_document_round_trips_wasm_fields(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Wasm Hi",
                "executor": "wasm_wasi",
                "inputs": {},
                "outputs": {"greeting": "reply text"},
                "wasm": "(module (memory (export \"memory\") 1) (func (export \"run\") (result i32) i32.const 0))",
                "wasm_abi_version": wasm_skill_abi_version(),
                "wasm_format": "wat",
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(exported["executor"], "wasm_wasi")
        self.assertEqual(exported["wasm_abi_version"], wasm_skill_abi_version())
        self.assertEqual(exported["wasm_format"], "wat")
        self.assertIn("wasm", exported)

    def test_skill_export_document_projects_hosting_metadata(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Open Browser URL",
                "executor": "python3",
                "inputs": {"url": "target URL"},
                "outputs": {"status": "open status"},
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened', 'url': url}\n",
                "governance": {
                    "governed_host_brokers": ["browser.open"],
                    "host_abi_version": host_abi_version(),
                    "virtual_mounts": {"skill_output": "/tmp/out"},
                },
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(exported["hosting_metadata"]["executor_framework"], "python3")
        self.assertEqual(exported["hosting_metadata"]["representation"], "python_script")
        self.assertEqual(exported["hosting_metadata"]["entrypoint"], "main")
        self.assertEqual(exported["hosting_metadata"]["governed_host_brokers"], ["browser.open"])
        self.assertEqual(exported["hosting_metadata"]["host_abi_version"], host_abi_version())
        self.assertEqual(exported["hosting_metadata"]["virtual_mounts"], ["skill_output"])

    def test_governed_data_surfaces_round_trip_through_skill_governance(self) -> None:
        """
        High Level Purpose:
            In circumstances like exporting and re-importing governed brokered skills, helps with verifying that virtual mounts, named queries, and skill-state namespace survive through the optional governance envelope.

        Reference to Theory:
            Verifies the new data-governance layer is portable rather than runtime-local by round-tripping the data-boundary configuration through the skill interface.

        Example Input Output:
            Input: `test_governed_data_surfaces_round_trip_through_skill_governance()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Mounted Notes Writer",
                "executor": "python3",
                "inputs": {"relative_path": "path under skill output", "text": "text to write"},
                "outputs": {"status": "write status"},
                "python": (
                    "def main(relative_path: str, text: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    from python_skill_host import broker_request\n"
                    "    return broker_request('fs.write_mount', mount='skill_output', relative_path=relative_path, text=text)\n"
                ),
                "declaration": {
                    "intent": "Write notes into the governed output mount.",
                    "inputs": {"relative_path": "path under skill output", "text": "text to write"},
                    "outputs": {"status": "write status"},
                    "authorities_requested": ["execute", "write", "persist"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "write": {
                            "scope": "virtual_mount",
                            "target": "skill_output",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "persist": {
                            "scope": "skill_state",
                            "target": "notes_state",
                            "context": "explicit_user_prompt",
                            "duration": "multi_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["public", "derived", "internal"],
                    "side_effects": ["write governed output mount", "persist skill state"],
                    "persistence_behavior": "skill_state",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
                "governance": {
                    "virtual_mounts": {
                        "skill_output": {
                            "root": str(Path(self.tempdir.name) / "mounted_output"),
                            "permissions": ["read", "write", "list"],
                            "data_class": "public",
                        }
                    },
                    "named_queries": {
                        "artifact_count": {
                            "sql": "SELECT COUNT(*) AS artifact_count FROM artifacts",
                            "parameter_order": [],
                            "data_class": "internal",
                        }
                    },
                    "skill_state_namespace": "notes_state",
                },
            }
        )

        exported = skill_export_document(artifact)
        governance = dict(exported.get("governance", {}))

        self.assertIn("virtual_mounts", governance)
        self.assertIn("named_queries", governance)
        self.assertEqual(governance["skill_state_namespace"], "notes_state")

        reimported = artifact_from_skill_document(exported)
        self.assertIn("virtual_mounts", reimported.content)
        self.assertIn("named_queries", reimported.content)
        self.assertEqual(reimported.content["skill_state_namespace"], "notes_state")

    def test_legacy_ability_export_synthesizes_governed_v2_declaration(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over governed export for legacy executable artifacts, helps with verifying that an older ability exports with a conservative synthesized v2 declaration.

        Reference to Theory:
            Verifies the governed export bridge so legacy abilities can move through the v2 skill interface without losing executable structure.

        Example Input Output:
            Input: `test_legacy_ability_export_synthesizes_governed_v2_declaration()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Open Browser URL",
                "executor": "python3",
                "inputs": {
                    "browser": "browser application name",
                    "url": "target URL",
                },
                "outputs": {
                    "status": "open status",
                },
                "python": (
                    "def main(browser: str, url: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    import webbrowser\n"
                    "    webbrowser.open(url)\n"
                    "    return {'status': 'opened', 'browser': browser, 'url': url}\n"
                ),
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(exported["schema"], "bssc_skill.v2")
        self.assertEqual(exported["kind"], "ability")
        self.assertEqual(exported["executor"], "python3")
        self.assertIn("declaration", exported)
        self.assertEqual(exported["declaration"]["executor_framework"], "python3")
        self.assertIn("execute", exported["declaration"]["authorities_requested"])

    def test_legacy_brokerized_ability_export_uses_governed_authority_hints(self) -> None:
        """
        High Level Purpose:
            In circumstances like exporting a learned Python skill that was already brokerized during markdown learning, helps with verifying that v2 declaration synthesis uses the stored governed authority hints and broker names instead of guessing from raw source text.

        Reference to Theory:
            Verifies the broker-first learning bridge into declaration-first governance so exported skills keep the intended authority and side-effect surface.

        Example Input Output:
            Input: `test_legacy_brokerized_ability_export_uses_governed_authority_hints()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "List Directory Entries",
                "executor": "python3",
                "inputs": {"path": "directory path"},
                "outputs": {"entries": "directory entries"},
                "python": (
                    "from python_skill_host import broker_request\n\n"
                    "def main(path: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:\n"
                    "    result = broker_request(\"fs.list_directory\", path=path)\n"
                    "    if result.get(\"status\") != \"ok\":\n"
                    "        return result\n"
                    "    return {\"status\": \"listed\", \"path\": path, \"entries\": result.get(\"entries\", [])}\n"
                ),
                "governance": {
                    "governed_authorities": ["execute", "read"],
                    "governed_host_brokers": ["fs.list_directory"],
                },
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(exported["schema"], "bssc_skill.v2")
        self.assertEqual(exported["declaration"]["authorities_requested"], ["execute", "read"])
        self.assertIn(
            "brokered host effect via fs.list_directory",
            exported["declaration"]["side_effects"],
        )
        self.assertEqual(exported["governance"]["host_abi_version"], host_abi_version())

    def test_legacy_mount_brokerized_ability_export_infers_derived_data_class_for_skill_tmp(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Write Text File By Mount",
                "executor": "python3",
                "inputs": {"mount": "mount name", "relative_path": "target path", "text": "text to write"},
                "outputs": {"status": "write status"},
                "python": (
                    "from python_skill_host import broker_request\n\n"
                    "def main(mount: str = \"skill_tmp\", *, relative_path: str, text: str, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:\n"
                    "    return broker_request(\"fs.write_mount\", mount=mount, relative_path=relative_path, text=text)\n"
                ),
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(exported["schema"], "bssc_skill.v2")
        self.assertIn("derived", exported["declaration"]["data_classes_touched"])
        self.assertEqual(
            artifact.content["governed_host_brokers"],
            ["fs.write_mount"],
        )
        self.assertEqual(
            exported["governance"]["governed_host_brokers"],
            ["fs.write_mount"],
        )

    def test_legacy_multiline_mount_brokerized_ability_export_infers_write_authority(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Append Text File By Mount",
                "executor": "python3",
                "inputs": {"mount": "mount name", "relative_path": "target path", "text": "text to append"},
                "outputs": {"status": "append status"},
                "python": (
                    "from python_skill_host import broker_request\n\n"
                    "def main(mount: str = \"skill_tmp\", *, relative_path: str, text: str, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:\n"
                    "    result = broker_request(\n"
                    "        \"fs.write_mount\",\n"
                    "        mount=mount,\n"
                    "        relative_path=relative_path,\n"
                    "        text=text,\n"
                    "        append=True,\n"
                    "    )\n"
                    "    return result\n"
                ),
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(exported["schema"], "bssc_skill.v2")
        self.assertIn("write", exported["declaration"]["authorities_requested"])
        self.assertIn("derived", exported["declaration"]["data_classes_touched"])

    def test_legacy_output_only_ability_export_round_trips_empty_runtime_inputs(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "boundary_shape_artifacts"
            / "hi_responder.yaml"
        )
        artifact = load_artifact_yaml_documents(fixture_path)[0]

        exported = skill_export_document(artifact)
        round_tripped = artifact_from_skill_document(exported)

        self.assertEqual(exported["schema"], "bssc_skill.v2")
        self.assertIn("inputs", exported)
        self.assertEqual(exported["inputs"], {})
        self.assertEqual(round_tripped.content.get("input_contract"), {})
        self.assertEqual(round_tripped.content.get("entrypoint"), "run")

    def test_batch_skill_export_filename_is_safe_and_deterministic(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over batch skill export, helps with verifying that exported filenames are deterministic and safe even when titles contain slash-structured segments.

        Reference to Theory:
            Verifies the title-immutable export rule so title identity can remain portable and idempotent without leaking filesystem-hostile title separators into output paths.

        Example Input Output:
            Input: `test_batch_skill_export_filename_is_safe_and_deterministic()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "knowledge",
                "title": "Physics / Force / Force From Mass And Acceleration",
                "answer": "Force equals mass times acceleration.",
            }
        )

        filename = batch_skill_export_filename(artifact)

        self.assertEqual(
            filename,
            f"{stable_skill_artifact_id('Physics / Force / Force From Mass And Acceleration')}.yaml",
        )
        self.assertNotIn("/", filename)

    def test_v2_ability_import_keeps_declaration(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over declaration-first governed skills, helps with verifying that the v2 declaration survives import onto the canonical artifact.

        Reference to Theory:
            Verifies the new declaration-first governed skill form so section-7 declaration fields remain available for admission and replay.

        Example Input Output:
            Input: `test_v2_ability_import_keeps_declaration()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Open Browser URL",
                "executor": "python3",
                "python": (
                    "def main(browser: str, url: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    import webbrowser\n"
                    "    webbrowser.open(url)\n"
                    "    return {'status': 'opened'}\n"
                ),
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {
                        "browser": "browser name",
                        "url": "target URL",
                    },
                    "outputs": {
                        "status": "open status",
                    },
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
            }
        )

        self.assertEqual(artifact.content.get("skill_schema"), "bssc_skill.v2")
        self.assertEqual(artifact.content.get("skill_kind"), "ability")
        self.assertEqual(artifact.content.get("skill_declaration", {}).get("intent"), "Open a browser URL.")
        self.assertEqual(artifact.content.get("skill_declaration", {}).get("risk_tier"), "tier1_bounded_transform")

    def test_v2_policy_import_survives_as_policy_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over policy artifacts, helps with verifying that a policy document imports as a governed record with policy content rather than an invokable user skill.

        Reference to Theory:
            Verifies the policy-artifact abstraction so admission can be evaluated against stored machine-readable policy.

        Example Input Output:
            Input: `test_v2_policy_import_survives_as_policy_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Local Admission Policy",
                "policy": {
                    "intent": "Admit only bounded local abilities.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier2_connected",
                    "allowed_authorities": ["read", "write", "execute", "persist", "export"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {
                        "tier3_sensitive": "operator_approved",
                    },
                },
            }
        )

        self.assertEqual(artifact.artifact_type, ArtifactType.KNOWLEDGE)
        self.assertEqual(artifact.content.get("skill_kind"), "policy")
        self.assertIn("skill_policy", artifact.content)
        self.assertIn("Admit only bounded local abilities", artifact.content.get("answer", ""))

    def test_v2_admission_is_held_without_policy(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over governed admission, helps with verifying that a v2 skill is held when no policy artifact is in force.

        Reference to Theory:
            Verifies the policy-before-admission rule so governed v2 skills do not silently become active without policy.

        Example Input Output:
            Input: `test_v2_admission_is_held_without_policy()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Open Browser URL",
                "executor": "python3",
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened'}\n",
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"status": "open status"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            policy_artifacts=[],
        )
        artifact.content["skill_admission"] = admission

        admitted, reason = artifact_admitted_for_use(artifact)

        self.assertFalse(admitted)
        self.assertIn("No policy artifact", reason)
        self.assertEqual(admission["status"], "held")

    def test_v2_admission_is_admitted_under_matching_policy(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over governed admission, helps with verifying that a v2 skill is admitted when its declaration matches the installed policy artifact.

        Reference to Theory:
            Verifies the policy-artifact plus authority-risk admission check so bounded skills can be admitted deterministically.

        Example Input Output:
            Input: `test_v2_admission_is_admitted_under_matching_policy()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Local Admission Policy",
                "policy": {
                    "intent": "Admit only bounded local abilities.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier2_connected",
                    "allowed_authorities": ["execute", "persist", "export"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Open Browser URL",
                "executor": "python3",
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened'}\n",
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"status": "open status"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            policy_artifacts=[policy_artifact],
        )
        artifact.content["skill_admission"] = admission

        admitted, reason = artifact_admitted_for_use(artifact)

        self.assertTrue(admitted)
        self.assertEqual(reason, "")
        self.assertEqual(admission["status"], "admitted")

    def test_higher_risk_python_skill_with_raw_sqlite_is_held(self) -> None:
        """
        High Level Purpose:
            In circumstances like tightening governed Python admission, helps with verifying that higher-risk Python skills cannot rely on raw sqlite patterns.

        Reference to Theory:
            Verifies the broker-first data-surface rule so sensitive Python skills use named store brokers rather than arbitrary database handles.

        Example Input Output:
            Input: `test_higher_risk_python_skill_with_raw_sqlite_is_held()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Python Admission Policy",
                "policy": {
                    "intent": "Admit higher-risk Python abilities only when governance rules hold.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "read", "persist"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Read Sensitive SQLite",
                "executor": "python3",
                "python": (
                    "def main(database_path: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    import sqlite3\n"
                    "    connection = sqlite3.connect(database_path)\n"
                    "    try:\n"
                    "        return {'status': 'ok'}\n"
                    "    finally:\n"
                    "        connection.close()\n"
                ),
                "declaration": {
                    "intent": "Read governed sqlite data.",
                    "inputs": {"database_path": "sqlite path"},
                    "outputs": {"status": "operation status"},
                    "authorities_requested": ["execute", "read"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "read": {
                            "scope": "internal_store",
                            "target": "sqlite_database",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["internal"],
                    "side_effects": ["read sqlite data"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier3_sensitive",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            skill_content=artifact.content,
            policy_artifacts=[policy_artifact],
        )

        self.assertEqual(admission["status"], "held")
        self.assertIn("Higher-risk Python skills must use governed host ABI surfaces", admission["rationale"])
        self.assertIn("raw sqlite access", admission["rationale"])

    def test_higher_risk_python_skill_with_raw_network_access_is_held(self) -> None:
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Python Admission Policy",
                "policy": {
                    "intent": "Admit higher-risk Python abilities only when governance rules hold.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "communicate"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Fetch Sensitive Remote Data",
                "executor": "python3",
                "python": (
                    "def main(url: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    import requests\n"
                    "    return requests.get(url, timeout=5).json()\n"
                ),
                "declaration": {
                    "intent": "Fetch remote JSON from a sensitive Python skill.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"payload": "remote payload"},
                    "authorities_requested": ["execute", "communicate"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "communicate": {
                            "scope": "remote_http",
                            "target": "allowlisted_domain",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["remote HTTP read"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier3_sensitive",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            skill_content=artifact.content,
            policy_artifacts=[policy_artifact],
        )

        self.assertEqual(admission["status"], "held")
        self.assertIn("raw network access", admission["rationale"])

    def test_higher_risk_python_skill_with_raw_process_invocation_is_held(self) -> None:
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Python Admission Policy",
                "policy": {
                    "intent": "Admit higher-risk Python abilities only when governance rules hold.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Run Sensitive Process",
                "executor": "python3",
                "python": (
                    "def main(command: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    import subprocess\n"
                    "    return {'status': subprocess.run(command, shell=True, capture_output=True, text=True).stdout}\n"
                ),
                "declaration": {
                    "intent": "Run an external process from a sensitive Python skill.",
                    "inputs": {"command": "command text"},
                    "outputs": {"status": "command stdout"},
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
                    "side_effects": ["process launch"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier3_sensitive",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            skill_content=artifact.content,
            policy_artifacts=[policy_artifact],
        )

        self.assertEqual(admission["status"], "held")
        self.assertIn("raw tool or process invocation", admission["rationale"])

    def test_higher_risk_python_skill_with_transitional_broker_is_held(self) -> None:
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Python Admission Policy",
                "policy": {
                    "intent": "Admit higher-risk Python abilities only when governance rules hold.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "read"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Read Transitional Broker Surface",
                "executor": "python3",
                "python": (
                    "from python_skill_host import broker_request\n\n"
                    "def main(path: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    return broker_request(\n"
                    "        'fs.read_text',\n"
                    "        path=path,\n"
                    "    )\n"
                ),
                "declaration": {
                    "intent": "Read a file through a governed broker.",
                    "inputs": {"path": "target file path"},
                    "outputs": {"text": "file contents"},
                    "authorities_requested": ["execute", "read"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "read": {
                            "scope": "governed_mount_surface",
                            "target": "virtual_mount",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["internal"],
                    "side_effects": ["read mounted file"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier3_sensitive",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            skill_content=artifact.content,
            policy_artifacts=[policy_artifact],
        )

        self.assertEqual(admission["status"], "held")
        self.assertIn("stable governed host ABI brokers", admission["rationale"])
        self.assertIn("fs.read_text", admission["rationale"])

    def test_higher_risk_python_skill_with_governed_store_surface_is_admitted(self) -> None:
        """
        High Level Purpose:
            In circumstances like tightening governed Python admission, helps with verifying that a higher-risk Python skill can still be admitted when it uses the governed store broker surfaces instead of raw sqlite.

        Reference to Theory:
            Verifies the broker-first store rule so named queries and namespaced skill state remain the approved persistence surfaces for sensitive Python skills.

        Example Input Output:
            Input: `test_higher_risk_python_skill_with_governed_store_surface_is_admitted()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Python Admission Policy",
                "policy": {
                    "intent": "Admit higher-risk Python abilities only when governance rules hold.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "read", "persist"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Read Governed Store State",
                "executor": "python3",
                "python": (
                    "from python_skill_host import broker_request\n\n"
                    "def main(query_name: str, wanted: int, __dependencies__: tuple[str, ...] = ()):\n"
                    "    rows = broker_request('store.named_query', query_name=query_name, parameters={'wanted': wanted})\n"
                    "    state = broker_request('store.skill_state', operation='put', key='last_wanted', value={'wanted': wanted})\n"
                    "    return {'status': rows.get('status'), 'state_status': state.get('status')}\n"
                ),
                "declaration": {
                    "intent": "Read governed store data and persist governed skill state.",
                    "inputs": {"query_name": "registered query", "wanted": "parameter value"},
                    "outputs": {"status": "query status"},
                    "authorities_requested": ["execute", "read", "persist"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "python3_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "read": {
                            "scope": "internal_store",
                            "target": "named_query",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                        "persist": {
                            "scope": "skill_state",
                            "target": "namespaced_state",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        },
                    },
                    "data_classes_touched": ["internal", "derived"],
                    "side_effects": ["named query read", "skill state write"],
                    "persistence_behavior": "skill_state",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier3_sensitive",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            skill_content=artifact.content,
            policy_artifacts=[policy_artifact],
        )

        self.assertEqual(admission["status"], "admitted")

    def test_v2_export_synthesizes_active_lifecycle_from_admission(self) -> None:
        """
        High Level Purpose:
            In circumstances like exporting governed skills that were admitted before explicit lifecycle state existed, helps with verifying that export emits a usable lifecycle block instead of silently omitting current runtime state.

        Reference to Theory:
            Verifies the lifecycle bridge so activation and trust become portable parts of governed skill state rather than local assumptions.

        Example Input Output:
            Input: `test_v2_export_synthesizes_active_lifecycle_from_admission()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Open Browser URL",
                "executor": "python3",
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened'}\n",
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"status": "open status"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
            }
        )
        artifact.content["skill_admission"] = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Declaration satisfied installed policy constraints and required no additional approval.",
            "policy_titles": ["Local Admission Policy"],
            "required_approval_class": "automatic",
            "evaluated_at": "2026-03-31T12:00:00+00:00",
        }

        exported = skill_export_document(artifact)

        self.assertIn("lifecycle", exported)
        self.assertEqual(exported["lifecycle"]["admission_status"], "admitted")
        self.assertEqual(exported["lifecycle"]["activation_status"], "active")
        self.assertEqual(exported["lifecycle"]["trust_status"], "trusted")

    def test_explicit_lifecycle_can_deactivate_admitted_v2_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed import of a temporarily disabled skill, helps with verifying that activation state remains distinct from admission and blocks invocation when inactive.

        Reference to Theory:
            Verifies open governance section 9 by preventing admitted governed skills from being treated as runnable when lifecycle activation is inactive.

        Example Input Output:
            Input: `test_explicit_lifecycle_can_deactivate_admitted_v2_skill()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Paused Browser URL",
                "executor": "python3",
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened'}\n",
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"status": "open status"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
                "lifecycle": {
                    "activation_status": "inactive",
                    "trust_status": "trusted",
                },
            }
        )
        artifact.content["skill_admission"] = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Declaration satisfied installed policy constraints and required no additional approval.",
            "policy_titles": ["Local Admission Policy"],
            "required_approval_class": "automatic",
            "evaluated_at": "2026-03-31T12:00:00+00:00",
        }

        admitted, reason = artifact_admitted_for_use(artifact)

        self.assertFalse(admitted)
        self.assertIn("activation status is inactive", reason)

    def test_v2_executable_skill_without_execute_authority_is_held(self) -> None:
        """
        High Level Purpose:
            In circumstances like importing governed executable skills that request broker or host effects, helps with verifying that the declaration must still include execute authority for the runtime boundary itself.

        Reference to Theory:
            Verifies declaration-first governance by preventing executable v2 skills from being admitted when they omit the authority needed to cross their own executor boundary.

        Example Input Output:
            Input: `test_v2_executable_skill_without_execute_authority_is_held()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Local Admission Policy",
                "policy": {
                    "intent": "Admit bounded local abilities with declared execution authority.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier2_connected",
                    "allowed_authorities": ["execute", "write"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Brokered File Write",
                "executor": "python3",
                "python": (
                    "def main(path: str, text: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    return {'status': 'ok'}\n"
                ),
                "declaration": {
                    "intent": "Write a file through a governed broker.",
                    "inputs": {"path": "target path", "text": "text to write"},
                    "outputs": {"status": "write status"},
                    "authorities_requested": ["write"],
                    "authority_bounds": {
                        "write": {
                            "scope": "local_host",
                            "target": "filesystem_text_file",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["filesystem write through broker"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            kind="ability",
            executor_framework="python3",
            policy_artifacts=[policy_artifact],
        )

        self.assertEqual(admission["status"], "held")
        self.assertFalse(admission["admitted"])
        self.assertIn("must declare execute authority", admission["rationale"])

    def test_v2_skill_requiring_operator_approval_is_held_without_approval_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like policy-governed higher-risk skill import, helps with verifying that non-automatic approval requirements remain held until a matching approval artifact exists.

        Reference to Theory:
            Verifies open governance section 13 by preventing policy-required approval from collapsing into admission without explicit approval evidence.

        Example Input Output:
            Input: `test_v2_skill_requiring_operator_approval_is_held_without_approval_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Admission Policy",
                "policy": {
                    "intent": "Require operator approval for sensitive abilities.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "communicate"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {
                        "tier3_sensitive": "operator_approved",
                    },
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Open External Browser URL",
                "executor": "python3",
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened'}\n",
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"status": "open status"},
                    "authorities_requested": ["execute", "communicate"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "operator_approved",
                        },
                        "communicate": {
                            "scope": "external_network",
                            "target": "browser_navigation",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "operator_approved",
                        },
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser", "network communication"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["operator_approved"],
                    "risk_tier": "tier3_sensitive",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            skill_title=artifact.title,
            kind="ability",
            executor_framework="python3",
            policy_artifacts=[policy_artifact],
            approval_artifacts=[],
        )

        self.assertEqual(admission["status"], "held")
        self.assertFalse(admission["admitted"])
        self.assertEqual(admission["required_approval_class"], "operator_approved")
        self.assertEqual(admission["approval_titles"], [])
        self.assertIn("requires explicit approval class operator_approved", admission["rationale"])

    def test_v2_skill_requiring_operator_approval_is_admitted_with_matching_approval_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like policy-governed higher-risk skill import, helps with verifying that a matching approval artifact can satisfy the non-automatic approval requirement and admit the skill.

        Reference to Theory:
            Verifies open governance section 13 by turning approval artifacts into real admission evidence instead of static metadata.

        Example Input Output:
            Input: `test_v2_skill_requiring_operator_approval_is_admitted_with_matching_approval_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        policy_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Sensitive Admission Policy",
                "policy": {
                    "intent": "Require operator approval for sensitive abilities.",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier3_sensitive",
                    "allowed_authorities": ["execute", "communicate"],
                    "denied_authorities": ["approve", "modify", "escalate"],
                    "allowed_executors": ["python3"],
                    "required_approval_for_risk_tiers": {
                        "tier3_sensitive": "operator_approved",
                    },
                },
            }
        )
        approval_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "approval",
                "title": "Operator Approval For External Browser URL",
                "approval": {
                    "intent": "Approve external browser opening for the named skill.",
                    "approval_class": "operator_approved",
                    "subject_titles": ["Open External Browser URL"],
                    "subject_kinds": ["ability"],
                    "approved_authorities": ["execute", "communicate"],
                    "approved_risk_tiers": ["tier3_sensitive"],
                    "issued_by": "operator://local-admin",
                    "rationale": "Operator approved bounded browser launch with external navigation.",
                    "status": "approved",
                },
            }
        )
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Open External Browser URL",
                "executor": "python3",
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened'}\n",
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"status": "open status"},
                    "authorities_requested": ["execute", "communicate"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "operator_approved",
                        },
                        "communicate": {
                            "scope": "external_network",
                            "target": "browser_navigation",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "operator_approved",
                        },
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser", "network communication"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["operator_approved"],
                    "risk_tier": "tier3_sensitive",
                },
            }
        )

        admission = evaluate_skill_admission(
            artifact.content.get("skill_declaration", {}),
            skill_title=artifact.title,
            kind="ability",
            executor_framework="python3",
            policy_artifacts=[policy_artifact],
            approval_artifacts=[approval_artifact],
        )
        artifact.content["skill_admission"] = admission

        admitted, reason = artifact_admitted_for_use(artifact)

        self.assertTrue(admission["admitted"])
        self.assertEqual(admission["status"], "admitted")
        self.assertEqual(admission["approval_titles"], ["Operator Approval For External Browser URL"])
        self.assertTrue(admitted)
        self.assertEqual(reason, "")

    def test_v2_approval_artifact_exports_as_approval_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like exporting governed approval evidence, helps with verifying that approval artifacts remain approval records instead of being projected as ordinary skill declarations.

        Reference to Theory:
            Verifies open governance sections 6 and 13 by preserving approval as a governed artifact in its own right.

        Example Input Output:
            Input: `test_v2_approval_artifact_exports_as_approval_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "approval",
                "title": "Operator Approval For Open Browser URL",
                "approval": {
                    "intent": "Approve browser opening for the named skill.",
                    "approval_class": "operator_approved",
                    "subject_titles": ["Open Browser URL"],
                    "subject_kinds": ["ability"],
                    "approved_authorities": ["execute"],
                    "issued_by": "operator://local-admin",
                    "rationale": "Operator approved local browser launch.",
                    "status": "approved",
                },
            }
        )
        artifact.content["skill_admission"] = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Approval artifacts are admitted governance records.",
            "policy_titles": [],
            "approval_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": "2026-03-31T12:00:00+00:00",
        }

        exported = skill_export_document(artifact)
        admitted, reason = artifact_admitted_for_use(artifact)

        self.assertEqual(exported["kind"], "approval")
        self.assertIn("approval", exported)
        self.assertNotIn("declaration", exported)
        self.assertFalse(admitted)
        self.assertIn("Approval artifacts", reason)

    def test_v2_revocation_artifact_exports_as_revocation_record(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "revocation",
                "title": "Revoke Open Browser URL",
                "revocation": {
                    "intent": "Withdraw trust from the named browser skill.",
                    "subject_titles": ["Open Browser URL"],
                    "subject_kinds": ["ability"],
                    "trust_status": "revoked",
                    "quarantine_status": "clear",
                    "activation_status": "inactive",
                    "installation_status": "blocked",
                    "status": "active",
                    "issued_by": "operator://local-admin",
                    "rationale": "The skill is revoked pending review.",
                },
            }
        )

        exported = skill_export_document(artifact)
        admitted, reason = artifact_admitted_for_use(artifact)

        self.assertEqual(exported["kind"], "revocation")
        self.assertIn("revocation", exported)
        self.assertEqual(exported["revocation"]["subject_titles"], ["Open Browser URL"])
        self.assertNotIn("declaration", exported)
        self.assertFalse(admitted)
        self.assertIn("Revocation artifacts", reason)

    def test_v2_incident_artifact_exports_as_incident_record(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "incident",
                "title": "Incident On Open Browser URL",
                "incident": {
                    "intent": "Suspend the named browser skill during an incident.",
                    "subject_titles": ["Open Browser URL"],
                    "subject_kinds": ["ability"],
                    "severity": "high",
                    "enforcement_action": "suspend",
                    "status": "open",
                    "issued_by": "operator://local-admin",
                    "rationale": "Unexpected behavior requires temporary suspension.",
                },
            }
        )

        exported = skill_export_document(artifact)
        admitted, reason = artifact_admitted_for_use(artifact)

        self.assertEqual(exported["kind"], "incident")
        self.assertIn("incident", exported)
        self.assertEqual(exported["incident"]["enforcement_action"], "suspend")
        self.assertNotIn("declaration", exported)
        self.assertFalse(admitted)
        self.assertIn("Incident artifacts", reason)

    def test_skill_registry_document_reflects_current_revocation_overlay(self) -> None:
        skill = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Open Browser URL",
                "executor": "python3",
                "python": "def main(url: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'opened', 'url': url}\n",
                "declaration": {
                    "intent": "Open a browser URL.",
                    "inputs": {"url": "target URL"},
                    "outputs": {"status": "open status"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_desktop",
                            "target": "browser_application",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["launch browser"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                },
                "admission": {
                    "status": "admitted",
                    "admitted": True,
                    "rationale": "Matched local admission policy.",
                    "policy_titles": ["Local Admission Policy"],
                    "required_approval_class": "automatic",
                    "evaluated_at": "2026-04-02T00:00:00Z",
                },
            }
        )
        revocation = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "revocation",
                "title": "Revoke Open Browser URL",
                "revocation": {
                    "intent": "Withdraw trust from the named browser skill.",
                    "subject_titles": ["Open Browser URL"],
                    "subject_kinds": ["ability"],
                    "trust_status": "revoked",
                    "quarantine_status": "clear",
                    "activation_status": "inactive",
                    "installation_status": "blocked",
                    "status": "active",
                    "issued_by": "operator://local-admin",
                    "rationale": "The skill is revoked pending review.",
                },
            }
        )

        registry = skill_registry_document([skill, revocation])
        by_title = {entry["title"]: entry for entry in registry["entries"]}

        self.assertEqual(registry["schema"], "bssc_skill_registry.v1")
        self.assertEqual(registry["entry_count"], 2)
        self.assertEqual(by_title["Open Browser URL"]["trust_status"], "revoked")
        self.assertEqual(by_title["Open Browser URL"]["activation_status"], "inactive")
        self.assertEqual(by_title["Open Browser URL"]["revocation_titles"], ["Revoke Open Browser URL"])

    def test_skill_registry_document_projects_canonical_hosted_metadata(self) -> None:
        skill = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Python Commands 03 — Write Text File / Python Commands 03 Write Text File",
                "executor": "python3",
                "inputs": {"text": "text to write"},
                "outputs": {"status": "write status"},
                "python": "def main(text: str, __dependencies__: tuple[str, ...] = ()): return {'status': 'ok', 'text': text}\n",
                "compatibility": {
                    "adapters": [
                        {
                            "direction": "import",
                            "format": "openai_tool",
                            "surface": "function",
                            "name": "write_text_file",
                        }
                    ]
                },
            }
        )

        registry = skill_registry_document([skill])
        entry = registry["entries"][0]

        self.assertEqual(entry["family"]["label"], "Python Commands")
        self.assertEqual(entry["alias_count"], 1)
        self.assertEqual(entry["compatibility_formats"], ["openai_tool"])
        self.assertIn("a", entry["normalized_regions"])
        self.assertIn("d", entry["normalized_regions"])
        self.assertEqual(entry["normalization_leaf_counts"]["a"], 1)
        self.assertEqual(entry["normalization_leaf_counts"]["d"], 1)
        self.assertEqual(entry["hosting_metadata"]["executor_framework"], "python3")
        self.assertEqual(entry["hosting_metadata"]["representation"], "python_script")
        self.assertEqual(entry["hosting_metadata"]["entrypoint"], "main")

    def test_v2_export_includes_declaration_and_admission(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over governed skill export, helps with verifying that v2 export includes the declaration and the locally evaluated admission state.

        Reference to Theory:
            Verifies the declaration-first export shape so review and replay can see both the declared skill and the admission outcome.

        Example Input Output:
            Input: `test_v2_export_includes_declaration_and_admission()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "knowledge",
                "title": "What Is Force?",
                "question": "What is force?",
                "answer": "Force equals mass times acceleration.",
                "declaration": {
                    "intent": "State the force relation.",
                    "inputs": {"question": "knowledge prompt"},
                    "outputs": {"answer": "knowledge answer"},
                    "authorities_requested": ["read"],
                    "authority_bounds": {
                        "read": {
                            "scope": "local_skill_store",
                            "target": "knowledge_artifact",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["none"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier0_passive",
                },
            }
        )
        artifact.content["skill_admission"] = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Matched local admission policy.",
            "policy_titles": ["Local Admission Policy"],
            "required_approval_class": "automatic",
            "evaluated_at": "2026-03-31T00:00:00Z",
        }

        exported = skill_export_document(artifact)

        self.assertEqual(exported["schema"], "bssc_skill.v2")
        self.assertEqual(exported["kind"], "knowledge")
        self.assertIn("declaration", exported)
        self.assertIn("admission", exported)
        self.assertEqual(exported["admission"]["status"], "admitted")

    def test_import_skill_command_applies_policy_before_persisting_v2_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed CLI import of a policy and a v2 skill bundle, helps with verifying that policy artifacts are installed first and the dependent skill is persisted with an admitted status.

        Reference to Theory:
            Verifies the policy-artifact plus admission loop so governed skills do not enter the store without being evaluated against installed policy.

        Example Input Output:
            Input: `test_import_skill_command_applies_policy_before_persisting_v2_skill()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        skill_file = Path(self.tempdir.name) / "governed_skill_bundle.yaml"
        skill_file.write_text(
            "\n---\n".join(
                [
                    "\n".join(
                        [
                            "schema: bssc_skill.v2",
                            "kind: policy",
                            "title: Local Admission Policy",
                            "policy:",
                            "  intent: Admit only bounded local abilities.",
                            "  target_kinds:",
                            "    - ability",
                            "  max_risk_tier: tier2_connected",
                            "  allowed_authorities:",
                            "    - execute",
                            "  denied_authorities:",
                            "    - approve",
                            "    - modify",
                            "    - escalate",
                            "  allowed_executors:",
                            "    - python3",
                            "  required_approval_for_risk_tiers: {}",
                        ]
                    ),
                    "\n".join(
                        [
                            "schema: bssc_skill.v2",
                            "kind: ability",
                            "title: Open Browser URL",
                            "executor: python3",
                            "python: |",
                            "  def main(url: str, __dependencies__: tuple[str, ...] = ()):",
                            "      return {'status': 'opened', 'url': url}",
                            "declaration:",
                            "  intent: Open a browser URL.",
                            "  inputs:",
                            "    url: target URL",
                            "  outputs:",
                            "    status: open status",
                            "  authorities_requested:",
                            "    - execute",
                            "  authority_bounds:",
                            "    execute:",
                            "      scope: local_desktop",
                            "      target: browser_application",
                            "      context: explicit_user_prompt",
                            "      duration: single_invocation",
                            "      triggering_conditions:",
                            "        - user invokes skill",
                            "      approval_class: automatic",
                            "  data_classes_touched: []",
                            "  side_effects:",
                            "    - launch browser",
                            "  persistence_behavior: none",
                            "  invocation_rights:",
                            "    - direct_user_invocation",
                            "  composition_rights: []",
                            "  escalation_rights: []",
                            "  approval_requirements:",
                            "    - automatic",
                            "  risk_tier: tier1_bounded_transform",
                        ]
                    ),
                ]
            )
            + "\n"
        )
        args = argparse.Namespace(
            skill_file=[skill_file],
            skill_files_file=None,
            skill_dir=None,
            normalized_out=None,
            normalized_out_dir=None,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = handle_import_skill_command(args)

        self.assertEqual(result, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["imported_count"], 2)
        imported_by_title = {item["title"]: item for item in payload["imported"]}
        self.assertEqual(imported_by_title["Open Browser URL"]["admission_status"], "admitted")
        self.assertEqual(imported_by_title["Local Admission Policy"]["admission_status"], "admitted")

        store = build_artifact_store()
        artifacts = {artifact.title: artifact for artifact in store.load_all_artifacts()}
        self.assertIn("Local Admission Policy", artifacts)
        self.assertIn("Open Browser URL", artifacts)
        self.assertEqual(
            artifacts["Open Browser URL"].content.get("skill_admission", {}).get("status"),
            "admitted",
        )

    def test_import_skill_command_applies_approval_before_persisting_approval_gated_v2_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed CLI import of policy, approval, and a gated v2 skill bundle, helps with verifying that approval artifacts are installed before the dependent skill is evaluated.

        Reference to Theory:
            Verifies open governance section 13 operationally by proving that explicit approval records can satisfy policy-required approval during import.

        Example Input Output:
            Input: `test_import_skill_command_applies_approval_before_persisting_approval_gated_v2_skill()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        skill_file = Path(self.tempdir.name) / "governed_approval_bundle.yaml"
        skill_file.write_text(
            "\n---\n".join(
                [
                    "\n".join(
                        [
                            "schema: bssc_skill.v2",
                            "kind: policy",
                            "title: Sensitive Admission Policy",
                            "policy:",
                            "  intent: Require operator approval for sensitive abilities.",
                            "  target_kinds:",
                            "    - ability",
                            "  max_risk_tier: tier3_sensitive",
                            "  allowed_authorities:",
                            "    - execute",
                            "    - communicate",
                            "  denied_authorities:",
                            "    - approve",
                            "    - modify",
                            "    - escalate",
                            "  allowed_executors:",
                            "    - python3",
                            "  required_approval_for_risk_tiers:",
                            "    tier3_sensitive: operator_approved",
                        ]
                    ),
                    "\n".join(
                        [
                            "schema: bssc_skill.v2",
                            "kind: approval",
                            "title: Operator Approval For External Browser URL",
                            "approval:",
                            "  intent: Approve external browser opening for the named skill.",
                            "  approval_class: operator_approved",
                            "  subject_titles:",
                            "    - Open External Browser URL",
                            "  subject_kinds:",
                            "    - ability",
                            "  approved_authorities:",
                            "    - execute",
                            "    - communicate",
                            "  approved_risk_tiers:",
                            "    - tier3_sensitive",
                            "  issued_by: operator://local-admin",
                            "  rationale: Operator approved bounded browser launch with external navigation.",
                            "  status: approved",
                        ]
                    ),
                    "\n".join(
                        [
                            "schema: bssc_skill.v2",
                            "kind: ability",
                            "title: Open External Browser URL",
                            "executor: python3",
                            "python: |",
                            "  def main(url: str, __dependencies__: tuple[str, ...] = ()):",
                            "      return {'status': 'opened', 'url': url}",
                            "declaration:",
                            "  intent: Open a browser URL.",
                            "  inputs:",
                            "    url: target URL",
                            "  outputs:",
                            "    status: open status",
                            "  authorities_requested:",
                            "    - execute",
                            "    - communicate",
                            "  authority_bounds:",
                            "    execute:",
                            "      scope: local_desktop",
                            "      target: browser_application",
                            "      context: explicit_user_prompt",
                            "      duration: single_invocation",
                            "      triggering_conditions:",
                            "        - user invokes skill",
                            "      approval_class: operator_approved",
                            "    communicate:",
                            "      scope: external_network",
                            "      target: browser_navigation",
                            "      context: explicit_user_prompt",
                            "      duration: single_invocation",
                            "      triggering_conditions:",
                            "        - user invokes skill",
                            "      approval_class: operator_approved",
                            "  data_classes_touched:",
                            "    - public",
                            "  side_effects:",
                            "    - launch browser",
                            "    - network communication",
                            "  persistence_behavior: none",
                            "  invocation_rights:",
                            "    - direct_user_invocation",
                            "  composition_rights: []",
                            "  escalation_rights: []",
                            "  approval_requirements:",
                            "    - operator_approved",
                            "  risk_tier: tier3_sensitive",
                        ]
                    ),
                ]
            )
            + "\n"
        )

        args = argparse.Namespace(
            skill_file=[skill_file],
            skill_files_file=None,
            skill_dir=None,
            normalized_out=None,
            normalized_out_dir=None,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = handle_import_skill_command(args)

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["imported_count"], 3)

        store = build_artifact_store()
        artifacts = {artifact.title: artifact for artifact in store.load_all_artifacts()}
        self.assertEqual(
            artifacts["Open External Browser URL"].content.get("skill_admission", {}).get("status"),
            "admitted",
        )
        self.assertEqual(
            artifacts["Open External Browser URL"].content.get("skill_admission", {}).get("approval_titles"),
            ["Operator Approval For External Browser URL"],
        )

    def test_import_skill_command_reports_timings_and_marks_unchanged_reimport(self) -> None:
        skill_file = Path(self.tempdir.name) / "knowledge_skill.yaml"
        skill_file.write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v2",
                    "kind: knowledge",
                    "title: What Is Force?",
                    "question: What is force?",
                    "answer: Force equals mass times acceleration.",
                    "declaration:",
                    "  intent: Answer what force is.",
                    "  inputs: {}",
                    "  outputs:",
                    "    answer: explanation",
                    "  authorities_requested: []",
                    "  authority_bounds: {}",
                    "  data_classes_touched: []",
                    "  side_effects: []",
                    "  persistence_behavior: none",
                    "  invocation_rights:",
                    "    - direct_user_invocation",
                    "  composition_rights: []",
                    "  escalation_rights: []",
                    "  approval_requirements:",
                    "    - automatic",
                    "  risk_tier: tier0_readonly",
                    "",
                ]
            )
        )
        args = argparse.Namespace(
            skill_file=[skill_file],
            skill_files_file=None,
            skill_dir=None,
            normalized_out=None,
            normalized_out_dir=None,
        )

        first_stdout = io.StringIO()
        with redirect_stdout(first_stdout):
            first_exit_code = handle_import_skill_command(args)
        self.assertEqual(first_exit_code, 0)
        first_payload = json.loads(first_stdout.getvalue())
        self.assertIn("timings", first_payload)
        self.assertIn("store_report", first_payload)
        self.assertIn("timings", first_payload["store_report"])
        self.assertIn("compiler_summary", first_payload)
        self.assertEqual(first_payload["compiler_summary"]["schema"], "bssc_skill.v2")
        self.assertEqual(first_payload["store_report"]["status"], "persisted")

        second_stdout = io.StringIO()
        with redirect_stdout(second_stdout):
            second_exit_code = handle_import_skill_command(args)
        self.assertEqual(second_exit_code, 0)
        second_payload = json.loads(second_stdout.getvalue())
        self.assertIn("compiler_summary", second_payload)
        self.assertEqual(second_payload["store_report"]["status"], "unchanged")
        self.assertGreaterEqual(float(second_payload["timings"]["total_seconds"]), 0.0)
        self.assertGreaterEqual(float(second_payload["store_report"]["timings"]["total_seconds"]), 0.0)

    def test_batch_import_skill_command_reports_persist_summaries_and_governance_snapshot(self) -> None:
        skill_file = Path(self.tempdir.name) / "batch_skill_bundle.yaml"
        skill_file.write_text(
            "\n---\n".join(
                [
                    "\n".join(
                        [
                            "schema: bssc_skill.v2",
                            "kind: policy",
                            "title: Local Admission Policy",
                            "policy:",
                            "  intent: Allow low-risk local skills.",
                            "  target_kinds:",
                            "    - ability",
                            "    - knowledge",
                            "  max_risk_tier: tier1_bounded_transform",
                            "  allowed_authorities: []",
                            "  denied_authorities: []",
                            "  allowed_executors: []",
                            "  required_approval_for_risk_tiers: {}",
                        ]
                    ),
                    "\n".join(
                        [
                            "schema: bssc_skill.v2",
                            "kind: knowledge",
                            "title: What Is Momentum?",
                            "question: What is momentum?",
                            "answer: Momentum equals mass times velocity.",
                            "declaration:",
                            "  intent: Answer what momentum is.",
                            "  inputs: {}",
                            "  outputs:",
                            "    answer: explanation",
                            "  authorities_requested: []",
                            "  authority_bounds: {}",
                            "  data_classes_touched: []",
                            "  side_effects: []",
                            "  persistence_behavior: none",
                            "  invocation_rights:",
                            "    - direct_user_invocation",
                            "  composition_rights: []",
                            "  escalation_rights: []",
                            "  approval_requirements:",
                            "    - automatic",
                            "  risk_tier: tier0_readonly",
                        ]
                    ),
                ]
            )
            + "\n"
        )
        args = argparse.Namespace(
            skill_file=[skill_file],
            skill_files_file=None,
            skill_dir=None,
            normalized_out=None,
            normalized_out_dir=None,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = handle_import_skill_command(args)

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["imported_count"], 2)
        self.assertIn("timings", payload)
        self.assertIn("persist_summaries", payload)
        self.assertIn("governance_snapshot", payload)
        self.assertIn("policy", payload["persist_summaries"])
        self.assertIn("skill", payload["persist_summaries"])
        self.assertEqual(payload["governance_snapshot"]["policy_count"], 1)

    def test_export_skill_bundle_text_prepends_local_policy_and_imports_as_admitted_bundle(self) -> None:
        ability_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Write Hello",
                "executor": "python3",
                "inputs": {},
                "outputs": {"status": "write status"},
                "python": (
                    "def main(__dependencies__: tuple[str, ...] = ()):\n"
                    "    return {'status': 'ok'}\n"
                ),
            }
        )

        bundle_text = export_skill_bundle_text([ability_artifact])
        documents = [document for document in yaml.safe_load_all(bundle_text) if isinstance(document, dict)]

        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0]["kind"], "policy")
        self.assertEqual(documents[1]["kind"], "ability")

        skill_file = Path(self.tempdir.name) / "bundle.yaml"
        skill_file.write_text(bundle_text)
        args = argparse.Namespace(
            skill_file=[skill_file],
            skill_files_file=None,
            skill_dir=None,
            normalized_out=None,
            normalized_out_dir=None,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = handle_import_skill_command(args)

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        imported_by_title = {item["title"]: item for item in payload["imported"]}
        self.assertEqual(imported_by_title["Write Hello"]["admission_status"], "admitted")

    def test_export_skill_bundle_text_skips_non_survivable_internal_knowledge_artifacts(self) -> None:
        unsupported_internal_artifact = Artifact(
            id="artifact-closure-pattern",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Direct closure pattern for learned_reuse",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="test",
            justification="test fixture",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "skill_schema": "bssc_skill.v2",
                "skill_kind": "closure_pattern",
                "question": "What closure pattern applies?",
            },
        )
        ability_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Say Hi",
                "executor": "python3",
                "inputs": {},
                "outputs": {"message": "reply"},
                "python": (
                    "def main(__dependencies__: tuple[str, ...] = ()):\n"
                    "    return {'message': 'hi'}\n"
                ),
            }
        )

        bundle_text = export_skill_bundle_text([unsupported_internal_artifact, ability_artifact])
        documents = [document for document in yaml.safe_load_all(bundle_text) if isinstance(document, dict)]
        titles = [document.get("title", "") for document in documents]

        self.assertIn("Say Hi", titles)
        self.assertNotIn("Direct closure pattern for learned_reuse", titles)

    def test_export_skill_bundle_text_strips_skill_runtime_state_from_non_governance_docs(self) -> None:
        governed_artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Bundle Fresh Install Demo",
                "executor": "python3",
                "declaration": {
                    "intent": "Return a status payload.",
                    "inputs": {},
                    "outputs": {"status": "reply"},
                    "authorities_requested": ["execute.python3"],
                    "data_classes_touched": [],
                    "side_effects": [],
                    "persistence_behavior": "none",
                    "invocation_rights": "owner_only",
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": {"required_approval_class": "automatic"},
                    "risk_tier": "tier1_local",
                },
                "admission": {
                    "status": "held",
                    "reason": "stale",
                    "policy_titles": [],
                    "approval_titles": [],
                    "required_approval_class": "automatic",
                    "evaluated_at": "2026-04-02T00:00:00+00:00",
                },
                "lifecycle": {
                    "activation_status": "inactive",
                    "trust_status": "restricted",
                },
                "inputs": {},
                "outputs": {"status": "reply"},
                "python": (
                    "def main(__dependencies__: tuple[str, ...] = ()):\n"
                    "    return {'status': 'ok'}\n"
                ),
            }
        )

        bundle_text = export_skill_bundle_text([governed_artifact])
        documents = [document for document in yaml.safe_load_all(bundle_text) if isinstance(document, dict)]
        self.assertEqual(len(documents), 2)
        ability_document = documents[1]
        self.assertEqual(ability_document["kind"], "ability")
        self.assertNotIn("admission", ability_document)
        self.assertNotIn("lifecycle", ability_document)


if __name__ == "__main__":
    unittest.main()
