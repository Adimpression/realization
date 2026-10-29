"""Public Decision Support Tool API."""

from . import core as _core
from . import discovery as _discovery
from . import normalization as _normalization
from . import orchestration as _orchestration
from . import projection as _projection
from . import revision as _revision


_PUBLIC_MODULES = (
    _core,
    _discovery,
    _normalization,
    _orchestration,
    _projection,
    _revision,
)

__all__ = tuple(
    name
    for module in _PUBLIC_MODULES
    for name in module.__all__
)

if len(__all__) != len(set(__all__)):
    raise RuntimeError("DST public modules export duplicate names")

for _module in _PUBLIC_MODULES:
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)

del _module
del _name
