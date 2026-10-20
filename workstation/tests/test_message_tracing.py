# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from workstation.foundation.events.message_tracing import DuplicateWorkstationMessageError, register_message_trace


class MessageTracingTests(unittest.TestCase):
    def test_register_message_trace_raises_on_recent_duplicate(self) -> None:
        register_message_trace(trace_id="trace-unit-test-1", parent_id="parent-a", message_kind="unit")
        with self.assertRaises(DuplicateWorkstationMessageError):
            register_message_trace(trace_id="trace-unit-test-1", parent_id="parent-a", message_kind="unit")
