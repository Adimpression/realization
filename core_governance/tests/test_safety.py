from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import unittest
from unittest.mock import patch

from realized_core_governance import safety


@dataclass
class _ArtifactView:
    title: str
    content: Any


def _revocation(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "intent": "Revoke governed execution.",
        "subject_titles": ["Governed Skill"],
        "subject_kinds": [],
        "trust_status": "revoked",
        "quarantine_status": "clear",
        "activation_status": "inactive",
        "installation_status": "blocked",
        "status": "active",
        "issued_by": "operator://reviewer",
        "rationale": "Revoked.",
        "valid_from": "",
        "valid_until": "",
    }
    value.update(overrides)
    return value


def _incident(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "intent": "Constrain governed execution.",
        "subject_titles": ["Governed Skill"],
        "subject_kinds": [],
        "severity": "high",
        "enforcement_action": "restrict",
        "status": "open",
        "issued_by": "operator://reviewer",
        "rationale": "Restricted.",
        "valid_from": "",
        "valid_until": "",
    }
    value.update(overrides)
    return value


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz: Any = None) -> datetime:
        moment = cls(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        return moment if tz is not None else moment.replace(tzinfo=None)


class GovernanceSafetyTests(unittest.TestCase):
    def test_vocabularies_and_normalization_are_exact(self) -> None:
        self.assertEqual(("active", "rescinded"), safety.REVOCATION_RECORD_STATUSES)
        self.assertEqual(
            ("open", "monitoring", "resolved"),
            safety.INCIDENT_RECORD_STATUSES,
        )
        self.assertEqual(
            ("low", "medium", "high", "critical"),
            safety.INCIDENT_SEVERITIES,
        )
        self.assertEqual(
            ("none", "restrict", "suspend", "quarantine"),
            safety.INCIDENT_ENFORCEMENT_ACTIONS,
        )
        cases = (
            (safety.normalize_revocation_record_status, " RESCINDED\n", {}, "rescinded"),
            (safety.normalize_incident_record_status, "\x00MONITORING\x7f", {}, "monitoring"),
            (safety.normalize_incident_severity, " CRITICAL ", {}, "critical"),
            (safety.normalize_incident_enforcement_action, " SUSPEND ", {}, "suspend"),
            (safety.normalize_incident_severity, 0, {}, "medium"),
            (safety.normalize_incident_severity, "unknown", {"default": "custom"}, "custom"),
        )
        for normalizer, value, kwargs, expected in cases:
            with self.subTest(normalizer=normalizer.__name__, value=value):
                self.assertEqual(expected, normalizer(value, **kwargs))

    def test_revocation_payload_normalization_preserves_fields(self) -> None:
        result = safety.skill_revocation_from_payload(
            {
                "schema": " bssc_skill.v2 ",
                "kind": " REVOCATION ",
                "revocation": {
                    "intent": " Revoke\nexecution. ",
                    "subject_titles": " Governed\x00Skill ",
                    "subject_kinds": ["ABILITY", "unknown"],
                    "trust_status": " SUSPENDED ",
                    "quarantine_status": " QUARANTINED ",
                    "activation_status": " ACTIVE ",
                    "installation_status": " INSTALLED ",
                    "status": " RESCINDED ",
                    "issued_by": " operator://reviewer ",
                    "rationale": " Reviewed\ncarefully. ",
                    "valid_from": " 2026-01-01T00:00:00Z ",
                    "valid_until": " 2027-01-01T00:00:00Z ",
                },
            }
        )
        self.assertEqual(
            {
                "intent": "Revoke execution.",
                "subject_titles": ["Governed Skill"],
                "subject_kinds": ["ability", "knowledge"],
                "trust_status": "suspended",
                "quarantine_status": "quarantined",
                "activation_status": "active",
                "installation_status": "installed",
                "status": "rescinded",
                "issued_by": "operator://reviewer",
                "rationale": "Reviewed carefully.",
                "valid_from": "2026-01-01T00:00:00Z",
                "valid_until": "2027-01-01T00:00:00Z",
            },
            result,
        )

    def test_incident_payload_normalization_preserves_fields(self) -> None:
        result = safety.skill_incident_from_payload(
            {
                "schema": "bssc_skill.v2",
                "kind": "incident",
                "incident": {
                    "intent": " Constrain execution. ",
                    "subject_titles": [" First ", "Second"],
                    "subject_kinds": " ABILITY ",
                    "severity": " CRITICAL ",
                    "enforcement_action": " QUARANTINE ",
                    "status": " MONITORING ",
                    "issued_by": " operator://reviewer ",
                    "rationale": " Active incident. ",
                    "valid_from": " start ",
                    "valid_until": " end ",
                },
            }
        )
        self.assertEqual(
            {
                "intent": "Constrain execution.",
                "subject_titles": ["First", "Second"],
                "subject_kinds": ["ability"],
                "severity": "critical",
                "enforcement_action": "quarantine",
                "status": "monitoring",
                "issued_by": "operator://reviewer",
                "rationale": "Active incident.",
                "valid_from": "start",
                "valid_until": "end",
            },
            result,
        )

    def test_payload_filtering_and_missing_field_errors_are_exact(self) -> None:
        self.assertEqual(
            {},
            safety.skill_revocation_from_payload(
                {"schema": "bssc_skill.v1", "kind": "revocation"}
            ),
        )
        self.assertEqual(
            {},
            safety.skill_incident_from_payload(
                {"schema": "bssc_skill.v2", "kind": "ability"}
            ),
        )
        with self.assertRaisesRegex(
            ValueError,
            "Revocation artifact v2 requires non-empty fields: "
            "intent, subject_titles, issued_by, rationale",
        ):
            safety.skill_revocation_from_payload(
                {
                    "schema": "bssc_skill.v2",
                    "kind": "revocation",
                    "revocation": False,
                }
            )
        with self.assertRaisesRegex(
            ValueError,
            "Incident artifact v2 requires non-empty fields: "
            "intent, subject_titles, issued_by, rationale",
        ):
            safety.skill_incident_from_payload(
                {
                    "schema": "bssc_skill.v2",
                    "kind": "incident",
                    "incident": False,
                }
            )

    def test_summaries_preserve_order_and_defaults(self) -> None:
        self.assertEqual(
            "Revocation record rescinded for First, Second with trust status suspended.",
            safety.revocation_answer_summary(
                {
                    "subject_titles": ["First", "Second"],
                    "status": "rescinded",
                    "trust_status": "suspended",
                }
            ),
        )
        self.assertEqual(
            "Incident record open for unspecified skill at severity medium with action none.",
            safety.incident_answer_summary({}),
        )

    def test_artifact_projection_uses_only_read_only_content(self) -> None:
        revocation = _revocation()
        incident = _incident()
        revocation_artifact = _ArtifactView(
            "Revocation",
            {"skill_revocation": revocation},
        )
        incident_artifact = _ArtifactView(
            "Incident",
            {"skill_incident": incident},
        )
        self.assertEqual(
            revocation,
            safety.artifact_skill_revocation(revocation_artifact),
        )
        self.assertEqual(incident, safety.artifact_skill_incident(incident_artifact))
        self.assertTrue(safety.artifact_is_revocation_record(revocation_artifact))
        self.assertTrue(safety.artifact_is_incident_record(incident_artifact))
        self.assertEqual(
            {},
            safety.artifact_skill_revocation(_ArtifactView("Invalid", "invalid")),
        )

    def test_temporal_bounds_are_inclusive_and_malformed_bounds_are_open(self) -> None:
        exact = "2026-04-01T12:00:00Z"
        with patch.object(safety, "datetime", _FixedDateTime):
            self.assertTrue(
                safety.revocation_matches_skill(
                    _revocation(valid_from=exact, valid_until=exact),
                    skill_title="Governed Skill",
                    kind="ability",
                )
            )
            self.assertTrue(
                safety.incident_matches_skill(
                    _incident(
                        valid_from="not-a-date",
                        valid_until="also-not-a-date",
                    ),
                    skill_title="Governed Skill",
                    kind="ability",
                )
            )

    def test_matching_denies_each_restriction_branch(self) -> None:
        revocations = (
            _revocation(status="rescinded"),
            _revocation(valid_from="2999-01-01T00:00:00Z"),
            _revocation(valid_until="2000-01-01T00:00:00Z"),
            _revocation(subject_titles=["Other Skill"]),
            _revocation(subject_kinds=["knowledge"]),
        )
        incidents = (
            _incident(status="resolved"),
            _incident(valid_from="2999-01-01T00:00:00Z"),
            _incident(valid_until="2000-01-01T00:00:00Z"),
            _incident(subject_titles=["Other Skill"]),
            _incident(subject_kinds=["knowledge"]),
        )
        for record in revocations:
            with self.subTest(record=record):
                self.assertFalse(
                    safety.revocation_matches_skill(
                        record,
                        skill_title="Governed Skill",
                        kind="ability",
                    )
                )
        for record in incidents:
            with self.subTest(record=record):
                self.assertFalse(
                    safety.incident_matches_skill(
                        record,
                        skill_title="Governed Skill",
                        kind="ability",
                    )
                )

    def test_matching_artifacts_preserves_input_order_and_identity(self) -> None:
        first = _ArtifactView("First", {"skill_revocation": _revocation()})
        ignored = _ArtifactView("Ignored", {})
        denied = _ArtifactView(
            "Denied",
            {"skill_revocation": _revocation(subject_titles=["Other Skill"])},
        )
        second = _ArtifactView("Second", {"skill_revocation": _revocation()})
        result = safety.matching_revocation_artifacts(
            [first, ignored, denied, second],
            skill_title="Governed Skill",
            kind="ability",
        )
        self.assertEqual([first, second], result)
        self.assertIs(first, result[0])
        self.assertEqual(
            [],
            safety.matching_incident_artifacts(
                None,
                skill_title="Governed Skill",
                kind="ability",
            ),
        )

    def test_revocation_dominates_incidents_and_last_revocation_supplies_state(self) -> None:
        first = _ArtifactView(
            "First revocation",
            {"skill_revocation": _revocation(rationale="First reason.")},
        )
        second = _ArtifactView(
            "Second revocation",
            {
                "skill_revocation": _revocation(
                    trust_status="restricted",
                    quarantine_status="quarantined",
                    activation_status="active",
                    installation_status="installed",
                    rationale="Second reason.",
                )
            },
        )
        incident = _ArtifactView(
            "Critical incident",
            {
                "skill_incident": _incident(
                    enforcement_action="quarantine",
                    rationale="Incident reason.",
                )
            },
        )
        self.assertEqual(
            {
                "trust_status": "restricted",
                "quarantine_status": "quarantined",
                "activation_status": "active",
                "installation_status": "installed",
                "status_reason": "Second reason.",
                "revocation_titles": ["First revocation", "Second revocation"],
                "incident_titles": ["Critical incident"],
            },
            safety.governed_safety_lifecycle_overlay(
                skill_title="Governed Skill",
                kind="ability",
                revocation_artifacts=[first, second],
                incident_artifacts=[incident],
            ),
        )

    def test_incident_precedence_and_equal_strength_ties_are_stable(self) -> None:
        first_suspend = _ArtifactView(
            "First suspend",
            {
                "skill_incident": _incident(
                    enforcement_action="suspend",
                    rationale="First suspend reason.",
                )
            },
        )
        second_suspend = _ArtifactView(
            "Second suspend",
            {
                "skill_incident": _incident(
                    enforcement_action="suspend",
                    rationale="Second suspend reason.",
                )
            },
        )
        tied = safety.governed_safety_lifecycle_overlay(
            skill_title="Governed Skill",
            kind="ability",
            incident_artifacts=[first_suspend, second_suspend],
        )
        self.assertEqual("First suspend reason.", tied["status_reason"])
        self.assertEqual("suspended", tied["trust_status"])
        self.assertEqual("inactive", tied["activation_status"])
        self.assertEqual(
            ["First suspend", "Second suspend"],
            tied["incident_titles"],
        )

        quarantine = _ArtifactView(
            "Quarantine",
            {
                "skill_incident": _incident(
                    enforcement_action="quarantine",
                    rationale="Quarantine reason.",
                )
            },
        )
        strongest = safety.governed_safety_lifecycle_overlay(
            skill_title="Governed Skill",
            kind="ability",
            incident_artifacts=[first_suspend, quarantine, second_suspend],
        )
        self.assertEqual("Quarantine reason.", strongest["status_reason"])
        self.assertEqual("quarantined", strongest["quarantine_status"])
        self.assertEqual("inactive", strongest["activation_status"])

    def test_empty_overlay_shape_is_exact(self) -> None:
        self.assertEqual(
            {"revocation_titles": [], "incident_titles": []},
            safety.governed_safety_lifecycle_overlay(
                skill_title="Governed Skill",
                kind="ability",
            ),
        )


if __name__ == "__main__":
    unittest.main()
