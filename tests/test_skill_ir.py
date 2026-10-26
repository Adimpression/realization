# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from applied_theory_types import Artifact
from skill_export_projection import skill_export_document
from skill_ir import (
    canonical_skill_ir_dict_from_artifact,
    canonical_skill_ir_from_artifact,
    normalized_skill_aliases,
    normalized_skill_family_metadata,
)
from skill_schema_io import artifact_from_skill_document


class SkillIrTests(unittest.TestCase):
    def test_canonical_skill_ir_artifact_projection_matches_golden_document(self) -> None:
        artifact = Artifact.from_dict(
            {
                "id": "artifact-golden",
                "title": (
                    "Python Commands 02 — Read Text File / "
                    "Python Commands 02 Read Text File"
                ),
                "artifact_type": "ability",
                "representation": "python_script",
                "content": {
                    "skill_schema": "bssc_skill.v2",
                    "skill_kind": "ability",
                    "skill_declaration": {
                        "intent": "Read text file",
                        "inputs": {"path": "String"},
                        "outputs": {"text": "String"},
                    },
                    "skill_normalization": {
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
                                        "value": "example",
                                        "leaf_class": "scalar",
                                    }
                                ],
                            }
                        }
                    },
                    "aliases": ["Read Text File"],
                    "skill_compatibility": {
                        "adapters": [
                            {
                                "direction": "import",
                                "format": "openai_tool",
                                "name": "read_text",
                            }
                        ]
                    },
                    "python_script": "print('ok')",
                    "entrypoint": "main",
                    "dependencies": ["dep-a", "dep-a", "dep-b"],
                    "governed_host_brokers": ["fs.read_mount"],
                    "governed_authorities": ["read"],
                    "host_abi_version": "bssc.host.v1",
                    "virtual_mounts": {"workspace": {}, "cache": {}},
                },
            }
        )

        self.assertEqual(
            {
                "artifact_id": "artifact-golden",
                "title": (
                    "Python Commands 02 — Read Text File / "
                    "Python Commands 02 Read Text File"
                ),
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "declaration": {
                    "intent": "Read text file",
                    "inputs": {"path": "String"},
                    "outputs": {"text": "String"},
                },
                "lifecycle": {},
                "runtime_package_reference": {
                    "representation": "python_script",
                    "executor_framework": "python3",
                    "entrypoint": "main",
                    "body_field": "python_script",
                    "body_sha256": (
                        "e651ef002de96727cf3b1f8533ebb5c1036d12d795ec486c4cbd4ed2872fde31"
                    ),
                    "dependencies": ["dep-a", "dep-b"],
                },
                "normalization": {
                    "normalization_version": "bssc.skill.normalization.v1",
                    "path_notation_version": "bssc.skill.path.v1",
                    "regions": {
                        "d": {
                            "boundary_term": "d*",
                            "carrier_kind": "value",
                            "reconstructible": True,
                            "leaves": [
                                {
                                    "region": "d*",
                                    "path": "/d/text",
                                    "carrier_kind": "value",
                                    "data_type": "String",
                                    "semantic_label": "text",
                                    "value": "example",
                                    "leaf_class": "scalar",
                                }
                            ],
                        }
                    },
                },
                "aliases": [
                    "Read Text File",
                    "Python Commands 02 Read Text File",
                ],
                "family": {
                    "label": "Python Commands",
                    "key": "python commands",
                    "ordinal": "02",
                    "variant": "Read Text File",
                },
                "compatibility": {
                    "adapters": [
                        {
                            "format": "openai_tool",
                            "direction": "import",
                            "name": "read_text",
                        }
                    ]
                },
                "hosting_metadata": {
                    "representation": "python_script",
                    "executor_framework": "python3",
                    "entrypoint": "main",
                    "body_field": "python_script",
                    "body_sha256": (
                        "e651ef002de96727cf3b1f8533ebb5c1036d12d795ec486c4cbd4ed2872fde31"
                    ),
                    "dependencies": ["dep-a", "dep-b"],
                    "governed_host_brokers": ["fs.read_mount"],
                    "governed_authorities": ["read"],
                    "host_abi_version": "bssc.host.v1",
                    "virtual_mounts": ["cache", "workspace"],
                },
            },
            canonical_skill_ir_dict_from_artifact(artifact),
        )

    def test_normalized_skill_aliases_includes_title_variants(self) -> None:
        aliases = normalized_skill_aliases(
            ["Read Text File"],
            title="Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
        )
        self.assertEqual(
            aliases,
            ["Read Text File", "Python Commands 02 Read Text File"],
        )

    def test_normalized_skill_family_metadata_derives_numbered_command_family(self) -> None:
        family = normalized_skill_family_metadata(
            {},
            title="Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
        )
        self.assertEqual(
            family,
            {
                "label": "Python Commands",
                "key": "python commands",
                "ordinal": "02",
                "variant": "Read Text File",
            },
        )

    def test_canonical_skill_ir_projects_aliases_family_and_hosting(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
                "aliases": ["Read Text File"],
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
                "governance": {
                    "governed_host_brokers": ["fs.read_mount"],
                    "host_abi_version": "bssc.host.v1",
                },
            }
        )

        projected = canonical_skill_ir_from_artifact(artifact)

        self.assertEqual(projected.schema, "bssc_skill.v1")
        self.assertEqual(projected.kind, "ability")
        self.assertEqual(projected.aliases, ["Read Text File", "Python Commands 02 Read Text File"])
        self.assertEqual(
            projected.family,
            {
                "label": "Python Commands",
                "key": "python commands",
                "ordinal": "02",
                "variant": "Read Text File",
            },
        )
        self.assertEqual(projected.hosting_metadata.get("executor_framework"), "python3")
        self.assertEqual(projected.hosting_metadata.get("representation"), "python_script")
        self.assertIn("fs.read_mount", projected.hosting_metadata.get("governed_host_brokers", []))

    def test_canonical_skill_ir_projects_compatibility_metadata(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Repo Search",
                "inputs": {"symbol": "required symbol to find"},
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

        projected = canonical_skill_ir_from_artifact(artifact)

        self.assertEqual(
            projected.compatibility,
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

    def test_skill_export_document_emits_aliases_and_family(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Symbol Search Commands 03 — Find Python Class Definition / Symbol Search Commands 03 Find Python Class Definition",
                "aliases": ["Find Python Class Definition"],
                "executor": "bash",
                "inputs": {"root": "required input value", "symbol": "required input value"},
                "outputs": {"result": "execution result"},
                "shell": "printf '%s\\n' \"$symbol\"",
            }
        )

        exported = skill_export_document(artifact)

        self.assertEqual(
            exported.get("aliases"),
            [
                "Find Python Class Definition",
                "Symbol Search Commands 03 Find Python Class Definition",
            ],
        )
        self.assertEqual(
            exported.get("family"),
            {
                "label": "Symbol Search Commands",
                "key": "symbol search commands",
                "ordinal": "03",
                "variant": "Find Python Class Definition",
            },
        )
