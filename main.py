# See MODULES.md for the repository module map before editing.
"""Historical import and executable facade for the canonical controller runtime."""
from __future__ import annotations

import sys

import controller_runtime as _runtime
from controller_entrypoint_binding import register_controller_entrypoint


def _run_controller_entrypoint() -> int:
    """Load the optional CLI composition surface only when it is executed."""
    from controller_entrypoints import main as controller_main

    return int(controller_main())


register_controller_entrypoint(_run_controller_entrypoint)

if __name__ == "__main__":
    raise SystemExit(_runtime.main())

# Preserve historical object identity and patch paths for `import main` callers.
sys.modules[__name__] = _runtime
