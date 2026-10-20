import unittest

from dst import (
    DST_SORT_ATOM_ORDER,
    build_dst_prompt_input,
    build_reduce_not_discovery_prompt,
    discovery_result_from_fixture,
    list_dst_discovery_fixture_paths,
    load_dst_discovery_results,
    load_dst_use_cases,
)


class DstDiscoveryTests(unittest.TestCase):
    def test_discovery_fixture_root_lists_checked_in_discovery_cases(self) -> None:
        paths = list_dst_discovery_fixture_paths()

        self.assertEqual(
            [path.name for path in paths],
            [
                "city-bus-ticketing-modernization.json",
                "regional-emergency-alerting-system.json",
            ],
        )

    def test_load_dst_discovery_results_reads_typed_candidate_path_discovery_cases(self) -> None:
        results = load_dst_discovery_results()

        self.assertEqual(
            [item.fixture_id for item in results],
            [
                "city-bus-ticketing-modernization",
                "regional-emergency-alerting-system",
            ],
        )
        bus = results[0]
        self.assertEqual(len(bus.candidate_paths), 2)
        self.assertEqual(
            bus.dominant_distinctions[0].separates_path_ids,
            ("p1-conservative-modernization", "p2-coordinated-leap"),
        )

    def test_build_reduce_not_discovery_prompt_shapes_candidate_path_search_against_fixture(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        prompt = build_reduce_not_discovery_prompt(fixture)

        self.assertIn("Root non-achievedness:", prompt)
        self.assertIn("preserve multiplicity; do not collapse to one recommendation", prompt)
        self.assertIn("s0 -> s1 -> s2", prompt)
        self.assertIn("s0 -> s3", prompt)
        self.assertIn("City bus ticketing modernization", prompt)
        self.assertIn("DST sort-atom lexicon:", prompt)
        self.assertIn("Return exactly these top-level sections:", prompt)
        self.assertIn("sort_atom_context", prompt)
        for label in DST_SORT_ATOM_ORDER:
            self.assertIn(f"- {label}:", prompt)

    def test_build_dst_prompt_input_carries_discovery_paths_distinctions_and_blockers_forward(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )
        discovery = next(
            item for item in load_dst_discovery_results()
            if item.fixture_id == fixture.fixture_id
        )

        prompt_input = build_dst_prompt_input(fixture, discovery)

        self.assertIn("Governed discovery candidate paths:", prompt_input)
        self.assertIn("p1-conservative-modernization | Path A: conservative modernization", prompt_input)
        self.assertIn("Dominant distinctions:", prompt_input)
        self.assertIn("Shared blockers:", prompt_input)
        self.assertIn("Missing information:", prompt_input)

    def test_discovery_result_from_fixture_preserves_route_shape_for_configuration_cases_and_seeds_sort_atom_context(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "regional-emergency-alerting-system"
        )

        discovery = discovery_result_from_fixture(fixture)

        self.assertEqual([item.path_kind for item in discovery.candidate_paths], ["configuration", "configuration", "configuration", "configuration"])
        self.assertEqual(discovery.root_non_achievedness.startswith("What are the materially distinct admissible transformation paths"), True)
        self.assertEqual(
            discovery.sort_atom_context.actors[0],
            fixture.section_entries("actors")[0].text,
        )
        self.assertEqual(
            discovery.sort_atom_context.capabilities[0],
            fixture.section_entries("capabilities")[0].text,
        )
        self.assertEqual(discovery.sort_atom_context.decisions, tuple(item.title for item in fixture.candidate_paths))


if __name__ == "__main__":
    unittest.main()
