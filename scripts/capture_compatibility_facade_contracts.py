#!/usr/bin/env python3
"""Capture executable compatibility contracts for repository-root facades."""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import io
import json
import pickle
import re
import sys
import unittest
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_INVENTORY_PATH = ROOT / "architecture" / "compatibility-facades.json"
DEFAULT_OUTPUT_PATH = (
    ROOT / "architecture" / "compatibility-facade-contracts.json"
)
CONTRACT_TEST_MODULE = "tests.test_architecture_compatibility_facades"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def _protocol_zero_global(data: object) -> tuple[str, str] | None:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        return None
    raw = bytes(data)
    if not raw.startswith(b"c"):
        return None
    parts = raw[1:].split(b"\n", 2)
    if len(parts) < 2:
        return None
    try:
        module = parts[0].decode("ascii")
        name = parts[1].decode("ascii")
    except UnicodeDecodeError:
        return None
    if not module or not name:
        return None
    return module, name


def _run_contract_suite() -> tuple[dict[str, list[str]], dict[str, Any]]:
    contract_tests = importlib.import_module(CONTRACT_TEST_MODULE)
    original_loads = pickle.loads
    observed: dict[str, set[str]] = defaultdict(set)

    def recording_loads(data: object, *args: object, **kwargs: object) -> Any:
        global_name = _protocol_zero_global(data)
        if global_name is not None:
            module, name = global_name
            observed[module].add(name)
        return original_loads(data, *args, **kwargs)

    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(contract_tests)
    with patch.object(pickle, "loads", recording_loads):
        result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError(
            "compatibility contract suite failed while capturing contracts:\n"
            + stream.getvalue()
        )
    return (
        {module: sorted(names) for module, names in sorted(observed.items())},
        {
            "errors": len(result.errors),
            "failures": len(result.failures),
            "module": CONTRACT_TEST_MODULE,
            "tests_run": result.testsRun,
        },
    )


def _safe_signature(value: object) -> str:
    if not callable(value):
        return ""
    try:
        signature = str(inspect.signature(value))
    except (TypeError, ValueError):
        return "<unavailable>"
    signature = re.sub(r"0x[0-9a-fA-F]+", "0x...", signature)

    def stable_frozenset(match: re.Match[str]) -> str:
        try:
            values = ast.literal_eval("{" + match.group("items") + "}")
        except (SyntaxError, ValueError):
            return match.group(0)
        if not isinstance(values, set):
            return match.group(0)
        return "frozenset({" + ", ".join(sorted(map(repr, values))) + "})"

    return re.sub(
        r"frozenset\(\{(?P<items>[^{}]*)\}\)",
        stable_frozenset,
        signature,
    )


def _module_contract_surface(module: ModuleType) -> dict[str, Any]:
    explicit_all_value = getattr(module, "__all__", None)
    explicit_all = (
        sorted({str(name) for name in explicit_all_value})
        if isinstance(explicit_all_value, (list, tuple, set, frozenset))
        else []
    )
    public_names = sorted(
        name for name in vars(module) if not name.startswith("_")
    )
    exported_names = explicit_all or public_names
    signatures = {
        name: signature
        for name in exported_names
        if (signature := _safe_signature(getattr(module, name, None)))
    }
    constant_types = {
        name: type(value).__name__
        for name in exported_names
        if (value := getattr(module, name, None)) is not None
        and not callable(value)
        and not isinstance(value, ModuleType)
    }
    return {
        "constant_types": constant_types,
        "explicit_all": explicit_all,
        "public_names": public_names,
        "signatures": signatures,
    }


def _proof_strategy(shape: str) -> str:
    if shape == "exact_module_alias":
        return "exact_module_object_identity"
    if shape == "symbol_reexport":
        return "exported_symbol_object_identity"
    if shape == "aggregate_reexport":
        return "manual_multi_owner_export_mapping"
    return "manual_behavior_equivalence"


def build_contracts(
    *,
    inventory_path: Path = DEFAULT_INVENTORY_PATH,
) -> dict[str, Any]:
    inventory = _load_json(inventory_path)
    pickle_globals, suite_evidence = _run_contract_suite()
    inventory_facades = inventory.get("facades", [])
    if not isinstance(inventory_facades, list):
        raise ValueError("compatibility inventory facades must be a list")
    facade_names = {str(row["module"]) for row in inventory_facades}
    unexpected_pickle_modules = sorted(set(pickle_globals) - facade_names)
    if unexpected_pickle_modules:
        raise ValueError(
            "contract suite exercised un-inventoried pickle modules: "
            + ", ".join(unexpected_pickle_modules)
        )

    cards: list[dict[str, Any]] = []
    for facade in inventory_facades:
        module_name = str(facade["module"])
        module = importlib.import_module(module_name)
        canonical_module_identity = str(
            facade.get("canonical_module_identity", "")
        )
        exact_identity_observed: bool | None = None
        if canonical_module_identity:
            canonical_module = importlib.import_module(canonical_module_identity)
            exact_identity_observed = module is canonical_module
        shape = str(facade["shape"])
        pickle_names = pickle_globals.get(module_name, [])
        cards.append(
            {
                "canonical_module_identity": canonical_module_identity,
                "canonical_targets": facade.get("canonical_targets", []),
                "command_replacements": facade.get("replacement_commands", []),
                "contract_evidence": CONTRACT_TEST_MODULE,
                "durable_pickle_globals": pickle_names,
                "exact_module_identity_observed": exact_identity_observed,
                "executable_surface": bool(facade.get("executable_surface")),
                "export_surface": _module_contract_surface(module),
                "import_effect_class": (
                    "module_alias_only"
                    if shape == "exact_module_alias"
                    else "symbol_projection"
                    if shape == "symbol_reexport"
                    else "multi_owner_projection"
                    if shape == "aggregate_reexport"
                    else "behavior_or_composition"
                ),
                "module": module_name,
                "owner": facade["owner"],
                "path": facade["path"],
                "proof_strategy": _proof_strategy(shape),
                "rollback_operation": (
                    f"restore {facade['path']} and its compatibility contract "
                    "assertions without reverting the canonical owner"
                ),
                "shape": shape,
                "support_status": facade["support_status"],
            }
        )

    exact_alias_failures = [
        card["module"]
        for card in cards
        if card["shape"] == "exact_module_alias"
        and card["exact_module_identity_observed"] is not True
    ]
    if exact_alias_failures:
        raise RuntimeError(
            "exact aliases did not preserve canonical module identity: "
            + ", ".join(exact_alias_failures)
        )

    return {
        "cards": cards,
        "contract_suite": suite_evidence,
        "schema_version": 1,
        "summary": {
            "card_count": len(cards),
            "exact_module_identity_count": sum(
                card["exact_module_identity_observed"] is True for card in cards
            ),
            "facades_with_durable_pickle_globals": sum(
                bool(card["durable_pickle_globals"]) for card in cards
            ),
            "pickle_global_count": sum(
                len(card["durable_pickle_globals"]) for card in cards
            ),
            "proof_strategy_counts": {
                strategy: sum(
                    card["proof_strategy"] == strategy for card in cards
                )
                for strategy in sorted(
                    {card["proof_strategy"] for card in cards}
                )
            },
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture or verify repository compatibility-facade contracts."
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help="generated compatibility inventory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="checked-in compatibility contract ledger",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the checked-in contract ledger",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inventory_path = args.inventory.resolve()
    output_path = args.output.resolve()
    current = build_contracts(inventory_path=inventory_path)
    rendered = _canonical_json(current)
    if args.update:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    elif not output_path.is_file():
        print(f"missing compatibility contract ledger: {output_path}", file=sys.stderr)
        return 1
    elif output_path.read_text(encoding="utf-8") != rendered:
        print(
            "compatibility facade contract ledger is stale; run "
            "scripts/capture_compatibility_facade_contracts.py --update",
            file=sys.stderr,
        )
        return 1
    print(
        "compatibility facade contracts passed: "
        f"{current['summary']['card_count']} cards, "
        f"{current['summary']['facades_with_durable_pickle_globals']} "
        "facades with pickle globals, "
        f"{current['contract_suite']['tests_run']} contract tests"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
