"""Non-semantic performance measurements for governed execution."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from functools import wraps
from time import perf_counter_ns
from typing import Any, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


@dataclass(slots=True)
class PerformanceRecorder:
    """Accumulate monotonic timings without entering semantic state."""

    _measurements: dict[str, int] = field(default_factory=dict)

    def add(self, name: str, value: int) -> None:
        if value < 0:
            raise ValueError("performance measurements cannot be negative")
        self._measurements[name] = self._measurements.get(name, 0) + value

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        started = perf_counter_ns()
        try:
            yield
        finally:
            self.add(name, perf_counter_ns() - started)

    def snapshot(self) -> dict[str, int]:
        return dict(sorted(self._measurements.items()))


_ACTIVE_RECORDER: ContextVar[PerformanceRecorder | None] = ContextVar(
    "realized_performance_recorder",
    default=None,
)


@contextmanager
def performance_scope(recorder: PerformanceRecorder) -> Iterator[None]:
    """Make a recorder available to nested runtime operations."""

    token: Token[PerformanceRecorder | None] = _ACTIVE_RECORDER.set(recorder)
    try:
        yield
    finally:
        _ACTIVE_RECORDER.reset(token)


@contextmanager
def measure_performance(name: str) -> Iterator[None]:
    """Measure against the active recorder, or become a no-op."""

    recorder = _ACTIVE_RECORDER.get()
    if recorder is None:
        yield
        return
    with recorder.measure(name):
        yield


def measured_performance(
    name: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a synchronous operation with context-local measurement."""

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def measured(*args: P.args, **kwargs: P.kwargs) -> R:
            with measure_performance(name):
                return function(*args, **kwargs)

        return measured

    return decorate


def merge_performance_measurements(
    *measurements: Mapping[str, Any],
) -> dict[str, int]:
    """Add compatible integer measurements from independent layers."""

    merged: dict[str, int] = {}
    for values in measurements:
        for key, raw_value in values.items():
            value = int(raw_value)
            if value < 0:
                raise ValueError("performance measurements cannot be negative")
            merged[str(key)] = merged.get(str(key), 0) + value
    return dict(sorted(merged.items()))


__all__ = [
    "PerformanceRecorder",
    "measure_performance",
    "measured_performance",
    "merge_performance_measurements",
    "performance_scope",
]
