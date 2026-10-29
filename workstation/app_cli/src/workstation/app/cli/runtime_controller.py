"""Subject-scoped controller bootstrap owned by workstation composition."""

# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from realized_host_interaction.context import HostInteractionContext
from workstation.subject.core.learning_context import (
    SubjectImport,
    SubjectReasoningScope,
    learning_context_projected_skill_ids,
    load_learning_context,
)
from realized_exchange.learning_context_skills import (
    materialize_learning_context_skill_projections,
    projected_skill_filename,
)
from realized_core_semantics.semantic_text import collapse_ws, ordered_unique
from realized_exchange.skill_schema import load_skill_yaml_documents


def _normalized_subject_reasoning_scope(subject_scope: Any) -> SubjectReasoningScope | None:
    if subject_scope is None:
        return None
    if isinstance(subject_scope, SubjectReasoningScope):
        return subject_scope
    if not isinstance(subject_scope, Mapping):
        return None
    imported_subjects = []
    for item in list(subject_scope.get("imported_subjects", [])):
        if isinstance(item, Mapping):
            imported_subjects.append(SubjectImport.from_dict(dict(item)))
    return SubjectReasoningScope(
        active_subject_id=collapse_ws(str(subject_scope.get("active_subject_id", ""))),
        active_subject_version_id=collapse_ws(str(subject_scope.get("active_subject_version_id", ""))),
        active_subject_title=collapse_ws(str(subject_scope.get("active_subject_title", ""))),
        imported_subjects=tuple(imported_subjects),
        global_retrieval_policy=collapse_ws(str(subject_scope.get("global_retrieval_policy", ""))) or "disabled",
    )


def _subject_import_scope_skill_ids(root_path: Path, subject_import: SubjectImport) -> tuple[str, ...]:
    explicit_skill_ids = tuple(str(item) for item in subject_import.imported_skill_ids if collapse_ws(str(item)))
    if explicit_skill_ids:
        return tuple(ordered_unique(explicit_skill_ids))
    if subject_import.imported_unit_ids:
        try:
            source_context = load_learning_context(root_path, subject_import.source_subject_id)
        except Exception:
            return ()
        imported_unit_ids = {str(item) for item in subject_import.imported_unit_ids if collapse_ws(str(item))}
        return tuple(
            ordered_unique(
                str(skill_id)
                for unit in source_context.units
                if unit.unit_id in imported_unit_ids
                for skill_id in unit.linked_skill_ids
                if collapse_ws(str(skill_id))
            )
        )
    has_any_explicit_slice = any(
        (
            subject_import.imported_source_ids,
            subject_import.imported_claim_ids,
            subject_import.imported_section_ids,
        )
    )
    if has_any_explicit_slice:
        return ()
    try:
        source_context = load_learning_context(root_path, subject_import.source_subject_id)
    except Exception:
        return ()
    return learning_context_projected_skill_ids(source_context)


def _load_projected_scope_artifacts(
    root_path: Path,
    *,
    subject_id: str,
    skill_ids: tuple[str, ...],
) -> list[Any]:
    if not collapse_ws(subject_id) or not skill_ids:
        return []
    try:
        context = load_learning_context(root_path, subject_id)
        materialize_learning_context_skill_projections(root_path, context)
    except Exception:
        return []
    derived_root = root_path / "corpus" / collapse_ws(subject_id) / "derived" / "skills"
    ordered_artifacts: dict[str, Any] = {}
    for skill_id in skill_ids:
        path = derived_root / projected_skill_filename(skill_id)
        if not path.is_file():
            continue
        for artifact in load_skill_yaml_documents(path):
            ordered_artifacts.setdefault(str(getattr(artifact, "id", "")), artifact)
    return list(ordered_artifacts.values())


def _subject_scope_artifacts(root_path: Path, subject_scope: SubjectReasoningScope) -> tuple[list[Any], dict[str, dict[str, Any]]]:
    ordered_artifacts: dict[str, Any] = {}
    artifact_origins: dict[str, dict[str, Any]] = {}
    try:
        active_context = load_learning_context(root_path, subject_scope.active_subject_id)
    except Exception:
        active_context = None
    active_skill_ids = learning_context_projected_skill_ids(active_context) if active_context is not None else ()
    for artifact in _load_projected_scope_artifacts(
        root_path,
        subject_id=subject_scope.active_subject_id,
        skill_ids=active_skill_ids,
    ):
        artifact_id = str(getattr(artifact, "id", "")).strip()
        if not artifact_id:
            continue
        ordered_artifacts.setdefault(artifact_id, artifact)
        artifact_origins.setdefault(
            artifact_id,
            {
                "origin_kind": "primary",
                "source_subject_id": subject_scope.active_subject_id,
                "source_subject_version_id": subject_scope.active_subject_version_id,
                "source_subject_title": subject_scope.active_subject_title,
            },
        )
    for subject_import in subject_scope.imported_subjects:
        for artifact in _load_projected_scope_artifacts(
            root_path,
            subject_id=subject_import.source_subject_id,
            skill_ids=_subject_import_scope_skill_ids(root_path, subject_import),
        ):
            artifact_id = str(getattr(artifact, "id", "")).strip()
            if not artifact_id or artifact_id in ordered_artifacts:
                continue
            ordered_artifacts[artifact_id] = artifact
            artifact_origins[artifact_id] = {
                "origin_kind": "borrowed",
                "source_subject_id": subject_import.source_subject_id,
                "source_subject_version_id": subject_import.source_subject_version_id,
                "source_subject_title": subject_import.source_subject_title,
                "source_import_id": subject_import.import_id,
                "import_kind": subject_import.import_kind,
            }
    return list(ordered_artifacts.values()), artifact_origins


def seed_runtime_controller_subject_scope(
    state: Any,
    *,
    subject_scope_root_path: Path,
    subject_scope: Any,
) -> None:
    normalized_scope = _normalized_subject_reasoning_scope(subject_scope)
    if normalized_scope is None:
        return
    normalized_root = Path(subject_scope_root_path).expanduser().resolve()
    artifacts, artifact_origins = _subject_scope_artifacts(normalized_root, normalized_scope)
    state.subject_reasoning_scope = normalized_scope.to_dict()
    state.learned_artifact_origins = dict(getattr(state, "learned_artifact_origins", {}) or {})
    for artifact_id, origin in artifact_origins.items():
        state.learned_artifact_origins[str(artifact_id)] = dict(origin)
    for artifact in artifacts:
        artifact_id = str(getattr(artifact, "id", "")).strip()
        if artifact_id:
            state.learned_artifacts.setdefault(artifact_id, artifact)
    state.supplement_profile = dict(getattr(state, "supplement_profile", {}) or {})
    state.supplement_profile["subject_reasoning_scope"] = state.subject_reasoning_scope
    state.supplement_profile["subject_reasoning_loaded_artifact_count"] = len(artifacts)


def bootstrap_runtime_controller(
    *,
    semantic_unit: str,
    llm_policy: str = "off",
    subject_scope: Any | None = None,
    subject_scope_root_path: Path | None = None,
    host_interaction_context: HostInteractionContext | None = None,
) -> tuple[Any, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill execution over the governed runtime, helps with bootstrapping one controller instance and its state through a narrow runtime facade.

    Reference to Theory:
        Supports six-layer extraction by letting workstation and other lower layers depend on a smaller runtime contract instead of importing controller/runtime internals directly from `main.py`.

    Example Input Output:
        Input: `bootstrap_runtime_controller(semantic_unit='Compute force from mass and acceleration.', llm_policy='off')`
        Output: (SystemState.bootstrap('Compute force from mass and acceleration.'), BSSCController(...))

    Args:
        semantic_unit: Value for `semantic_unit` used by `bootstrap_runtime_controller`. Expected type: `str`.
        llm_policy: Value for `llm_policy` used by `bootstrap_runtime_controller`. Expected type: `str`. Defaults to `'off'`.

    Returns:
        tuple[SystemState, Any]: Result produced by `bootstrap_runtime_controller`.
    """
    from realized_core_engine.controller_runtime import BSSCController
    from realized_core_engine.state import SystemState

    state = SystemState.bootstrap(semantic_unit)
    if subject_scope is not None:
        if subject_scope_root_path is None:
            raise ValueError("subject_scope_root_path is required when subject_scope is provided.")
        seed_runtime_controller_subject_scope(
            state,
            subject_scope_root_path=subject_scope_root_path,
            subject_scope=subject_scope,
        )
    controller = BSSCController(
        state,
        llm_policy=llm_policy,
        host_interaction_context=host_interaction_context,
    )
    return state, controller


def new_runtime_controller(
    state: Any,
    *,
    llm_policy: str = "off",
    subject_scope: Any | None = None,
    subject_scope_root_path: Path | None = None,
    host_interaction_context: HostInteractionContext | None = None,
) -> Any:
    """
    High Level Purpose:
        In circumstances like lower-layer replay or reconstruction flows that must finish shaping a `SystemState` before execution, helps with constructing one controller instance through the narrow runtime facade without importing `main.py` directly.

    Reference to Theory:
        Supports six-layer extraction by letting lower layers keep controller bootstrap on the runtime facade while still managing state assembly locally.

    Example Input Output:
        Input: `new_runtime_controller(state=SystemState.bootstrap('What is force?'), llm_policy='off')`
        Output: BSSCController(...)

    Args:
        state: Value for `state` used by `new_runtime_controller`. Expected type: `SystemState`.
        llm_policy: Value for `llm_policy` used by `new_runtime_controller`. Expected type: `str`. Defaults to `'off'`.

    Returns:
        Any: Result produced by `new_runtime_controller`.
    """
    from realized_core_engine.controller_runtime import BSSCController

    if subject_scope is not None:
        if subject_scope_root_path is None:
            raise ValueError("subject_scope_root_path is required when subject_scope is provided.")
        seed_runtime_controller_subject_scope(
            state,
            subject_scope_root_path=subject_scope_root_path,
            subject_scope=subject_scope,
        )
    return BSSCController(
        state,
        llm_policy=llm_policy,
        host_interaction_context=host_interaction_context,
    )
