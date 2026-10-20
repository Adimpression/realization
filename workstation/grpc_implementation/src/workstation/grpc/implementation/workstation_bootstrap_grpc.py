# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import grpc

from semantic_text import collapse_ws
from workstation.foundation.events.message_tracing import derived_trace_id, new_trace_id, register_message_trace
from workstation.grpc.definitions import workstation_bootstrap_pb2, workstation_bootstrap_pb2_grpc


@dataclass(frozen=True)
class ServedWorkstationRoot:
    root_id: str
    label: str
    root_path: Path
    workspace_name: str = ""
    is_default: bool = False


def _registered_trace_fields(
    *,
    message_kind: str,
    prefix: str,
    parent_id: str = "",
    components: tuple[object, ...] = (),
) -> tuple[str, str]:
    trace_id = (
        derived_trace_id(prefix, *(components or (parent_id or new_trace_id(prefix),)))
        if components
        else new_trace_id(prefix)
    )
    return register_message_trace(
        trace_id=trace_id,
        parent_id=parent_id,
        message_kind=message_kind,
    )


def _default_root_id(path: Path) -> str:
    normalized = collapse_ws(path.name or path.as_posix())
    slug = "".join(character if character.isalnum() else "-" for character in normalized.casefold()).strip("-")
    return slug or "workstation"


def _default_root_label(path: Path) -> str:
    return collapse_ws(path.name.replace("-", " ").replace("_", " ").title()) or path.as_posix()


class WorkstationRootRegistry:
    def __init__(self, roots: Iterable[ServedWorkstationRoot] = ()) -> None:
        normalized_roots: list[ServedWorkstationRoot] = []
        default_seen = False
        for index, root in enumerate(roots):
            resolved_path = Path(root.root_path).expanduser().resolve()
            normalized_root = ServedWorkstationRoot(
                root_id=collapse_ws(root.root_id) or _default_root_id(resolved_path),
                label=collapse_ws(root.label) or _default_root_label(resolved_path),
                root_path=resolved_path,
                workspace_name=collapse_ws(root.workspace_name) or resolved_path.name,
                is_default=bool(root.is_default) or (index == 0 and not default_seen),
            )
            if normalized_root.is_default:
                default_seen = True
            normalized_roots.append(normalized_root)
        self._roots = tuple(normalized_roots)
        self._root_by_path = {root.root_path: root for root in self._roots}

    @classmethod
    def from_paths(
        cls,
        paths: Iterable[Path],
        *,
        default_root: str = "",
    ) -> WorkstationRootRegistry:
        normalized_default = collapse_ws(default_root)
        roots: list[ServedWorkstationRoot] = []
        for index, raw_path in enumerate(paths):
            resolved_path = Path(raw_path).expanduser().resolve()
            root_id = _default_root_id(resolved_path)
            roots.append(
                ServedWorkstationRoot(
                    root_id=root_id,
                    label=_default_root_label(resolved_path),
                    root_path=resolved_path,
                    workspace_name=resolved_path.name,
                    is_default=bool(normalized_default and normalized_default in {root_id, str(resolved_path)}) or index == 0,
                )
            )
        return cls(roots)

    def descriptors(self) -> tuple[ServedWorkstationRoot, ...]:
        return self._roots

    def descriptor_for_path(self, root_path: str | Path) -> ServedWorkstationRoot | None:
        resolved = Path(root_path).expanduser().resolve()
        return self._root_by_path.get(resolved)

    def resolve_root_path(self, root_path: str | Path) -> Path:
        resolved = Path(root_path).expanduser().resolve()
        if self._roots:
            if resolved not in self._root_by_path:
                raise ValueError(f"Root path is not advertised by this workstation host: {resolved}")
            return resolved
        if not resolved.exists():
            raise ValueError(f"Root path does not exist: {resolved}")
        return resolved


def _root_descriptor_message(root: ServedWorkstationRoot) -> workstation_bootstrap_pb2.WorkstationRootDescriptor:
    return workstation_bootstrap_pb2.WorkstationRootDescriptor(
        root_id=root.root_id,
        label=root.label,
        root_path=str(root.root_path),
        workspace_name=root.workspace_name,
        is_default=bool(root.is_default),
    )


class WorkstationBootstrapGrpcService(workstation_bootstrap_pb2_grpc.WorkstationBootstrapServiceServicer):
    def __init__(self, *, root_registry: WorkstationRootRegistry | None = None) -> None:
        self._root_registry = root_registry or WorkstationRootRegistry()

    def ListWorkstationRoots(
        self,
        request: workstation_bootstrap_pb2.ListWorkstationRootsRequest,
        context: grpc.ServicerContext,
    ) -> workstation_bootstrap_pb2.ListWorkstationRootsResponse:
        del request
        del context
        roots = self._root_registry.descriptors()
        parent_id = new_trace_id("bootstrap-roots-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="ListWorkstationRootsResponse",
            prefix="bootstrap-roots-response",
            parent_id=parent_id,
            components=(parent_id, *(str(root.root_path) for root in roots)),
        )
        return workstation_bootstrap_pb2.ListWorkstationRootsResponse(
            roots=[_root_descriptor_message(root) for root in roots],
            trace_id=trace_id,
            parent_id=parent_id,
        )
