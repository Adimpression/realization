from __future__ import annotations

import unittest

from realized_core_governance import (
    admission,
    approval,
    data,
    declarations,
    inventory,
    lifecycle,
    records,
    safety,
    vocabulary,
)


class CoreGovernanceApiTests(unittest.TestCase):
    def test_package_exports_only_governance_modules(self) -> None:
        import realized_core_governance

        self.assertEqual(
            [
                "admission",
                "approval",
                "data",
                "declarations",
                "inventory",
                "lifecycle",
                "records",
                "safety",
                "vocabulary",
            ],
            realized_core_governance.__all__,
        )
        self.assertIs(realized_core_governance.admission, admission)
        self.assertIs(realized_core_governance.approval, approval)
        self.assertIs(realized_core_governance.data, data)
        self.assertIs(realized_core_governance.declarations, declarations)
        self.assertIs(realized_core_governance.inventory, inventory)
        self.assertIs(realized_core_governance.lifecycle, lifecycle)
        self.assertIs(realized_core_governance.records, records)
        self.assertIs(realized_core_governance.safety, safety)
        self.assertIs(realized_core_governance.vocabulary, vocabulary)

    def test_module_exports_are_explicit_unique_and_resolvable(self) -> None:
        for module in (
            admission,
            approval,
            data,
            declarations,
            inventory,
            lifecycle,
            records,
            safety,
            vocabulary,
        ):
            with self.subTest(module=module.__name__):
                self.assertEqual(len(module.__all__), len(set(module.__all__)))
                for name in module.__all__:
                    self.assertTrue(hasattr(module, name), name)


if __name__ == "__main__":
    unittest.main()
