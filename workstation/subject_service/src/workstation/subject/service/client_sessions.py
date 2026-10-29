# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
import threading
import uuid

from realized_core_semantics.semantic_text import collapse_ws
from workstation.subject.core.subject_workflow import (
    SubjectProgress,
    apply_subject_progress_client_view_payload,
    infer_subject_progress_client_view_defaults,
    subject_progress_client_view_payload,
)


@dataclass
class _ClientSessionRecord:
    subject_view_state_by_subject_id: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass
class WorkstationClientSessionRegistry:
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _records_by_root_and_session: dict[tuple[str, str], _ClientSessionRecord] = field(default_factory=dict)

    def open_client_session(self, *, root_path: Path, client_session_id: str = "") -> str:
        normalized_root = self._normalized_root(root_path)
        normalized_session_id = collapse_ws(client_session_id) or f"client-{uuid.uuid4().hex}"
        key = (normalized_root, normalized_session_id)
        with self._lock:
            self._records_by_root_and_session.setdefault(key, _ClientSessionRecord())
        return normalized_session_id

    def close_client_session(self, *, root_path: Path, client_session_id: str) -> None:
        normalized_root = self._normalized_root(root_path)
        normalized_session_id = collapse_ws(client_session_id)
        if not normalized_session_id:
            return
        with self._lock:
            self._records_by_root_and_session.pop((normalized_root, normalized_session_id), None)

    def subject_progress_with_session_view(
        self,
        *,
        root_path: Path,
        client_session_id: str,
        subject_id: str,
        durable_progress: SubjectProgress,
    ) -> SubjectProgress:
        progress = copy.deepcopy(durable_progress)
        payload = self.subject_view_payload(
            root_path=root_path,
            client_session_id=client_session_id,
            subject_id=subject_id,
        )
        if not payload:
            inferred = infer_subject_progress_client_view_defaults(
                root_path=root_path,
                subject_id=subject_id,
                progress=progress,
            )
            payload = subject_progress_client_view_payload(inferred)
            if payload:
                self.replace_subject_view_payload(
                    root_path=root_path,
                    client_session_id=client_session_id,
                    subject_id=subject_id,
                    payload=payload,
                )
        return apply_subject_progress_client_view_payload(progress, payload)

    def subject_view_payload(
        self,
        *,
        root_path: Path,
        client_session_id: str,
        subject_id: str,
    ) -> dict[str, object]:
        normalized_root = self._normalized_root(root_path)
        normalized_session_id = collapse_ws(client_session_id)
        normalized_subject_id = collapse_ws(subject_id)
        if not normalized_session_id or not normalized_subject_id:
            return {}
        key = (normalized_root, normalized_session_id)
        with self._lock:
            record = self._records_by_root_and_session.get(key)
            if record is None:
                return {}
            payload = record.subject_view_state_by_subject_id.get(normalized_subject_id, {})
            return copy.deepcopy(payload)

    def update_subject_view_from_progress(
        self,
        *,
        root_path: Path,
        client_session_id: str,
        subject_id: str,
        progress: SubjectProgress,
    ) -> None:
        normalized_root = self._normalized_root(root_path)
        normalized_session_id = collapse_ws(client_session_id)
        normalized_subject_id = collapse_ws(subject_id)
        if not normalized_session_id or not normalized_subject_id:
            return
        key = (normalized_root, normalized_session_id)
        payload = subject_progress_client_view_payload(progress)
        with self._lock:
            record = self._records_by_root_and_session.setdefault(key, _ClientSessionRecord())
            record.subject_view_state_by_subject_id[normalized_subject_id] = payload

    def replace_subject_view_payload(
        self,
        *,
        root_path: Path,
        client_session_id: str,
        subject_id: str,
        payload: dict[str, object],
    ) -> None:
        normalized_root = self._normalized_root(root_path)
        normalized_session_id = collapse_ws(client_session_id)
        normalized_subject_id = collapse_ws(subject_id)
        if not normalized_session_id or not normalized_subject_id:
            return
        key = (normalized_root, normalized_session_id)
        with self._lock:
            record = self._records_by_root_and_session.setdefault(key, _ClientSessionRecord())
            record.subject_view_state_by_subject_id[normalized_subject_id] = copy.deepcopy(dict(payload))

    @staticmethod
    def _normalized_root(root_path: Path) -> str:
        return str(Path(root_path).expanduser().resolve())


_ClientSessionRecord.__module__ = "workstation.foundation.host.client_sessions"
WorkstationClientSessionRegistry.__module__ = "workstation.foundation.host.client_sessions"

__all__ = ["WorkstationClientSessionRegistry"]
