from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import unittest

from realized_core_governance.trace import (
    EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
    canonical_effect_trace_receipt_payload,
    canonical_trace_answer,
    effect_trace_receipt,
    effect_trace_signature,
)


class _Status(Enum):
    READY = "ready"


@dataclass
class _Evidence:
    status: _Status
    payload: bytes


class _Unserializable:
    def __str__(self) -> str:
        return "unserializable"


class EffectTraceReceiptTests(unittest.TestCase):
    def test_receipt_uses_stable_schema_kind_and_sha256_digest(self) -> None:
        payload = {"effect_kind": "execute.python3", "allowed": True}
        canonical_json = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        receipt = effect_trace_receipt("  request  ", payload)

        self.assertEqual(
            {
                "schema": "bssc_effect_receipt.v1",
                "kind": "request",
                "digest": hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
            },
            receipt,
        )
        self.assertEqual(
            "bssc_effect_receipt.v1",
            EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
        )

    def test_canonicalization_omits_volatile_fields_at_every_depth(self) -> None:
        payload = {
            "id": "outer-id",
            "kept": {
                "issued_at": "now",
                "created_at": "then",
                "evaluated_at": "later",
                "updated_at": "eventually",
                "value": 7,
            },
        }

        self.assertEqual(
            {"kept": {"value": 7}},
            canonical_effect_trace_receipt_payload(payload),
        )

    def test_status_normalization_preserves_historical_admission_equivalence(self) -> None:
        for value in ("admitted", " ADMITTED ", "legacy_implicit_admit"):
            with self.subTest(value=value):
                self.assertEqual(
                    {"status": "admitted"},
                    canonical_effect_trace_receipt_payload({"status": value}),
                )
        self.assertEqual(
            {"status": "held"},
            canonical_effect_trace_receipt_payload({"status": " HELD "}),
        )

    def test_nested_lists_tuples_and_json_safe_values_keep_historical_shape(self) -> None:
        payload = {
            "items": [
                ("alpha", {"status": "admitted", "id": "discard"}),
                _Evidence(status=_Status.READY, payload=b"hello"),
                {"red", "blue"},
            ]
        }

        canonical = canonical_effect_trace_receipt_payload(payload)

        self.assertEqual(
            ["alpha", {"status": "admitted"}],
            canonical["items"][0],
        )
        self.assertEqual(
            {"status": "ready", "payload": "hello"},
            canonical["items"][1],
        )
        self.assertCountEqual(["red", "blue"], canonical["items"][2])

    def test_mapping_keys_are_trimmed_and_sorted_before_projection(self) -> None:
        self.assertEqual(
            {"alpha": 1, "beta": 2},
            canonical_effect_trace_receipt_payload(
                {" beta ": 2, "alpha": 1}
            ),
        )

    def test_mixed_incomparable_mapping_keys_keep_historical_type_error(self) -> None:
        with self.assertRaises(TypeError):
            canonical_effect_trace_receipt_payload({"alpha": 1, 2: "beta"})

    def test_non_json_serializable_value_keeps_historical_type_error(self) -> None:
        with self.assertRaises(TypeError):
            effect_trace_receipt("result", object())

    def test_canonicalization_does_not_mutate_supplied_evidence(self) -> None:
        payload = {
            "status": "legacy_implicit_admit",
            "nested": {"id": "keep-in-input", "value": [1, 2]},
        }

        canonical_effect_trace_receipt_payload(payload)

        self.assertEqual(
            {
                "status": "legacy_implicit_admit",
                "nested": {"id": "keep-in-input", "value": [1, 2]},
            },
            payload,
        )


class ConstitutionalEffectTraceTests(unittest.TestCase):
    def test_trace_answer_preserves_historical_projection_and_fallbacks(self) -> None:
        self.assertEqual("hello", canonical_trace_answer("  hello  "))
        for value in (None, "", [], {}):
            with self.subTest(value=value):
                self.assertEqual("", canonical_trace_answer(value))
        self.assertEqual(
            '{"alpha":1,"beta":2}',
            canonical_trace_answer({"beta": 2, "alpha": 1}),
        )
        self.assertEqual("unserializable", canonical_trace_answer(_Unserializable()))

    def test_empty_trace_has_complete_default_requirement_signature(self) -> None:
        self.assertEqual(
            {
                "artifact_title": "",
                "effect_kind": "",
                "required_authority": "",
                "allowed": False,
                "executor_framework": "",
                "admission_status": "",
                "activation_status": "",
                "trust_status": "",
                "ok": False,
                "exit_code": 0,
                "answer": "",
                "receipt_digests": {
                    "request": '{"effect_kind":"","executor_framework":"","invocation_payload":""}',
                    "declaration": "{}",
                    "policy": '{"policy_titles":[],"required_approval_class":"automatic"}',
                    "approval": '{"approval_titles":[],"required_approval_class":"automatic"}',
                    "lifecycle": '{"activation_status":"","admission_status":"","installation_status":"","quarantine_status":"","review_status":"","trust_status":""}',
                    "grants": "[]",
                },
            },
            effect_trace_signature(None),
        )

    def test_signature_projects_every_effect_requirement_and_semantic_digest(self) -> None:
        trace = {
            "id": "volatile-trace-id",
            "artifact_title": "Example Ability",
            "request": {
                "effect_kind": "execute.python3",
                "executor_framework": "python3",
                "invocation_payload": {"created_at": "volatile", "count": 2},
            },
            "decision": {"allowed": True, "required_authority": "execute"},
            "declaration": {
                "authorities_requested": ["execute"],
                "status": "legacy_implicit_admit",
            },
            "admission": {
                "status": "legacy_implicit_admit",
                "policy_titles": [
                    "Policy A",
                    "Replay Policy Snapshot / transient",
                    "Policy A",
                    "",
                ],
                "approval_titles": [" Approval A ", "Approval A", ""],
                "required_approval_class": "operator_approved",
            },
            "lifecycle": {
                "activation_status": "inactive",
                "installation_status": "installed",
                "quarantine_status": "clear",
                "review_status": "approved",
                "trust_status": "revoked",
            },
            "grants": [
                {
                    "id": "volatile-grant-id",
                    "authority": "execute",
                    "scope": "artifact",
                    "target": "example",
                    "context": "request",
                    "duration": "invocation",
                    "triggering_conditions": ["selected"],
                    "approval_class": "operator_approved",
                    "risk_tier": "tier_2",
                    "executor_framework": "python3",
                    "effect_kind": "execute.python3",
                    "semantic_unit": "Run example.",
                    "data_classes_touched": ["internal"],
                    "side_effects": ["process"],
                    "policy_titles": [
                        "Policy A",
                        "Replay Policy Snapshot / transient",
                    ],
                    "admission_status": "legacy_implicit_admit",
                },
                "ignored-non-mapping",
            ],
            "result": {
                "ok": True,
                "exit_code": "7",
                "answer": {"beta": 2, "alpha": 1},
            },
        }

        signature = effect_trace_signature(trace)

        self.assertEqual(
            {
                "artifact_title": "Example Ability",
                "effect_kind": "execute.python3",
                "required_authority": "execute",
                "allowed": True,
                "executor_framework": "python3",
                "admission_status": "admitted",
                "activation_status": "active",
                "trust_status": "trusted",
                "ok": True,
                "exit_code": 7,
                "answer": '{"alpha":1,"beta":2}',
            },
            {key: value for key, value in signature.items() if key != "receipt_digests"},
        )
        self.assertEqual(
            {
                "request": '{"effect_kind":"execute.python3","executor_framework":"python3","invocation_payload":{"count":2}}',
                "declaration": '{"authorities_requested":["execute"],"status":"admitted"}',
                "policy": '{"policy_titles":["Policy A"],"required_approval_class":"operator_approved"}',
                "approval": '{"approval_titles":["Approval A","Approval A"],"required_approval_class":"operator_approved"}',
                "lifecycle": '{"activation_status":"active","admission_status":"admitted","installation_status":"installed","quarantine_status":"clear","review_status":"approved","trust_status":"trusted"}',
                "grants": '[{"admission_status":"admitted","approval_class":"operator_approved","authority":"execute","context":"request","data_classes_touched":["internal"],"duration":"invocation","effect_kind":"execute.python3","executor_framework":"python3","policy_titles":["Policy A"],"risk_tier":"tier_2","scope":"artifact","semantic_unit":"Run example.","side_effects":["process"],"target":"example","triggering_conditions":["selected"]}]',
            },
            signature["receipt_digests"],
        )

    def test_non_mapping_sections_keep_historical_empty_fallbacks(self) -> None:
        signature = effect_trace_signature(
            {
                "effect_kind": "fallback.effect",
                "request": "malformed",
                "decision": [],
                "admission": 1,
                "lifecycle": None,
                "result": "malformed",
                "grants": "not-a-list",
            }
        )

        self.assertEqual("fallback.effect", signature["effect_kind"])
        self.assertFalse(signature["allowed"])
        self.assertEqual("", signature["admission_status"])
        self.assertEqual("[]", signature["receipt_digests"]["grants"])

    def test_deterministic_failures_keep_historical_types_and_messages(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"invalid literal for int\(\) with base 10: 'invalid'",
        ):
            effect_trace_signature({"result": {"exit_code": "invalid"}})
        with self.assertRaisesRegex(
            TypeError,
            r"'NoneType' object is not iterable",
        ):
            effect_trace_signature({"grants": None})
        with self.assertRaisesRegex(
            TypeError,
            r"'<' not supported between instances of 'int' and 'str'",
        ):
            effect_trace_signature({"declaration": {"alpha": 1, 2: "beta"}})

    def test_signature_does_not_mutate_supplied_trace(self) -> None:
        trace = {
            "request": {"invocation_payload": {"created_at": "keep", "value": 1}},
            "admission": {"status": "legacy_implicit_admit"},
            "grants": [{"id": "keep", "authority": "read"}],
        }
        original = deepcopy(trace)

        effect_trace_signature(trace)

        self.assertEqual(original, trace)


if __name__ == "__main__":
    unittest.main()
