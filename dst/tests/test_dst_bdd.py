from __future__ import annotations

import unittest

from dst.tests.dst_bdd_support import DstEmbeddedStory


class DstBehaviorBDDTests(unittest.TestCase):
    def test_bdd_fare_modernization_preserves_staged_and_direct_routes_end_to_end(self) -> None:
        markdown = """# Fare Modernization

## Situation
A transit authority wants to modernize fare payment without breaking service.

## Actors
- `a1`: transit authority
- `a2`: payment processor
- `a3`: regulator

## Objectives
- `o1`: reduce boarding time
- `o2`: preserve continuity

## Capabilities
- `k1`: improved closed-loop card system
- `k2`: open-loop payment acceptance

## Dependencies
- `d1`: certification approval
- `d2`: payment network readiness

## Constraints
- `q1`: no downtime

## Boundaries
- `b1`: transit-payment boundary

## States
- `s0`: legacy fare system
- `s1`: improved closed-loop card system
- `s2`: hybrid payment environment
- `s3`: full open-loop payment

## Transitions
- `t1`: legacy to improved closed-loop
- `t2`: improved closed-loop to hybrid
- `t3`: hybrid to full open-loop

## Candidate Paths
### Path A: staged modernization route
A staged route reduces disruption by improving the existing card system first and then expanding.
- `s0 -> s1 -> s2 -> s3`
- preserves continuity while capabilities and approvals mature

### Path B: direct open-loop route
A direct route aims for the target immediately but depends on readiness across the payment boundary.
- `s0 -> s3`
- faster but riskier if certification and network readiness are incomplete
"""
        story = DstEmbeddedStory(
            self,
            name="embedded_fare_modernization",
            markdown=markdown,
        )

        story.given_embedded_dst_prose()
        story.when_governed_candidate_path_discovery_runs()
        story.when_the_end_to_end_dst_pipeline_runs(subject_id="fare-modernization")

        story.then_candidate_paths_are(
            (
                "Path A: staged modernization route",
                "Path B: direct open-loop route",
            )
        )
        story.then_candidate_path_routes_are(
            (
                "s0 -> s1 -> s2 -> s3",
                "s0 -> s3",
            )
        )
        story.then_path_kinds_are(("multi_step", "single_step"))
        story.then_the_current_state_is("legacy fare system")
        story.then_the_target_states_are(("full open-loop payment",))
        story.then_the_normalized_candidate_surface_has(transition_count=2, decision_count=2)
        story.then_valid_decision_titles_include_set(
            (
                "Path A: staged modernization route",
                "Path B: direct open-loop route",
            )
        )
        story.then_executable_decision_titles_include_set(
            (
                "Path A: staged modernization route",
                "Path B: direct open-loop route",
            )
        )

    def test_bdd_medication_cutover_keeps_one_safe_direct_decision_when_only_one_route_exists(self) -> None:
        markdown = """# Medication Cutover

## Situation
A hospital wants to retire paper prescribing once readiness work is complete.

## Actors
- `a1`: clinical leadership
- `a2`: medication safety office

## Objectives
- `o1`: reduce transcription errors

## Capabilities
- `k1`: validated electronic prescribing

## Dependencies
- `d1`: training complete
- `d2`: integration validated

## Constraints
- `q1`: no mixed-mode prescribing

## Boundaries
- `b1`: clinical safety boundary

## States
- `s0`: paper-only operation with cutover readiness complete
- `s2`: fully electronic and validated medication workflow

## Transitions
- `t1`: prepared direct cutover to validated electronic prescribing

## Candidate Paths
### Outcome
A safe cutover is available only when readiness is complete before go-live.
- `s0 -> s2`
- direct cutover after validation and training
"""
        story = DstEmbeddedStory(
            self,
            name="embedded_medication_cutover",
            markdown=markdown,
        )

        story.given_embedded_dst_prose()
        story.when_governed_candidate_path_discovery_runs()
        story.when_the_end_to_end_dst_pipeline_runs(subject_id="medication-cutover")

        story.then_candidate_paths_are(("Outcome",))
        story.then_candidate_path_routes_are(("s0 -> s2",))
        story.then_path_kinds_are(("single_step",))
        story.then_the_current_state_is("paper-only operation with cutover readiness complete")
        story.then_the_target_states_are(("fully electronic and validated medication workflow",))
        story.then_the_normalized_candidate_surface_has(transition_count=1, decision_count=1)
        story.then_admissible_transition_names_are(("s0 -> s2",))
        story.then_valid_decision_titles_are(("Outcome",))
        story.then_executable_decision_titles_are(("Outcome",))

    def test_bdd_configuration_only_prose_surfaces_configuration_candidates_during_discovery(self) -> None:
        markdown = """# Regional Alerting

## Situation
A region wants to improve alerting without excluding vulnerable residents.

## Actors
- `a1`: regional operations center
- `a2`: telecom partners

## Objectives
- `o1`: speed
- `o2`: resilience
- `o3`: inclusion

## Capabilities
- `k1`: sms alerting
- `k2`: radio fallback
- `k3`: accessible templates

## Dependencies
- `d1`: telecom availability

## Constraints
- `q1`: no single channel dependence

## Boundaries
- `b1`: regional-local coordination

## Candidate Paths
### Example A: speed-first configuration
Fastest path with minimal redundancy.
- prioritize sms dispatch and central control

### Example B: resilience-first configuration
Layered fallback path with additional redundancy.
- combine sms, radio, and escalation drills

### Example C: inclusion-first configuration
Accessibility-first path across vulnerable groups.
- prioritize accessible templates and local outreach
"""
        story = DstEmbeddedStory(
            self,
            name="embedded_regional_alerting_configuration",
            markdown=markdown,
        )

        story.given_embedded_dst_prose()
        story.when_governed_candidate_path_discovery_runs()

        story.then_candidate_paths_are(
            (
                "Example A: speed-first configuration",
                "Example B: resilience-first configuration",
                "Example C: inclusion-first configuration",
            )
        )
        story.then_path_kinds_are(("configuration", "configuration", "configuration"))
        story.then_sort_atom_context_includes(
            actors=("regional operations center", "telecom partners"),
            capabilities=("sms alerting", "radio fallback", "accessible templates"),
        )

    def test_bdd_complex_rollout_keeps_multiple_paths_visible_in_the_decision_surface(self) -> None:
        markdown = """# Exam Rollout

## Situation
A national school system wants to digitize exams without losing resilience or operational trust.

## Actors
- `a1`: education ministry
- `a2`: regional authorities
- `a3`: audit office

## Objectives
- `o1`: modernize exam delivery
- `o2`: preserve reliability

## Capabilities
- `k1`: readiness package
- `k2`: audited digital rollout
- `k3`: direct leap rollout

## Dependencies
- `d1`: regional readiness evidence
- `d2`: audit signoff

## Constraints
- `q1`: no nationwide failure

## Boundaries
- `b1`: national-regional delivery boundary

## States
- `s0`: paper-based baseline with readiness package complete
- `s1`: pilot readiness state
- `s2`: audited readiness state
- `s3`: pilot then stall
- `s5`: direct leap target
- `s6`: resilience-first audited digital rollout
- `s9`: readiness-based regional rollout

## Transitions
- `t1`: conservative layered rollout
- `t2`: resilience-first audited rollout
- `t3`: direct leap rollout
- `t4`: readiness-based regional rollout
- `t5`: pilot then stall

## Candidate Paths
### Path A: conservative layering
- `s0 -> s1 -> s2 -> s5`
- slower path through pilots and controls

### Path B: resilience-first modernization
- `s0 -> s1 -> s2 -> s6`
- audited route optimized for resilience

### Path C: direct leap
- `s0 -> s5`
- immediate digitization leap

### Path D: regional rollout
- `s0 -> s1 -> s2 -> s9 -> s6`
- phased rollout by region

### Path E: pilot then stall
- `s0 -> s1 -> s2 -> s3`
- progress without sustained rollout
"""
        story = DstEmbeddedStory(
            self,
            name="embedded_exam_rollout",
            markdown=markdown,
        )

        story.given_embedded_dst_prose()
        story.when_governed_candidate_path_discovery_runs()
        story.when_the_end_to_end_dst_pipeline_runs(subject_id="exam-rollout")

        story.then_candidate_paths_are(
            (
                "Path A: conservative layering",
                "Path B: resilience-first modernization",
                "Path C: direct leap",
                "Path D: regional rollout",
                "Path E: pilot then stall",
            )
        )
        story.then_path_kinds_are(
            ("multi_step", "multi_step", "single_step", "multi_step", "multi_step")
        )
        story.then_the_normalized_candidate_surface_has(transition_count=2, decision_count=5)
        story.then_valid_decision_titles_include_set(
            (
                "Path A: conservative layering",
                "Path B: resilience-first modernization",
                "Path C: direct leap",
                "Path D: regional rollout",
                "Path E: pilot then stall",
            )
        )
        story.then_executable_decision_titles_include_set(
            (
                "Path C: direct leap",
                "Path B: resilience-first modernization",
                "Path E: pilot then stall",
                "Path D: regional rollout",
                "Path A: conservative layering",
            )
        )

    def test_bdd_selected_item_construct_discovery_returns_runtime_tagged_candidates(self) -> None:
        markdown = """# Fare Modernization

## Situation
A transit authority wants to modernize fare payment without breaking service.

## Actors
- `a1`: transit authority
- `a2`: payment processor
- `a3`: regulator

## Objectives
- `o1`: reduce boarding time
- `o2`: preserve continuity

## Capabilities
- `k1`: improved closed-loop card system
- `k2`: open-loop payment acceptance

## Dependencies
- `d1`: certification approval
- `d2`: payment network readiness

## Constraints
- `q1`: no downtime

## Boundaries
- `b1`: transit-payment boundary

## States
- `s0`: legacy fare system
- `s1`: improved closed-loop card system
- `s2`: hybrid payment environment
- `s3`: full open-loop payment

## Transitions
- `t1`: legacy to improved closed-loop
- `t2`: improved closed-loop to hybrid
- `t3`: hybrid to full open-loop

## Candidate Paths
### Path A: staged modernization route
A staged route reduces disruption by improving the existing card system first and then expanding.
- `s0 -> s1 -> s2 -> s3`
- preserves continuity while capabilities and approvals mature

### Path B: direct open-loop route
A direct route aims for the target immediately but depends on readiness across the payment boundary.
- `s0 -> s3`
- faster but riskier if certification and network readiness are incomplete
"""
        story = DstEmbeddedStory(
            self,
            name="embedded_fare_modernization_for_constructs",
            markdown=markdown,
        )
        story.given_embedded_dst_prose()
        story.when_governed_candidate_path_discovery_runs()
        story.when_dst_normalization_runs()
        story.then_selected_item_construct_discovery_returns_runtime_tagged_candidates(
            subject_id="fare-modernization"
        )


if __name__ == "__main__":
    unittest.main()
