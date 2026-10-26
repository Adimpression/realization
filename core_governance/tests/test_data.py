from __future__ import annotations

import unittest

from realized_core_governance import data


class GovernanceDataTests(unittest.TestCase):
    def test_vocabulary_and_single_value_normalization_are_exact(self) -> None:
        self.assertEqual(
            (
                "public",
                "internal",
                "sensitive",
                "regulated",
                "secret",
                "audit_only",
                "derived",
            ),
            data.DATA_CLASS_CHOICES,
        )
        cases = (
            (" AUDIT-ONLY\n", "public", "audit_only"),
            ("\x00Sensitive\x7f", "public", "sensitive"),
            (None, "internal", "internal"),
            (0, "internal", "internal"),
            ("unknown", "custom", "custom"),
        )
        for value, default, expected in cases:
            with self.subTest(value=value, default=default):
                self.assertEqual(
                    expected,
                    data.normalize_data_class(value, default=default),
                )

    def test_list_normalization_preserves_historical_collection_rules(self) -> None:
        self.assertEqual([], data.normalize_data_class_list(None))
        self.assertEqual([], data.normalize_data_class_list({}))
        self.assertEqual(
            ["public", "secret", "audit_only"],
            data.normalize_data_class_list(
                ["public", " SECRET ", "public", "audit-only", ""]
            ),
        )
        self.assertEqual(["internal"], data.normalize_data_class_list("internal"))
        self.assertEqual(
            ["public"],
            data.normalize_data_class_list(("secret", "internal")),
        )

    def test_allowed_classes_put_grants_before_declaration_stably(self) -> None:
        context = {
            "grants": [
                {"data_classes_touched": ["derived", "public"]},
                "ignored",
                {"data_classes_touched": ["secret", "derived"]},
            ],
            "declaration": {
                "data_classes_touched": ["internal", "public", "regulated"]
            },
        }
        self.assertEqual(
            ["derived", "public", "secret", "internal", "regulated"],
            data.allowed_data_classes_from_governance_context(context),
        )
        self.assertEqual(
            [], data.allowed_data_classes_from_governance_context("invalid")
        )
        self.assertEqual(
            ["internal"],
            data.allowed_data_classes_from_governance_context(
                {"grants": {}, "declaration": {"data_classes_touched": "internal"}}
            ),
        )

    def test_access_evaluation_covers_allow_and_exact_denials(self) -> None:
        context = {
            "grants": [{"data_classes_touched": ["public", "internal"]}],
            "declaration": {"data_classes_touched": ["derived"]},
        }
        self.assertEqual(
            (True, ""),
            data.ensure_governed_data_access(
                None,
                requested_data_classes=[],
                operation=" fs.read_mount ",
            ),
        )
        self.assertEqual(
            (True, ""),
            data.ensure_governed_data_access(
                context,
                requested_data_classes=["derived", "public"],
                operation="fs.read_mount",
            ),
        )
        self.assertEqual(
            (
                False,
                "Governed data access for fs.read mount requires declared data "
                "classes secret, regulated, but runtime grants declare none.",
            ),
            data.ensure_governed_data_access(
                None,
                requested_data_classes=["secret", "regulated"],
                operation=" fs.read\x00mount ",
            ),
        )
        self.assertEqual(
            (
                False,
                "Governed data access for fs.read_mount requires data classes "
                "secret, regulated, but runtime grants allow public, internal, "
                "derived.",
            ),
            data.ensure_governed_data_access(
                context,
                requested_data_classes=["public", "secret", "regulated"],
                operation="fs.read_mount",
            ),
        )

    def test_named_query_registry_preserves_shape_and_defaults(self) -> None:
        self.assertEqual({}, data.normalize_named_query_registry(None))
        self.assertEqual(
            {
                "artifact count": {
                    "sql": "SELECT COUNT(*) AS count FROM artifacts",
                    "parameter_order": ["subject", "subject"],
                    "data_class": "internal",
                },
                "public query": {
                    "sql": "SELECT 1",
                    "parameter_order": [],
                    "data_class": "public",
                },
            },
            data.normalize_named_query_registry(
                {
                    " artifact\ncount ": {
                        "sql": " SELECT COUNT(*) AS count\nFROM artifacts ",
                        "parameter_order": [" subject ", "", "subject"],
                        "data_class": "unknown",
                    },
                    "public query": {
                        "sql": "SELECT 1",
                        "parameter_order": ("ignored",),
                        "data_class": "public",
                    },
                    "": {"sql": "SELECT 2"},
                    "missing sql": {},
                    "invalid": "SELECT 3",
                }
            ),
        )

    def test_read_only_query_predicate_preserves_all_lexical_branches(self) -> None:
        cases = (
            (" SELECT\n1 ", True),
            ("WITH values_cte AS (SELECT 1) SELECT * FROM values_cte", True),
            ("SELECT 1; UPDATE records SET value = 2", False),
            ("WITH values_cte AS (DELETE FROM records) SELECT 1", True),
            ("WITH values_cte AS ( SELECT 1 ) DELETE FROM values_cte", False),
            ("PRAGMA table_info(records)", False),
            ("select", False),
            ("", False),
        )
        for sql, expected in cases:
            with self.subTest(sql=sql):
                self.assertIs(expected, data.query_is_read_only(sql))


if __name__ == "__main__":
    unittest.main()
