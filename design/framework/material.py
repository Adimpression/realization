"""Material framework encodings for typed design mediation."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import FrameworkEncoding


@dataclass(frozen=True, slots=True)
class MaterialButtonEncoding(FrameworkEncoding):
    framework_name: str = field(default="material", init=False)
    component_type: str = field(default="button", init=False)
    variant: str = "filled"


@dataclass(frozen=True, slots=True)
class MaterialDialogEncoding(FrameworkEncoding):
    framework_name: str = field(default="material", init=False)
    component_type: str = field(default="dialog", init=False)
    emphasis: str = "blocking"


@dataclass(frozen=True, slots=True)
class MaterialCardEncoding(FrameworkEncoding):
    framework_name: str = field(default="material", init=False)
    component_type: str = field(default="card", init=False)
    emphasis: str = "supporting"


@dataclass(frozen=True, slots=True)
class MaterialNavigationBarEncoding(FrameworkEncoding):
    framework_name: str = field(default="material", init=False)
    component_type: str = field(default="navigation_bar", init=False)
    destination_count: int = 0

