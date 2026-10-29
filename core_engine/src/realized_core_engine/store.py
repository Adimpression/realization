# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sqlite3
import time
from collections import OrderedDict
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Iterable

from realized_core_semantics.applied_model import Artifact, BoundaryShapeTerm, NotDegreeKind, enum_text as enum_text_runtime, json_safe
from realized_core_engine.artifact_semantics import (
    ARTIFACT_DETAIL_SCALAR_FIELDS,
    ARTIFACT_DETAIL_YAML_FIELDS,
    artifact_boundary_shape_projection as artifact_boundary_shape_projection_runtime,
    artifact_build_from_normalized as artifact_build_from_normalized_runtime,
    artifact_compatibility_payload as artifact_compatibility_payload_runtime,
    artifact_contract_rows as artifact_contract_rows_runtime,
    artifact_list_item_rows as artifact_list_item_rows_runtime,
    artifact_normalized_projection as artifact_normalized_projection_runtime,
    artifact_notation_projection as artifact_notation_projection_runtime,
    artifact_structured_learning_from_content as artifact_structured_learning_from_content_runtime,
    artifact_with_id as artifact_with_id_runtime,
    notation_item_rows as notation_item_rows_runtime,
    yaml_dump_storage as yaml_dump_storage_runtime,
    yaml_load_storage as yaml_load_storage_runtime,
    yaml_string_list as yaml_string_list_runtime,
)
from realized_core_semantics.boundary import (
    boundary_shape_term_rows as boundary_shape_term_rows_runtime,
    infer_function_bit as infer_function_bit_runtime,
    is_template_bearing_artifact_type as is_template_bearing_artifact_type_runtime,
)
from realized_core_engine.non_achievedness_normalization import normalize_not_elaboration_payload
from realized_core_semantics.normalization import (
    normalize_boundary_shape,
    normalize_not_degree,
    normalize_not_misalignment_list,
    normalize_not_origin_list,
    normalize_remainder_shape_list,
)
from realized_core_semantics.semantic_text import (
    collapse_ws as collapse_ws_runtime,
    learning_core_tokens as learning_core_tokens_runtime,
    learning_lookup_keys as learning_lookup_keys_runtime,
    ordered_unique as ordered_unique_runtime,
    semantic_named_input_keys as semantic_named_input_keys_runtime,
    semantic_tokens as semantic_tokens_runtime,
    structured_text_list as structured_text_list_runtime,
    titleize_semantic_unit as titleize_semantic_unit_runtime,
)
from realized_core_engine.structured_learning import render_structured_learning_yaml as render_structured_learning_yaml_runtime


def _runtime_attr(name: str) -> Any:
    """Resolve a legacy private proxy through explicit owning modules."""
    helpers = {
        "artifact_boundary_shape_projection": artifact_boundary_shape_projection_runtime,
        "artifact_build_from_normalized": artifact_build_from_normalized_runtime,
        "artifact_compatibility_payload": artifact_compatibility_payload_runtime,
        "artifact_contract_rows": artifact_contract_rows_runtime,
        "artifact_list_item_rows": artifact_list_item_rows_runtime,
        "artifact_normalized_projection": artifact_normalized_projection_runtime,
        "artifact_notation_projection": artifact_notation_projection_runtime,
        "artifact_structured_learning_from_content": artifact_structured_learning_from_content_runtime,
        "artifact_with_id": artifact_with_id_runtime,
        "collapse_ws": collapse_ws_runtime,
        "enum_text": enum_text_runtime,
        "learning_core_tokens": learning_core_tokens_runtime,
        "learning_lookup_keys": learning_lookup_keys_runtime,
        "notation_item_rows": notation_item_rows_runtime,
        "ordered_unique": ordered_unique_runtime,
        "render_structured_learning_yaml": render_structured_learning_yaml_runtime,
        "semantic_named_input_keys": semantic_named_input_keys_runtime,
        "semantic_tokens": semantic_tokens_runtime,
        "structured_text_list": structured_text_list_runtime,
        "titleize_semantic_unit": titleize_semantic_unit_runtime,
        "yaml_dump_storage": yaml_dump_storage_runtime,
        "yaml_load_storage": yaml_load_storage_runtime,
        "yaml_string_list": yaml_string_list_runtime,
    }
    try:
        return helpers[name]
    except KeyError as exc:
        raise AttributeError(name) from exc


def _elapsed_seconds(start: float) -> float:
    return round(time.perf_counter() - start, 6)


def _payload_digest(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def _stable_payload_value(value: Any, *, parent_key: str = "") -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key)
            if parent_key == "skill_admission" and normalized_key == "evaluated_at":
                continue
            if parent_key == "skill_lifecycle" and normalized_key == "updated_at":
                continue
            if not parent_key and normalized_key == "created_at":
                continue
            normalized[normalized_key] = _stable_payload_value(item, parent_key=normalized_key)
        return normalized
    if isinstance(value, list):
        return [_stable_payload_value(item, parent_key=parent_key) for item in value]
    return value


def _payload_semantic_digest_json(payload_json: str) -> str:
    text = str(payload_json or "").strip()
    if not text:
        return _payload_digest("")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _payload_digest(text)
    stable_payload = _stable_payload_value(payload)
    return _payload_digest(json.dumps(stable_payload, sort_keys=True))


class _RuntimeProxy:
    def __init__(self, name: str) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with initializing the surrounding object with a usable starting state.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__init__(name='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            name: Value for `name` used by `__init__`. Expected type: `str`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.name = name

    def _value(self) -> Any:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling value.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_value()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            Any: Result produced by `_value`.
        """
        return _runtime_attr(self.name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling call.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__call__()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
            **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

        Returns:
            Any: Result produced by `__call__`.
        """
        return self._value()(*args, **kwargs)

    def __iter__(self):
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling iter.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__iter__()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
        """
        return iter(self._value())

    def __len__(self) -> int:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling len.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__len__()`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            int: Result produced by `__len__`.
        """
        return len(self._value())

    def __contains__(self, item: Any) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling contains.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__contains__(item=3)`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            item: Value for `item` used by `__contains__`. Expected type: `Any`.

        Returns:
            bool: Result produced by `__contains__`.
        """
        return item in self._value()

    def __getitem__(self, key: Any) -> Any:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling getitem.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__getitem__(key=3)`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            key: Value for `key` used by `__getitem__`. Expected type: `Any`.

        Returns:
            Any: Result produced by `__getitem__`.
        """
        return self._value()[key]

    def __bool__(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling bool.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__bool__()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `__bool__`.
        """
        return bool(self._value())

    def __str__(self) -> str:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling str.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__str__()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            str: Result produced by `__str__`.
        """
        return str(self._value())

    def __repr__(self) -> str:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling repr.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__repr__()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            str: Result produced by `__repr__`.
        """
        return repr(self._value())

    def __getattr__(self, attr: str) -> Any:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling getattr.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__getattr__(attr='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            attr: Value for `attr` used by `__getattr__`. Expected type: `str`.

        Returns:
            Any: Result produced by `__getattr__`.
        """
        return getattr(self._value(), attr)


def artifact_notation_projection(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact notation projection.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_notation_projection()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_notation_projection`.
    """
    return artifact_notation_projection_runtime(*args, **kwargs)


def artifact_with_id(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact with id.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_with_id()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_with_id`.
    """
    return artifact_with_id_runtime(*args, **kwargs)


def notation_item_rows(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling notation item rows.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `notation_item_rows()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `notation_item_rows`.
    """
    return notation_item_rows_runtime(*args, **kwargs)


def boundary_shape_term_rows(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling boundary shape term rows.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `boundary_shape_term_rows()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `boundary_shape_term_rows`.
    """
    return boundary_shape_term_rows_runtime(*args, **kwargs)


def artifact_list_item_rows(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact list item rows.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_list_item_rows()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_list_item_rows`.
    """
    return artifact_list_item_rows_runtime(*args, **kwargs)


def artifact_contract_rows(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact contract rows.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_contract_rows()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_contract_rows`.
    """
    return artifact_contract_rows_runtime(*args, **kwargs)


def artifact_normalized_projection(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact normalized projection.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_normalized_projection()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_normalized_projection`.
    """
    return artifact_normalized_projection_runtime(*args, **kwargs)


def yaml_load_storage(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling yaml load storage.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    return yaml_load_storage_runtime(*args, **kwargs)


def yaml_dump_storage(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling yaml dump storage.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    return yaml_dump_storage_runtime(*args, **kwargs)


def artifact_compatibility_payload(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with building payload data for artifact compatibility.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_compatibility_payload()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_compatibility_payload`.
    """
    return artifact_compatibility_payload_runtime(*args, **kwargs)


def learning_lookup_keys(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling learning lookup keys.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `learning_lookup_keys()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `learning_lookup_keys`.
    """
    return learning_lookup_keys_runtime(*args, **kwargs)


def semantic_named_input_keys(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling semantic named input keys.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `semantic_named_input_keys()`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `semantic_named_input_keys`.
    """
    return semantic_named_input_keys_runtime(*args, **kwargs)


def semantic_tokens(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling semantic tokens.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `semantic_tokens()`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `semantic_tokens`.
    """
    return semantic_tokens_runtime(*args, **kwargs)


def is_template_bearing_artifact_type(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with deciding whether template bearing artifact type.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `is_template_bearing_artifact_type()`
        Output: True

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `is_template_bearing_artifact_type`.
    """
    return is_template_bearing_artifact_type_runtime(*args, **kwargs)


def titleize_semantic_unit(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling titleize semantic unit.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `titleize_semantic_unit()`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `titleize_semantic_unit`.
    """
    return titleize_semantic_unit_runtime(*args, **kwargs)


def learning_core_tokens(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling learning core tokens.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `learning_core_tokens()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `learning_core_tokens`.
    """
    return learning_core_tokens_runtime(*args, **kwargs)


def render_structured_learning_yaml(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with rendering structured learning yaml.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    return render_structured_learning_yaml_runtime(*args, **kwargs)


def structured_text_list(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling structured text list.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `structured_text_list()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `structured_text_list`.
    """
    return structured_text_list_runtime(*args, **kwargs)


def ordered_unique(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ordered unique.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `ordered_unique()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `ordered_unique`.
    """
    return ordered_unique_runtime(*args, **kwargs)


def artifact_boundary_shape_projection(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact boundary shape projection.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_boundary_shape_projection()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_boundary_shape_projection`.
    """
    return artifact_boundary_shape_projection_runtime(*args, **kwargs)


def enum_text(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling enum text.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `enum_text()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `enum_text`.
    """
    return enum_text_runtime(*args, **kwargs)


def collapse_ws(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with collapsing ws.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `collapse_ws()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `collapse_ws`.
    """
    return collapse_ws_runtime(*args, **kwargs)


def yaml_string_list(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling yaml string list.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    return yaml_string_list_runtime(*args, **kwargs)


def infer_function_bit(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with inferring function bit.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

    Example Input Output:
        Input: `infer_function_bit()`
        Output: 'F = m * a'

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `infer_function_bit`.
    """
    return infer_function_bit_runtime(*args, **kwargs)


def artifact_structured_learning_from_content(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact structured learning from content.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_structured_learning_from_content()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_structured_learning_from_content`.
    """
    return artifact_structured_learning_from_content_runtime(*args, **kwargs)


def artifact_build_from_normalized(*args: Any, **kwargs: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact build from normalized.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_build_from_normalized()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        *args: Additional positional arguments forwarded by the caller. Expected type: `Any`.
        **kwargs: Additional keyword arguments forwarded by the caller. Expected type: `Any`.

    Returns:
        Any: Result produced by `artifact_build_from_normalized`.
    """
    return artifact_build_from_normalized_runtime(*args, **kwargs)


class ArtifactStore:
    ARTIFACT_KEY_UNIQUE_INDEX = "uq_bssc_artifacts_notation_key_normalized"
    ARTIFACT_NOTATION_KEY_UNIQUE_INDEX = "uq_bssc_artifacts_notation_key"

    def __init__(self) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with initializing the surrounding object with a usable starting state.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__init__()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.host = os.getenv("STATE_DB_URL", "localhost").strip() or "localhost"
        self.port = int(os.getenv("STATE_DB_PORT", "3306"))
        self.database = os.getenv("STATE_DB_NAME", "").strip()
        self.user = os.getenv("STATE_DB_USER", "").strip()
        self.password = os.getenv("STATE_DB_PASSWORD", "")
        self.backend_name, self.backend_module = self._detect_backend()

    def _detect_backend(self) -> tuple[str | None, Any | None]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling detect backend.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_detect_backend()`
            Output: ('Physics', 'Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            tuple[str | None, Any | None]: Result produced by `_detect_backend`.
        """
        for module_name in ("mysql.connector", "pymysql"):
            try:
                return module_name, importlib.import_module(module_name)
            except Exception:
                continue
        return None, None

    def configured(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling configured.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `configured()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `configured`.
        """
        return bool(self.host and self.database and self.user)

    def available(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling available.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `available()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `available`.
        """
        return self.configured() and self.backend_name is not None and self.backend_module is not None

    def describe(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling describe.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `describe()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `describe`.
        """
        return {
            "backend": self.backend_name,
            "configured": self.configured(),
            "host": self.host,
            "port": self.port,
            "database": self.database,
        }

    def _connect(self) -> Any:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling connect.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_connect()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            Any: Result produced by `_connect`.
        """
        if self.backend_name == "mysql.connector":
            return self.backend_module.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True,
            )
        if self.backend_name == "pymysql":
            return self.backend_module.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True,
            )
        raise RuntimeError("No supported SQL backend is available.")

    def _execute(self, connection: Any, sql: str, params: tuple[Any, ...] = ()) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling execute.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_execute(connection=3, sql='force', params=('Physics', 'Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_execute`. Expected type: `Any`.
            sql: Value for `sql` used by `_execute`. Expected type: `str`.
            params: Value for `params` used by `_execute`. Expected type: `tuple[Any, ...]`. Defaults to `()`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()

    def _column_exists(self, connection: Any, table_name: str, column_name: str) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling column exists.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_column_exists(connection=3, table_name='force', column_name='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_column_exists`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_column_exists`. Expected type: `str`.
            column_name: Value for `column_name` used by `_column_exists`. Expected type: `str`.

        Returns:
            bool: Result produced by `_column_exists`.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (column_name,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def _ensure_column(self, connection: Any, table_name: str, column_name: str, column_sql: str) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure column.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_column(connection=3, table_name='force', column_name='force', column_sql='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_column`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_ensure_column`. Expected type: `str`.
            column_name: Value for `column_name` used by `_ensure_column`. Expected type: `str`.
            column_sql: Value for `column_sql` used by `_ensure_column`. Expected type: `str`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self._column_exists(connection, table_name, column_name):
            return
        self._execute(connection, f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")

    def _index_exists(self, connection: Any, table_name: str, index_name: str) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling index exists.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_index_exists(connection=3, table_name='force', index_name='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_index_exists`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_index_exists`. Expected type: `str`.
            index_name: Value for `index_name` used by `_index_exists`. Expected type: `str`.

        Returns:
            bool: Result produced by `_index_exists`.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(f"SHOW INDEX FROM {table_name} WHERE Key_name = %s", (index_name,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def _ensure_unique_index(self, connection: Any, table_name: str, index_name: str, column_name: str) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure unique index.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_unique_index(connection=3, table_name='force', index_name='force', column_name='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_unique_index`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_ensure_unique_index`. Expected type: `str`.
            index_name: Value for `index_name` used by `_ensure_unique_index`. Expected type: `str`.
            column_name: Value for `column_name` used by `_ensure_unique_index`. Expected type: `str`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self._index_exists(connection, table_name, index_name):
            return
        self._execute(connection, f"ALTER TABLE {table_name} ADD UNIQUE KEY {index_name} ({column_name})")

    def _artifact_id_for_notation_key(self, connection: Any, normalized_key: str) -> str | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact id for notation key.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_artifact_id_for_notation_key(connection=3, normalized_key='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_artifact_id_for_notation_key`. Expected type: `Any`.
            normalized_key: Value for `normalized_key` used by `_artifact_id_for_notation_key`. Expected type: `str`.

        Returns:
            str | None: Result produced by `_artifact_id_for_notation_key`.
        """
        if not normalized_key:
            return None
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT artifact_id FROM bssc_artifacts WHERE notation_key_normalized = %s LIMIT 1",
                (normalized_key,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
        if not row:
            return None
        return str(row[0] if isinstance(row, (tuple, list)) else row)

    def _canonicalize_artifact_for_storage(
        self,
        connection: Any,
        artifact: Artifact,
        *,
        staged_notation_ids: Mapping[str, str] | None = None,
    ) -> Artifact:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with canonicalizing artifact for storage.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_canonicalize_artifact_for_storage(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_canonicalize_artifact_for_storage`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_canonicalize_artifact_for_storage`. Expected type: `Artifact`.

        Returns:
            Artifact: Result produced by `_canonicalize_artifact_for_storage`.
        """
        notation = artifact_notation_projection(artifact)
        normalized_key = notation["notation_key_normalized"]
        if staged_notation_ids:
            staged_existing_id = str(staged_notation_ids.get(normalized_key, "")).strip()
            if staged_existing_id:
                return artifact_with_id(artifact, staged_existing_id)
        existing_id = self._artifact_id_for_notation_key(connection, normalized_key)
        if existing_id:
            return artifact_with_id(artifact, existing_id)
        return artifact

    def _delete_search_rows_for_artifact(self, connection: Any, artifact_id: str) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling delete search rows for artifact.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_delete_search_rows_for_artifact(connection=3, artifact_id='artifact-force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_delete_search_rows_for_artifact`. Expected type: `Any`.
            artifact_id: Value for `artifact_id` used by `_delete_search_rows_for_artifact`. Expected type: `str`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if not artifact_id:
            return
        for table_name in ("bssc_artifact_search_units", "bssc_artifact_search_links"):
            if self._table_exists(connection, table_name):
                connection.execute(f"DELETE FROM {table_name} WHERE artifact_id = ?" if table_name == "bssc_artifact_search_units" else f"DELETE FROM {table_name} WHERE from_artifact_id = ? OR to_artifact_id = ?", (artifact_id,) if table_name == "bssc_artifact_search_units" else (artifact_id, artifact_id))
        if self._table_exists(connection, "bssc_artifact_search_fts"):
            connection.execute("DELETE FROM bssc_artifact_search_fts WHERE artifact_id = ?", (artifact_id,))
        for table_name in ("bssc_artifact_vec", *self.SEARCH_VECTOR_TABLES.values()):
            if self._table_exists(connection, table_name):
                connection.execute(f"DELETE FROM {table_name} WHERE artifact_id = ?", (artifact_id,))

    def _replace_notation_item_rows(self, connection: Any, notation: Mapping[str, Any]) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace notation item rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_replace_notation_item_rows(connection=3, notation={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_notation_item_rows`. Expected type: `Any`.
            notation: Value for `notation` used by `_replace_notation_item_rows`. Expected type: `Mapping[str, Any]`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        notation_key = str(notation.get("notation_key", "")).strip()
        if not notation_key:
            return
        self._execute(connection, "DELETE FROM bssc_artifact_in_items WHERE notation_key = %s", (notation_key,))
        self._execute(connection, "DELETE FROM bssc_artifact_out_items WHERE notation_key = %s", (notation_key,))
        for item_index, item_text, item_normalized in notation_item_rows(notation.get("notation_in_entries", [])):
            self._execute(
                connection,
                """
                INSERT INTO bssc_artifact_in_items (notation_key, item_index, item_text, item_normalized)
                VALUES (%s, %s, %s, %s)
                """,
                (notation_key, item_index, item_text, item_normalized),
            )
        for item_index, item_text, item_normalized in notation_item_rows(notation.get("notation_out_entries", [])):
            self._execute(
                connection,
                """
                INSERT INTO bssc_artifact_out_items (notation_key, item_index, item_text, item_normalized)
                VALUES (%s, %s, %s, %s)
                """,
                (notation_key, item_index, item_text, item_normalized),
            )

    def _replace_boundary_shape_term_rows(self, connection: Any, artifact: Artifact) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace boundary shape term rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_boundary_shape_term_rows(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_boundary_shape_term_rows`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_replace_boundary_shape_term_rows`. Expected type: `Artifact`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._execute(connection, "DELETE FROM bssc_artifact_boundary_shape_terms WHERE artifact_id = %s", (artifact.id,))
        for artifact_id, term_index, boundary_term in boundary_shape_term_rows(artifact.id, artifact.boundary_shape):
            self._execute(
                connection,
                """
                INSERT INTO bssc_artifact_boundary_shape_terms (artifact_id, term_index, boundary_term)
                VALUES (%s, %s, %s)
                """,
                (artifact_id, term_index, boundary_term),
            )

    def _replace_artifact_text_rows(self, connection: Any, table_name: str, artifact_id: str, items: Iterable[Any], *, column_name: str = "item_text") -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace artifact text rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_artifact_text_rows(connection=3, table_name='force', artifact_id='artifact-force', items=['mass', 'acceleration', 'force'])`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_artifact_text_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_replace_artifact_text_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_replace_artifact_text_rows`. Expected type: `str`.
            items: Value for `items` used by `_replace_artifact_text_rows`. Expected type: `Iterable[Any]`.
            column_name: Value for `column_name` used by `_replace_artifact_text_rows`. Expected type: `str`. Defaults to `'item_text'`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._execute(connection, f"DELETE FROM {table_name} WHERE artifact_id = %s", (artifact_id,))
        for item_index, item_text in artifact_list_item_rows(items):
            self._execute(
                connection,
                f"""
                INSERT INTO {table_name} (artifact_id, item_index, {column_name})
                VALUES (%s, %s, %s)
                """,
                (artifact_id, item_index, item_text),
            )

    def _replace_artifact_contract_rows(self, connection: Any, table_name: str, artifact_id: str, contract: Mapping[str, Any] | None) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace artifact contract rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_artifact_contract_rows(connection=3, table_name='force', artifact_id='artifact-force', contract={'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_artifact_contract_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_replace_artifact_contract_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_replace_artifact_contract_rows`. Expected type: `str`.
            contract: Value for `contract` used by `_replace_artifact_contract_rows`. Expected type: `Mapping[str, Any] | None`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._execute(connection, f"DELETE FROM {table_name} WHERE artifact_id = %s", (artifact_id,))
        for item_index, item_key, item_value_yaml in artifact_contract_rows(contract):
            self._execute(
                connection,
                f"""
                INSERT INTO {table_name} (artifact_id, item_index, item_key, item_value_yaml)
                VALUES (%s, %s, %s, %s)
                """,
                (artifact_id, item_index, item_key, item_value_yaml),
            )

    def _replace_artifact_normalized_rows(self, connection: Any, artifact: Artifact) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace artifact normalized rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_artifact_normalized_rows(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_artifact_normalized_rows`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_replace_artifact_normalized_rows`. Expected type: `Artifact`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        projection = artifact_normalized_projection(artifact)
        scalar_detail = projection["scalar_detail"]
        yaml_detail = projection["yaml_detail"]
        list_detail = projection["list_detail"]
        structured = projection["structured"]
        template = projection["template"]
        self._execute(connection, "DELETE FROM bssc_artifact_detail WHERE artifact_id = %s", (artifact.id,))
        self._execute(
            connection,
            """
            INSERT INTO bssc_artifact_detail (
                artifact_id, question, answer, source_path, source_document, entrypoint, script_language,
                python_script, input_form, output_form, affordance, relation_to_evidence,
                implementing_ability_artifact_id, output_field, compute_expression, validation_check,
                limits_yaml, parameter_aliases_yaml, default_invocation_payload_yaml, extra_content_yaml
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                artifact.id,
                scalar_detail.get("question", ""),
                scalar_detail.get("answer", ""),
                scalar_detail.get("source_path", ""),
                scalar_detail.get("source_document", ""),
                scalar_detail.get("entrypoint", ""),
                scalar_detail.get("script_language", ""),
                scalar_detail.get("python_script", ""),
                scalar_detail.get("input_form", ""),
                scalar_detail.get("output_form", ""),
                scalar_detail.get("affordance", ""),
                scalar_detail.get("relation_to_evidence", ""),
                scalar_detail.get("implementing_ability_artifact_id", ""),
                scalar_detail.get("output_field", ""),
                scalar_detail.get("compute_expression", ""),
                scalar_detail.get("validation_check", ""),
                yaml_detail.get("limits", ""),
                yaml_detail.get("parameter_aliases", ""),
                yaml_detail.get("default_invocation_payload", ""),
                projection["extra_content_yaml"],
            ),
        )
        self._replace_artifact_text_rows(connection, "bssc_artifact_provenance_items", artifact.id, artifact.provenance)
        self._replace_artifact_text_rows(connection, "bssc_artifact_related_items", artifact.id, artifact.related_artifact_ids, column_name="related_artifact_id")
        self._replace_artifact_text_rows(connection, "bssc_artifact_constraint_items", artifact.id, artifact.constraints, column_name="constraint_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_alias_items", artifact.id, list_detail.get("aliases", []), column_name="alias_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_dependency_items", artifact.id, list_detail.get("dependencies", []), column_name="dependency_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_lookup_key_items", artifact.id, structured.get("lookup_keys", []), column_name="lookup_key")
        self._replace_artifact_text_rows(connection, "bssc_artifact_component_not_items", artifact.id, structured.get("component_nots", []), column_name="component_not")
        self._replace_artifact_contract_rows(connection, "bssc_artifact_input_contract_items", artifact.id, projection["input_contract"])
        self._replace_artifact_contract_rows(connection, "bssc_artifact_output_contract_items", artifact.id, projection["output_contract"])
        self._execute(connection, "DELETE FROM bssc_artifact_template_schema WHERE artifact_id = %s", (artifact.id,))
        self._execute(
            connection,
            """
            INSERT INTO bssc_artifact_template_schema (
                artifact_id, governed_function, scope_of_reuse, bssc_awareness_yaml, holdon_awareness_yaml
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (
                artifact.id,
                template.get("governed_function", ""),
                template.get("scope_of_reuse", ""),
                template.get("bssc_awareness_yaml", ""),
                template.get("holdon_awareness_yaml", ""),
            ),
        )
        self._replace_artifact_text_rows(connection, "bssc_artifact_template_precondition_items", artifact.id, template.get("preconditions", []), column_name="condition_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_template_completion_items", artifact.id, template.get("completion_conditions", []), column_name="condition_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_template_failure_items", artifact.id, template.get("failure_conditions", []), column_name="condition_text")

    def _fetch_text_item_rows(self, connection: Any, table_name: str, artifact_id: str, *, column_name: str = "item_text") -> list[str]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch text item rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_fetch_text_item_rows(connection=3, table_name='force', artifact_id='artifact-force', column_name='force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_text_item_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_fetch_text_item_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_fetch_text_item_rows`. Expected type: `str`.
            column_name: Value for `column_name` used by `_fetch_text_item_rows`. Expected type: `str`. Defaults to `'item_text'`.

        Returns:
            list[str]: Result produced by `_fetch_text_item_rows`.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"SELECT {column_name} FROM {table_name} WHERE artifact_id = %s ORDER BY item_index ASC",
                (artifact_id,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        values: list[str] = []
        for row in rows:
            value = row[0] if isinstance(row, (tuple, list)) else row
            text = str(value or "").strip()
            if text:
                values.append(text)
        return values

    def _fetch_contract_rows(self, connection: Any, table_name: str, artifact_id: str) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch contract rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_fetch_contract_rows(connection=3, table_name='force', artifact_id='artifact-force')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_contract_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_fetch_contract_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_fetch_contract_rows`. Expected type: `str`.

        Returns:
            dict[str, Any]: Result produced by `_fetch_contract_rows`.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"SELECT item_key, item_value_yaml FROM {table_name} WHERE artifact_id = %s ORDER BY item_index ASC",
                (artifact_id,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        contract: dict[str, Any] = {}
        for row in rows:
            if not isinstance(row, (tuple, list)) or len(row) < 2:
                continue
            item_key = str(row[0] or "").strip()
            if not item_key:
                continue
            contract[item_key] = yaml_load_storage(row[1], default=str(row[1] or "").strip())
        return contract

    def _fetch_boundary_shape_terms(self, connection: Any, artifact_id: str, *, fallback_blob: str = "") -> tuple[BoundaryShapeTerm, ...]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch boundary shape terms.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_fetch_boundary_shape_terms(connection=3, artifact_id='artifact-force', fallback_blob='force')`
            Output: ('Physics', 'Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_boundary_shape_terms`. Expected type: `Any`.
            artifact_id: Value for `artifact_id` used by `_fetch_boundary_shape_terms`. Expected type: `str`.
            fallback_blob: Value for `fallback_blob` used by `_fetch_boundary_shape_terms`. Expected type: `str`. Defaults to `''`.

        Returns:
            tuple[BoundaryShapeTerm, ...]: Result produced by `_fetch_boundary_shape_terms`.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT boundary_term
                FROM bssc_artifact_boundary_shape_terms
                WHERE artifact_id = %s
                ORDER BY term_index ASC
                """,
                (artifact_id,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        if rows:
            return normalize_boundary_shape(
                [row[0] if isinstance(row, (tuple, list)) else row for row in rows],
                default=(BoundaryShapeTerm.OUTPUT_VALUE,),
            )
        if fallback_blob:
            return normalize_boundary_shape(
                [item.strip() for item in str(fallback_blob).split("|") if item.strip()],
                default=(BoundaryShapeTerm.OUTPUT_VALUE,),
            )
        return normalize_boundary_shape((BoundaryShapeTerm.OUTPUT_VALUE,), default=(BoundaryShapeTerm.OUTPUT_VALUE,))

    def _hydrate_artifact_from_row(self, connection: Any, row: Any) -> Artifact | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling hydrate artifact from row.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_hydrate_artifact_from_row(connection=3, row=3)`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_hydrate_artifact_from_row`. Expected type: `Any`.
            row: Value for `row` used by `_hydrate_artifact_from_row`. Expected type: `Any`.

        Returns:
            Artifact | None: Result produced by `_hydrate_artifact_from_row`.
        """
        artifact_id = str((row[0] if isinstance(row, (tuple, list)) else row.get("artifact_id")) or "").strip()
        payload_json = row[14] if isinstance(row, (tuple, list)) and len(row) > 14 else (row.get("payload_json") if isinstance(row, Mapping) else "")
        if not artifact_id:
            return None

        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT question, answer, source_path, source_document, entrypoint, script_language,
                       python_script, input_form, output_form, affordance, relation_to_evidence,
                       implementing_ability_artifact_id, output_field, compute_expression, validation_check,
                       limits_yaml, parameter_aliases_yaml, default_invocation_payload_yaml, extra_content_yaml
                FROM bssc_artifact_detail
                WHERE artifact_id = %s
                LIMIT 1
                """,
                (artifact_id,),
            )
            detail_row = cursor.fetchone()
            cursor.execute(
                """
                SELECT governed_function, scope_of_reuse, bssc_awareness_yaml, holdon_awareness_yaml
                FROM bssc_artifact_template_schema
                WHERE artifact_id = %s
                LIMIT 1
                """,
                (artifact_id,),
            )
            template_row = cursor.fetchone()
        finally:
            cursor.close()

        if detail_row is None and payload_json:
            try:
                return Artifact.from_dict(json.loads(payload_json))
            except Exception:
                return None

        content: dict[str, Any] = {}
        if isinstance(detail_row, (tuple, list)):
            detail_columns = (
                "question",
                "answer",
                "source_path",
                "source_document",
                "entrypoint",
                "script_language",
                "python_script",
                "input_form",
                "output_form",
                "affordance",
                "relation_to_evidence",
                "implementing_ability_artifact_id",
                "output_field",
                "compute_expression",
                "validation_check",
                "limits_yaml",
                "parameter_aliases_yaml",
                "default_invocation_payload_yaml",
                "extra_content_yaml",
            )
            detail = dict(zip(detail_columns, detail_row))
        elif isinstance(detail_row, Mapping):
            detail = dict(detail_row)
        else:
            detail = {}

        for key in ARTIFACT_DETAIL_SCALAR_FIELDS:
            value = str(detail.get(key, "") or "").strip()
            if value:
                content[key] = value
        for key in ARTIFACT_DETAIL_YAML_FIELDS:
            yaml_key = f"{key}_yaml"
            value = yaml_load_storage(detail.get(yaml_key, ""), default=None)
            if value not in (None, "", [], {}):
                content[key] = value
        extra_content = yaml_load_storage(detail.get("extra_content_yaml", ""), default={})
        structured_extras = {}
        if isinstance(extra_content, Mapping):
            for key, value in extra_content.items():
                if str(key) == "structured_learning_extras" and isinstance(value, Mapping):
                    structured_extras = {
                        str(extra_key): json_safe(extra_value)
                        for extra_key, extra_value in value.items()
                        if extra_value not in (None, "", [], {})
                    }
                    continue
                if key not in content and value not in (None, "", [], {}):
                    content[str(key)] = json_safe(value)

        aliases = self._fetch_text_item_rows(connection, "bssc_artifact_alias_items", artifact_id, column_name="alias_text")
        if aliases:
            content["aliases"] = aliases
        dependencies = self._fetch_text_item_rows(connection, "bssc_artifact_dependency_items", artifact_id, column_name="dependency_text")
        if dependencies:
            content["dependencies"] = dependencies
        input_contract = self._fetch_contract_rows(connection, "bssc_artifact_input_contract_items", artifact_id)
        if input_contract:
            content["input_contract"] = input_contract
        output_contract = self._fetch_contract_rows(connection, "bssc_artifact_output_contract_items", artifact_id)
        if output_contract:
            content["output_contract"] = output_contract

        encountered_not = str((row[11] if isinstance(row, (tuple, list)) else row.get("structured_encountered_not")) or "").strip()
        composed_not = str((row[12] if isinstance(row, (tuple, list)) else row.get("structured_composed_not")) or "").strip()
        lookup_keys = self._fetch_text_item_rows(connection, "bssc_artifact_lookup_key_items", artifact_id, column_name="lookup_key")
        component_nots = self._fetch_text_item_rows(connection, "bssc_artifact_component_not_items", artifact_id, column_name="component_not")
        if encountered_not or lookup_keys or component_nots or composed_not:
            semantic_unit = str(content.get("question", "")).strip() or str((row[5] if isinstance(row, (tuple, list)) else row.get("title")) or "").strip()
            content["structured_learning"] = {
                "encountered_not": encountered_not,
                "lookup_keys": lookup_keys,
                "component_nots": component_nots,
                "composed_not": composed_not,
                **structured_extras,
                "notation_yaml": render_structured_learning_yaml(
                    semantic_unit=semantic_unit or encountered_not or artifact_id,
                    encountered_not=encountered_not or titleize_semantic_unit(semantic_unit),
                    component_nots=component_nots,
                    composed_not=composed_not,
                    related_artifact_titles=[],
                    intended_object=collapse_ws(str(structured_extras.get("intended_object", "")).strip()),
                    success_criteria=structured_text_list(structured_extras.get("success_criteria", [])) if isinstance(structured_extras.get("success_criteria", []), list) else [],
                    actual_realization=collapse_ws(str(structured_extras.get("actual_realization", "")).strip()),
                    givens=structured_text_list(structured_extras.get("givens", [])) if isinstance(structured_extras.get("givens", []), list) else [],
                    unknowns=structured_text_list(structured_extras.get("unknowns", [])) if isinstance(structured_extras.get("unknowns", []), list) else [],
                    missing_components=structured_text_list(structured_extras.get("missing_components", [])) if isinstance(structured_extras.get("missing_components", []), list) else [],
                    distorted_components=structured_text_list(structured_extras.get("distorted_components", [])) if isinstance(structured_extras.get("distorted_components", []), list) else [],
                    differentiators=structured_text_list(structured_extras.get("differentiators", [])) if isinstance(structured_extras.get("differentiators", []), list) else [],
                    contrastive_cases=structured_text_list(structured_extras.get("contrastive_cases", [])) if isinstance(structured_extras.get("contrastive_cases", []), list) else [],
                    risk_of_wrong_closure=structured_text_list(structured_extras.get("risk_of_wrong_closure", [])) if isinstance(structured_extras.get("risk_of_wrong_closure", []), list) else [],
                    disallowed_assumptions=structured_text_list(structured_extras.get("disallowed_assumptions", [])) if isinstance(structured_extras.get("disallowed_assumptions", []), list) else [],
                    misalignment_types=normalize_not_misalignment_list(structured_extras.get("misalignment_types", [])),
                    origin_layers=normalize_not_origin_list(structured_extras.get("origin_layers", [])),
                    degree=normalize_not_degree(structured_extras.get("degree"), default=NotDegreeKind.PARTIAL),
                    remainder_shapes=normalize_remainder_shape_list(structured_extras.get("remainder_shapes", [])),
                    why_it_matters=structured_text_list(structured_extras.get("why_it_matters", [])) if isinstance(structured_extras.get("why_it_matters", []), list) else [],
                    minimal_repair=structured_text_list(structured_extras.get("minimal_repair", [])) if isinstance(structured_extras.get("minimal_repair", []), list) else [],
                    full_repair=structured_text_list(structured_extras.get("full_repair", [])) if isinstance(structured_extras.get("full_repair", []), list) else [],
                    action_posture=collapse_ws(str(structured_extras.get("action_posture", "")).strip()),
                ),
            }

        template_schema: dict[str, Any] = {}
        if isinstance(template_row, (tuple, list)):
            governed_function = str(template_row[0] or "").strip()
            scope_of_reuse = str(template_row[1] or "").strip()
            bssc_awareness = yaml_load_storage(template_row[2], default={})
            holdon_awareness = yaml_load_storage(template_row[3], default={})
        elif isinstance(template_row, Mapping):
            governed_function = str(template_row.get("governed_function", "") or "").strip()
            scope_of_reuse = str(template_row.get("scope_of_reuse", "") or "").strip()
            bssc_awareness = yaml_load_storage(template_row.get("bssc_awareness_yaml", ""), default={})
            holdon_awareness = yaml_load_storage(template_row.get("holdon_awareness_yaml", ""), default={})
        else:
            governed_function = ""
            scope_of_reuse = ""
            bssc_awareness = {}
            holdon_awareness = {}
        preconditions = self._fetch_text_item_rows(connection, "bssc_artifact_template_precondition_items", artifact_id, column_name="condition_text")
        completion_conditions = self._fetch_text_item_rows(connection, "bssc_artifact_template_completion_items", artifact_id, column_name="condition_text")
        failure_conditions = self._fetch_text_item_rows(connection, "bssc_artifact_template_failure_items", artifact_id, column_name="condition_text")
        if governed_function or scope_of_reuse or preconditions or completion_conditions or failure_conditions or bssc_awareness or holdon_awareness:
            template_schema = {
                "preconditions": preconditions,
                "governed_function": governed_function,
                "completion_conditions": completion_conditions,
                "failure_conditions": failure_conditions,
                "scope_of_reuse": scope_of_reuse,
                "bssc_awareness": bssc_awareness if isinstance(bssc_awareness, Mapping) else {},
                "holdon_awareness": holdon_awareness if isinstance(holdon_awareness, Mapping) else {},
            }

        provenance = self._fetch_text_item_rows(connection, "bssc_artifact_provenance_items", artifact_id)
        related_artifact_ids = self._fetch_text_item_rows(connection, "bssc_artifact_related_items", artifact_id, column_name="related_artifact_id")
        constraints = self._fetch_text_item_rows(connection, "bssc_artifact_constraint_items", artifact_id, column_name="constraint_text")
        boundary_shape = self._fetch_boundary_shape_terms(
            connection,
            artifact_id,
            fallback_blob=str((row[13] if isinstance(row, (tuple, list)) else row.get("boundary_shape_blob")) or ""),
        )

        return artifact_build_from_normalized(
            artifact_id=artifact_id,
            artifact_type=row[2] if isinstance(row, (tuple, list)) else row.get("artifact_type"),
            representation=row[3] if isinstance(row, (tuple, list)) else row.get("representation"),
            function_bit=row[4] if isinstance(row, (tuple, list)) else row.get("function_bit"),
            title=row[5] if isinstance(row, (tuple, list)) else row.get("title"),
            scope=row[6] if isinstance(row, (tuple, list)) else row.get("scope"),
            provenance=provenance,
            reusability=row[7] if isinstance(row, (tuple, list)) else row.get("reusability"),
            admissibility=row[8] if isinstance(row, (tuple, list)) else row.get("admissibility"),
            template_schema=template_schema,
            learning_relation=row[9] if isinstance(row, (tuple, list)) else row.get("learning_relation"),
            related_artifact_ids=related_artifact_ids,
            content=content,
            justification=row[10] if isinstance(row, (tuple, list)) else row.get("justification"),
            boundary_shape=boundary_shape,
            constraints=constraints,
            created_at=row[15] if isinstance(row, (tuple, list)) else row.get("created_at"),
        )

    def _backfill_notation_item_rows(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill notation item rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_backfill_notation_item_rows(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_notation_item_rows`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT payload_json
                FROM bssc_artifacts
                WHERE COALESCE(notation_key, '') <> ''
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

        for row in rows:
            payload_json = row[0] if isinstance(row, (tuple, list)) else row
            if not payload_json:
                continue
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
                notation = artifact_notation_projection(artifact)
            except Exception:
                continue
            self._replace_notation_item_rows(connection, notation)

    def _backfill_boundary_shape_term_rows(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill boundary shape term rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_boundary_shape_term_rows(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_boundary_shape_term_rows`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT payload_json
                FROM bssc_artifacts
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

        for row in rows:
            payload_json = row[0] if isinstance(row, (tuple, list)) else row
            if not payload_json:
                continue
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            self._replace_boundary_shape_term_rows(connection, artifact)

    def _ensure_notation_item_tables(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure notation item tables.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_notation_item_tables(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_notation_item_tables`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._ensure_unique_index(connection, "bssc_artifacts", self.ARTIFACT_NOTATION_KEY_UNIQUE_INDEX, "notation_key")
        self._execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_in_items (
                notation_key VARCHAR(255) NOT NULL,
                item_index INT NOT NULL,
                item_text TEXT NOT NULL,
                item_normalized VARCHAR(255) NOT NULL DEFAULT '',
                PRIMARY KEY (notation_key, item_index),
                KEY idx_bssc_artifact_in_items_item_normalized (item_normalized),
                CONSTRAINT fk_bssc_artifact_in_items_notation_key
                    FOREIGN KEY (notation_key) REFERENCES bssc_artifacts(notation_key)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """,
        )
        self._execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_out_items (
                notation_key VARCHAR(255) NOT NULL,
                item_index INT NOT NULL,
                item_text TEXT NOT NULL,
                item_normalized VARCHAR(255) NOT NULL DEFAULT '',
                PRIMARY KEY (notation_key, item_index),
                KEY idx_bssc_artifact_out_items_item_normalized (item_normalized),
                CONSTRAINT fk_bssc_artifact_out_items_notation_key
                    FOREIGN KEY (notation_key) REFERENCES bssc_artifacts(notation_key)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """,
        )
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM bssc_artifact_in_items")
            in_count_row = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM bssc_artifact_out_items")
            out_count_row = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM bssc_artifacts WHERE COALESCE(notation_key, '') <> ''")
            artifact_count_row = cursor.fetchone()
        finally:
            cursor.close()
        in_count = int(in_count_row[0] if isinstance(in_count_row, (tuple, list)) else 0)
        out_count = int(out_count_row[0] if isinstance(out_count_row, (tuple, list)) else 0)
        artifact_count = int(artifact_count_row[0] if isinstance(artifact_count_row, (tuple, list)) else 0)
        if artifact_count > 0 and in_count == 0 and out_count == 0:
            self._backfill_notation_item_rows(connection)

    def _ensure_boundary_shape_term_table(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure boundary shape term table.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_ensure_boundary_shape_term_table(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_boundary_shape_term_table`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_boundary_shape_terms (
                artifact_id VARCHAR(191) NOT NULL,
                term_index INT NOT NULL,
                boundary_term VARCHAR(16) NOT NULL,
                PRIMARY KEY (artifact_id, term_index),
                KEY idx_bssc_artifact_boundary_shape_terms_term (boundary_term),
                CONSTRAINT fk_bssc_artifact_boundary_shape_terms_artifact_id
                    FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """,
        )
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM bssc_artifact_boundary_shape_terms")
            row = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM bssc_artifacts")
            artifact_row = cursor.fetchone()
        finally:
            cursor.close()
        term_count = int(row[0] if isinstance(row, (tuple, list)) else 0)
        artifact_count = int(artifact_row[0] if isinstance(artifact_row, (tuple, list)) else 0)
        if artifact_count > 0 and term_count == 0:
            self._backfill_boundary_shape_term_rows(connection)

    def _ensure_artifact_normalized_tables(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure artifact normalized tables.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_ensure_artifact_normalized_tables(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_artifact_normalized_tables`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_detail (
                artifact_id VARCHAR(191) PRIMARY KEY,
                question TEXT NOT NULL,
                answer LONGTEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_document TEXT NOT NULL,
                entrypoint VARCHAR(191) NOT NULL,
                script_language VARCHAR(64) NOT NULL,
                python_script LONGTEXT NOT NULL,
                input_form TEXT NOT NULL,
                output_form TEXT NOT NULL,
                affordance TEXT NOT NULL,
                relation_to_evidence TEXT NOT NULL,
                implementing_ability_artifact_id VARCHAR(191) NOT NULL,
                output_field VARCHAR(191) NOT NULL,
                compute_expression LONGTEXT NOT NULL,
                validation_check TEXT NOT NULL,
                limits_yaml LONGTEXT NOT NULL,
                parameter_aliases_yaml LONGTEXT NOT NULL,
                default_invocation_payload_yaml LONGTEXT NOT NULL,
                extra_content_yaml LONGTEXT NOT NULL,
                CONSTRAINT fk_bssc_artifact_detail_artifact_id
                    FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """,
        )
        text_tables = (
            ("bssc_artifact_provenance_items", "item_text"),
            ("bssc_artifact_related_items", "related_artifact_id"),
            ("bssc_artifact_constraint_items", "constraint_text"),
            ("bssc_artifact_alias_items", "alias_text"),
            ("bssc_artifact_dependency_items", "dependency_text"),
            ("bssc_artifact_lookup_key_items", "lookup_key"),
            ("bssc_artifact_component_not_items", "component_not"),
            ("bssc_artifact_template_precondition_items", "condition_text"),
            ("bssc_artifact_template_completion_items", "condition_text"),
            ("bssc_artifact_template_failure_items", "condition_text"),
        )
        for table_name, column_name in text_tables:
            self._execute(
                connection,
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    artifact_id VARCHAR(191) NOT NULL,
                    item_index INT NOT NULL,
                    {column_name} TEXT NOT NULL,
                    PRIMARY KEY (artifact_id, item_index),
                    CONSTRAINT fk_{table_name}_artifact_id
                        FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
                """,
            )
        for table_name in ("bssc_artifact_input_contract_items", "bssc_artifact_output_contract_items"):
            self._execute(
                connection,
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    artifact_id VARCHAR(191) NOT NULL,
                    item_index INT NOT NULL,
                    item_key VARCHAR(191) NOT NULL,
                    item_value_yaml LONGTEXT NOT NULL,
                    PRIMARY KEY (artifact_id, item_index),
                    KEY idx_{table_name}_item_key (item_key),
                    CONSTRAINT fk_{table_name}_artifact_id
                        FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
                """,
            )
        self._execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_template_schema (
                artifact_id VARCHAR(191) PRIMARY KEY,
                governed_function TEXT NOT NULL,
                scope_of_reuse TEXT NOT NULL,
                bssc_awareness_yaml LONGTEXT NOT NULL,
                holdon_awareness_yaml LONGTEXT NOT NULL,
                CONSTRAINT fk_bssc_artifact_template_schema_artifact_id
                    FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """,
        )
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM bssc_artifact_detail")
            detail_row = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM bssc_artifacts")
            artifact_row = cursor.fetchone()
        finally:
            cursor.close()
        detail_count = int(detail_row[0] if isinstance(detail_row, (tuple, list)) else 0)
        artifact_count = int(artifact_row[0] if isinstance(artifact_row, (tuple, list)) else 0)
        if artifact_count > 0 and detail_count == 0:
            self._backfill_artifact_normalized_rows(connection)

    def _backfill_artifact_core_columns(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact core columns.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_core_columns(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_core_columns`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT artifact_id, payload_json
                FROM bssc_artifacts
                WHERE COALESCE(justification, '') = '' OR COALESCE(learning_relation, '') = ''
                LIMIT 512
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        for row in rows:
            artifact_id = row[0] if isinstance(row, (tuple, list)) else None
            payload_json = row[1] if isinstance(row, (tuple, list)) else None
            if not artifact_id or not payload_json:
                continue
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            self._execute(
                connection,
                """
                UPDATE bssc_artifacts
                SET justification = %s, learning_relation = %s
                WHERE artifact_id = %s
                """,
                (artifact.justification, artifact.learning_relation, artifact_id),
            )

    def _backfill_artifact_normalized_rows(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact normalized rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_normalized_rows(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_normalized_rows`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT artifact_id, payload_json
                FROM bssc_artifacts
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        for row in rows:
            artifact_id = row[0] if isinstance(row, (tuple, list)) else None
            payload_json = row[1] if isinstance(row, (tuple, list)) else None
            if not artifact_id or not payload_json:
                continue
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            self._replace_artifact_normalized_rows(connection, artifact)

    def _dedupe_artifact_keys(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling dedupe artifact keys.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_dedupe_artifact_keys(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_dedupe_artifact_keys`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT artifact_id, notation_key_normalized, created_at
                FROM bssc_artifacts
                WHERE COALESCE(notation_key_normalized, '') <> ''
                ORDER BY created_at DESC, artifact_id DESC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

        seen: set[str] = set()
        for row in rows:
            artifact_id = row[0] if isinstance(row, (tuple, list)) else None
            normalized_key = row[1] if isinstance(row, (tuple, list)) else None
            if not artifact_id or not normalized_key:
                continue
            normalized_key = str(normalized_key)
            if normalized_key in seen:
                self._execute(connection, "DELETE FROM bssc_artifacts WHERE artifact_id = %s", (artifact_id,))
                continue
            seen.add(normalized_key)

    def _backfill_artifact_learning_columns(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact learning columns.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_learning_columns(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_learning_columns`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT artifact_id, payload_json
                FROM bssc_artifacts
                WHERE
                    COALESCE(representation, '') = ''
                    OR COALESCE(structured_encountered_not, '') = ''
                    OR COALESCE(structured_lookup_blob, '') = ''
                    OR COALESCE(boundary_shape_blob, '') = ''
                    OR COALESCE(notation_key_normalized, '') = ''
                LIMIT 512
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

        for row in rows:
            artifact_id = row[0] if isinstance(row, (tuple, list)) else None
            payload_json = row[1] if isinstance(row, (tuple, list)) else None
            if not artifact_id or not payload_json:
                continue
            try:
                payload = json.loads(payload_json)
                artifact = Artifact.from_dict(payload)
                projection = self._artifact_learning_projection(artifact)
                notation = artifact_notation_projection(artifact)
            except Exception:
                continue
            self._execute(
                connection,
                """
                UPDATE bssc_artifacts
                SET
                    representation = %s,
                    structured_encountered_not = %s,
                    structured_lookup_blob = %s,
                    structured_composed_not = %s,
                    boundary_shape_blob = %s,
                    notation_key = %s,
                    notation_key_normalized = %s
                WHERE artifact_id = %s
                """,
                (
                    projection["representation"],
                    projection["structured_encountered_not"],
                    projection["structured_lookup_blob"],
                    projection["structured_composed_not"],
                    projection["boundary_shape_blob"],
                    notation["notation_key"],
                    notation["notation_key_normalized"],
                    artifact_id,
                ),
            )

    def _backfill_artifact_function_bits(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact function bits.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_function_bits(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_function_bits`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT artifact_id, payload_json, COALESCE(function_bit, 0)
                FROM bssc_artifacts
                LIMIT 2048
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()

        for row in rows:
            artifact_id = row[0] if isinstance(row, (tuple, list)) else None
            payload_json = row[1] if isinstance(row, (tuple, list)) else None
            stored_function_bit = row[2] if isinstance(row, (tuple, list)) else 0
            if not artifact_id or not payload_json:
                continue
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            function_bit = infer_function_bit(
                artifact_type=artifact.artifact_type,
                representation=artifact.representation,
                content=artifact.content,
                explicit=artifact.function_bit,
            )
            if int(stored_function_bit or 0) == function_bit:
                continue
            self._execute(
                connection,
                "UPDATE bssc_artifacts SET function_bit = %s WHERE artifact_id = %s",
                (function_bit, artifact_id),
            )

    def _artifact_learning_projection(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact learning projection.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_artifact_learning_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `_artifact_learning_projection`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `_artifact_learning_projection`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        structured = artifact_structured_learning_from_content(artifact)
        encountered_not = ""
        lookup_keys: list[str] = []
        component_nots: list[str] = []
        composed_not = ""

        if isinstance(structured, Mapping):
            encountered_not = str(structured.get("encountered_not", "")).strip()
            if isinstance(structured.get("lookup_keys", []), list):
                lookup_keys = [
                    str(item).strip().lower()
                    for item in structured.get("lookup_keys", [])
                    if str(item).strip()
                ]
            if isinstance(structured.get("component_nots", []), list):
                component_nots = [
                    str(item).strip()
                    for item in structured.get("component_nots", [])
                    if str(item).strip()
                ]
            composed_not = str(structured.get("composed_not", "")).strip()

        if not encountered_not:
            source_text = str(content.get("question", "")).strip() or artifact.title
            encountered_not = titleize_semantic_unit(" ".join(learning_core_tokens(source_text))) or titleize_semantic_unit(source_text)
        if not lookup_keys:
            source_text = str(content.get("question", "")).strip() or artifact.title
            lookup_keys = learning_lookup_keys(source_text)

        lookup_blob = " | ".join(ordered_unique([encountered_not.lower(), *lookup_keys, *(item.lower() for item in component_nots), composed_not.lower()]))
        return {
            "representation": artifact.representation,
            "structured_encountered_not": encountered_not,
            "structured_lookup_blob": lookup_blob,
            "structured_composed_not": composed_not,
            "boundary_shape_blob": artifact_boundary_shape_projection(artifact)["boundary_shape_blob"],
        }

    def _ensure_schema(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure schema.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_schema(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_schema`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self._execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS bssc_artifacts (
                artifact_id VARCHAR(191) PRIMARY KEY,
                run_id VARCHAR(191) NOT NULL,
                artifact_type VARCHAR(64) NOT NULL,
                representation VARCHAR(64) NOT NULL,
                function_bit TINYINT NOT NULL DEFAULT 0,
                title TEXT NOT NULL,
                notation_key VARCHAR(255) NOT NULL DEFAULT '',
                notation_key_normalized VARCHAR(255) NOT NULL DEFAULT '',
                scope TEXT NOT NULL,
                reusability VARCHAR(32) NOT NULL,
                admissibility VARCHAR(32) NOT NULL,
                learning_relation VARCHAR(64) NOT NULL DEFAULT 'new_family',
                justification LONGTEXT NOT NULL,
                structured_encountered_not VARCHAR(255) NOT NULL DEFAULT '',
                structured_lookup_blob LONGTEXT NOT NULL,
                structured_composed_not VARCHAR(255) NOT NULL DEFAULT '',
                boundary_shape_blob VARCHAR(255) NOT NULL DEFAULT '',
                payload_json LONGTEXT NOT NULL,
                created_at VARCHAR(64) NOT NULL
            )
            """,
        )
        self._ensure_column(connection, "bssc_artifacts", "representation", "VARCHAR(64) NOT NULL DEFAULT 'json'")
        self._ensure_column(connection, "bssc_artifacts", "function_bit", "TINYINT NOT NULL DEFAULT 0")
        self._ensure_column(connection, "bssc_artifacts", "notation_key", "VARCHAR(255) NOT NULL DEFAULT ''")
        self._ensure_column(connection, "bssc_artifacts", "notation_key_normalized", "VARCHAR(255) NOT NULL DEFAULT ''")
        self._ensure_column(connection, "bssc_artifacts", "learning_relation", "VARCHAR(64) NOT NULL DEFAULT 'new_family'")
        self._ensure_column(connection, "bssc_artifacts", "justification", "LONGTEXT NOT NULL")
        self._ensure_column(connection, "bssc_artifacts", "structured_encountered_not", "VARCHAR(255) NOT NULL DEFAULT ''")
        self._ensure_column(connection, "bssc_artifacts", "structured_lookup_blob", "LONGTEXT NOT NULL")
        self._ensure_column(connection, "bssc_artifacts", "structured_composed_not", "VARCHAR(255) NOT NULL DEFAULT ''")
        self._ensure_column(connection, "bssc_artifacts", "boundary_shape_blob", "VARCHAR(255) NOT NULL DEFAULT ''")
        self._backfill_artifact_core_columns(connection)
        self._backfill_artifact_learning_columns(connection)
        self._backfill_artifact_function_bits(connection)
        self._dedupe_artifact_keys(connection)
        self._ensure_unique_index(connection, "bssc_artifacts", self.ARTIFACT_KEY_UNIQUE_INDEX, "notation_key_normalized")
        self._ensure_notation_item_tables(connection)
        self._ensure_boundary_shape_term_table(connection)
        self._ensure_artifact_normalized_tables(connection)
        self._execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS bssc_discovery_audits (
                audit_id VARCHAR(191) PRIMARY KEY,
                run_id VARCHAR(191) NOT NULL,
                node_id VARCHAR(191) NOT NULL,
                pain_class VARCHAR(32) NOT NULL,
                gain_class VARCHAR(32) NOT NULL,
                payload_json LONGTEXT NOT NULL,
                created_at VARCHAR(64) NOT NULL
            )
            """,
        )

    def persist(self, state: SystemState) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling persist.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `persist(state=SystemState.bootstrap(prompt='Compute force from mass and acceleration.'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            state: Value for `state` used by `persist`. Expected type: `SystemState`.

        Returns:
            dict[str, Any]: Result produced by `persist`.
        """
        report = {
            "backend": self.backend_name,
            "configured": self.configured(),
            "database": self.database,
            "persisted_artifacts": 0,
            "persisted_discovery_audits": 0,
            "status": "skipped",
            "reason": "",
        }
        if not state.artifacts and not state.discovery_audits:
            report["reason"] = "nothing_to_persist"
            return report
        if not self.configured():
            report["reason"] = "missing_state_db_configuration"
            return report
        if self.backend_name is None or self.backend_module is None:
            report["reason"] = "no_supported_mysql_client"
            return report

        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            for artifact in state.artifacts.values():
                artifact = self._canonicalize_artifact_for_storage(connection, artifact)
                learning_projection = self._artifact_learning_projection(artifact)
                notation = artifact_notation_projection(artifact)
                self._execute(
                    connection,
                    """
                    INSERT INTO bssc_artifacts (
                        artifact_id, run_id, artifact_type, representation, function_bit, title, notation_key, notation_key_normalized,
                        scope, reusability, admissibility, learning_relation, justification,
                        structured_encountered_not, structured_lookup_blob,
                        structured_composed_not, boundary_shape_blob,
                        payload_json, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        artifact_type = VALUES(artifact_type),
                        representation = VALUES(representation),
                        function_bit = VALUES(function_bit),
                        title = VALUES(title),
                        notation_key = VALUES(notation_key),
                        notation_key_normalized = VALUES(notation_key_normalized),
                        scope = VALUES(scope),
                        reusability = VALUES(reusability),
                        admissibility = VALUES(admissibility),
                        learning_relation = VALUES(learning_relation),
                        justification = VALUES(justification),
                        structured_encountered_not = VALUES(structured_encountered_not),
                        structured_lookup_blob = VALUES(structured_lookup_blob),
                        structured_composed_not = VALUES(structured_composed_not),
                        boundary_shape_blob = VALUES(boundary_shape_blob),
                        payload_json = VALUES(payload_json),
                        created_at = VALUES(created_at)
                    """,
                    (
                        artifact.id,
                        state.run_id,
                        artifact.artifact_type,
                        learning_projection["representation"],
                        artifact.function_bit,
                        artifact.title,
                        notation["notation_key"],
                        notation["notation_key_normalized"],
                        artifact.scope,
                        artifact.reusability,
                        artifact.admissibility,
                        artifact.learning_relation,
                        artifact.justification,
                        learning_projection["structured_encountered_not"],
                        learning_projection["structured_lookup_blob"],
                        learning_projection["structured_composed_not"],
                        learning_projection["boundary_shape_blob"],
                        json.dumps(artifact_compatibility_payload(artifact), sort_keys=True),
                        artifact.created_at,
                    ),
                )
                self._replace_notation_item_rows(connection, notation)
                self._replace_boundary_shape_term_rows(connection, artifact)
                self._replace_artifact_normalized_rows(connection, artifact)
                report["persisted_artifacts"] += 1
            for audit in state.discovery_audits.values():
                self._execute(
                    connection,
                    """
                    INSERT INTO bssc_discovery_audits (
                        audit_id, run_id, node_id, pain_class, gain_class, payload_json, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        pain_class = VALUES(pain_class),
                        gain_class = VALUES(gain_class),
                        payload_json = VALUES(payload_json),
                        created_at = VALUES(created_at)
                    """,
                    (
                        audit.id,
                        state.run_id,
                        audit.node_id,
                        audit.pain_class,
                        audit.gain_class,
                        json.dumps(audit.to_dict(), sort_keys=True),
                        audit.created_at,
                    ),
                )
                report["persisted_discovery_audits"] += 1
            try:
                connection.commit()
            except Exception:
                pass
            report["status"] = "persisted"
            return report
        except Exception as exc:
            report["status"] = "error"
            report["reason"] = str(exc)
            return report
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    def persist_artifact(self, artifact: Artifact, *, run_id: str = "artifact_import") -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with persisting artifact.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `persist_artifact(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), run_id='artifact-force')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `persist_artifact`. Expected type: `Artifact`.
            run_id: Value for `run_id` used by `persist_artifact`. Expected type: `str`. Defaults to `'artifact_import'`.

        Returns:
            dict[str, Any]: Result produced by `persist_artifact`.
        """
        report = {
            "backend": self.backend_name,
            "configured": self.configured(),
            "database": self.database,
            "artifact_id": artifact.id,
            "persisted_artifacts": 0,
            "status": "skipped",
            "reason": "",
        }
        if not self.configured():
            report["reason"] = "missing_state_db_configuration"
            return report
        if self.backend_name is None or self.backend_module is None:
            report["reason"] = "no_supported_mysql_client"
            return report

        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            artifact = self._canonicalize_artifact_for_storage(connection, artifact)
            report["artifact_id"] = artifact.id
            learning_projection = self._artifact_learning_projection(artifact)
            notation = artifact_notation_projection(artifact)
            self._execute(
                connection,
                """
                INSERT INTO bssc_artifacts (
                    artifact_id, run_id, artifact_type, representation, function_bit, title, notation_key, notation_key_normalized,
                    scope, reusability, admissibility, learning_relation, justification,
                    structured_encountered_not, structured_lookup_blob,
                    structured_composed_not, boundary_shape_blob,
                    payload_json, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    artifact_type = VALUES(artifact_type),
                    representation = VALUES(representation),
                    function_bit = VALUES(function_bit),
                    title = VALUES(title),
                    notation_key = VALUES(notation_key),
                    notation_key_normalized = VALUES(notation_key_normalized),
                    scope = VALUES(scope),
                    reusability = VALUES(reusability),
                    admissibility = VALUES(admissibility),
                    learning_relation = VALUES(learning_relation),
                    justification = VALUES(justification),
                    structured_encountered_not = VALUES(structured_encountered_not),
                    structured_lookup_blob = VALUES(structured_lookup_blob),
                    structured_composed_not = VALUES(structured_composed_not),
                    boundary_shape_blob = VALUES(boundary_shape_blob),
                    payload_json = VALUES(payload_json),
                    created_at = VALUES(created_at)
                """,
                (
                    artifact.id,
                    run_id,
                    artifact.artifact_type,
                    learning_projection["representation"],
                    artifact.function_bit,
                    artifact.title,
                    notation["notation_key"],
                    notation["notation_key_normalized"],
                    artifact.scope,
                    artifact.reusability,
                    artifact.admissibility,
                    artifact.learning_relation,
                    artifact.justification,
                    learning_projection["structured_encountered_not"],
                    learning_projection["structured_lookup_blob"],
                    learning_projection["structured_composed_not"],
                    learning_projection["boundary_shape_blob"],
                    json.dumps(artifact_compatibility_payload(artifact), sort_keys=True),
                    artifact.created_at,
                ),
            )
            self._replace_notation_item_rows(connection, notation)
            self._replace_boundary_shape_term_rows(connection, artifact)
            self._replace_artifact_normalized_rows(connection, artifact)
            report["persisted_artifacts"] = 1
            report["status"] = "persisted"
            return report
        except Exception as exc:
            report["status"] = "error"
            report["reason"] = str(exc)
            return report
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    def persist_artifacts(self, artifacts: Iterable[Artifact], *, run_id: str = "artifact_import") -> dict[str, Any]:
        started_at = time.perf_counter()
        reports: list[dict[str, Any]] = []
        persisted_count = 0
        unchanged_count = 0
        error_count = 0
        for artifact in artifacts:
            report = self.persist_artifact(artifact, run_id=run_id)
            reports.append(report)
            status = str(report.get("status", "")).strip().lower()
            if status == "persisted":
                persisted_count += int(report.get("persisted_artifacts", 0) or 0)
            elif status == "unchanged":
                unchanged_count += 1
            elif status == "error":
                error_count += 1
        overall_status = "error" if error_count else "persisted"
        return {
            "backend": self.backend_name,
            "configured": self.configured(),
            "database": self.database,
            "status": overall_status,
            "persisted_artifacts": persisted_count,
            "unchanged_artifacts": unchanged_count,
            "error_artifacts": error_count,
            "reports": reports,
            "timings": {
                "total_seconds": _elapsed_seconds(started_at),
            },
        }

    def load_artifact_by_id(self, artifact_id: str) -> Artifact | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading artifact by id.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_artifact_by_id(artifact_id='artifact-force')`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact_id: Value for `artifact_id` used by `load_artifact_by_id`. Expected type: `str`.

        Returns:
            Artifact | None: Result produced by `load_artifact_by_id`.
        """
        if not artifact_id:
            return None
        if not self.configured() or self.backend_name is None or self.backend_module is None:
            return None

        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT
                        artifact_id, run_id, artifact_type, representation, function_bit, title,
                        scope, reusability, admissibility, learning_relation, justification,
                        structured_encountered_not, structured_composed_not, boundary_shape_blob,
                        payload_json, created_at
                    FROM bssc_artifacts
                    WHERE artifact_id = %s
                    LIMIT 1
                    """,
                    (artifact_id,),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
            if not row:
                return None
            return self._hydrate_artifact_from_row(connection, row)
        except Exception:
            return None
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    def load_all_artifacts(self) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading all artifacts.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_all_artifacts()`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            list[Artifact]: Result produced by `load_all_artifacts`.
        """
        if not self.configured() or self.backend_name is None or self.backend_module is None:
            return []

        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT
                        artifact_id, run_id, artifact_type, representation, function_bit, title,
                        scope, reusability, admissibility, learning_relation, justification,
                        structured_encountered_not, structured_composed_not, boundary_shape_blob,
                        payload_json, created_at
                    FROM bssc_artifacts
                    WHERE admissibility <> %s
                    ORDER BY created_at ASC
                    """,
                    ("rejected",),
                )
                rows = cursor.fetchall()
            finally:
                cursor.close()
            artifacts: list[Artifact] = []
            seen: set[str] = set()
            for row in rows:
                artifact = self._hydrate_artifact_from_row(connection, row)
                if artifact is None:
                    continue
                if artifact.id in seen:
                    continue
                seen.add(artifact.id)
                artifacts.append(artifact)
            return artifacts
        except Exception:
            return []
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    def load_relevant_artifacts(self, semantic_unit: str, *, limit: int = 8) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading relevant artifacts.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_relevant_artifacts(semantic_unit='Physics / Force / Force From Mass And Acceleration', limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_unit: Value for `semantic_unit` used by `load_relevant_artifacts`. Expected type: `str`.
            limit: Value for `limit` used by `load_relevant_artifacts`. Expected type: `int`. Defaults to `8`.

        Returns:
            list[Artifact]: Result produced by `load_relevant_artifacts`.
        """
        if not self.configured() or self.backend_name is None or self.backend_module is None:
            return []

        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            cursor = connection.cursor()
            try:
                query_keys = ordered_unique(learning_lookup_keys(semantic_unit))
                named_input_keys = semantic_named_input_keys(semantic_unit)
                input_contract_ids: list[str] = []
                if named_input_keys:
                    key_clauses = " OR ".join(
                        [
                            """
                            EXISTS (
                                SELECT 1
                                FROM bssc_artifact_in_items notation_in_item
                                WHERE notation_in_item.notation_key = bssc_artifacts.notation_key
                                  AND notation_in_item.item_normalized LIKE %s
                            )
                            """
                            for _ in named_input_keys
                        ]
                    )
                    cursor.execute(
                        f"""
                        SELECT artifact_id
                        FROM bssc_artifacts
                        WHERE admissibility <> %s AND ({key_clauses})
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        tuple(["rejected", *[f"{key}:%" for key in named_input_keys], max(32, limit * 8)]),
                    )
                    input_contract_ids.extend(
                        str(row[0] if isinstance(row, (tuple, list)) else row)
                        for row in cursor.fetchall()
                    )
                lookup_blob_clauses = " OR ".join(["LOWER(COALESCE(structured_lookup_blob, '')) LIKE %s" for _ in query_keys])
                encountered_clauses = " OR ".join(["LOWER(COALESCE(structured_encountered_not, '')) = %s" for _ in query_keys])
                notation_key_clauses = " OR ".join(["COALESCE(notation_key_normalized, '') = %s" for _ in query_keys])
                notation_in_item_clauses = " OR ".join(
                    [
                        """
                        EXISTS (
                            SELECT 1
                            FROM bssc_artifact_in_items notation_in_item
                            WHERE notation_in_item.notation_key = bssc_artifacts.notation_key
                              AND notation_in_item.item_normalized LIKE %s
                        )
                        """
                        for _ in query_keys
                    ]
                )
                notation_out_item_clauses = " OR ".join(
                    [
                        """
                        EXISTS (
                            SELECT 1
                            FROM bssc_artifact_out_items notation_out_item
                            WHERE notation_out_item.notation_key = bssc_artifacts.notation_key
                              AND notation_out_item.item_normalized LIKE %s
                        )
                        """
                        for _ in query_keys
                    ]
                )
                title_scope_parts: list[str] = []
                flattened_title_scope = []
                for key in query_keys[:2]:
                    title_scope_parts.extend(
                        ["LOWER(COALESCE(title, '')) LIKE %s", "LOWER(COALESCE(scope, '')) LIKE %s"]
                    )
                    flattened_title_scope.extend([f"%{key}%", f"%{key}%"])
                title_scope_clauses = " OR ".join(title_scope_parts)
                where_parts = ["admissibility <> %s"]
                params: list[Any] = ["rejected"]
                match_parts: list[str] = []
                if encountered_clauses:
                    match_parts.append(f"({encountered_clauses})")
                    params.extend(query_keys)
                if notation_key_clauses:
                    match_parts.append(f"({notation_key_clauses})")
                    params.extend(query_keys)
                if lookup_blob_clauses:
                    match_parts.append(f"({lookup_blob_clauses})")
                    params.extend([f"%{key}%" for key in query_keys])
                if notation_in_item_clauses:
                    match_parts.append(f"({notation_in_item_clauses})")
                    params.extend([f"%{key}%" for key in query_keys])
                if notation_out_item_clauses:
                    match_parts.append(f"({notation_out_item_clauses})")
                    params.extend([f"%{key}%" for key in query_keys])
                if title_scope_clauses:
                    match_parts.append(f"({title_scope_clauses})")
                    params.extend(flattened_title_scope)
                match_parts.append("(reusability = %s AND artifact_type <> %s)")
                params.extend(["broad_reuse", "knowledge"])
                where_parts.append("(" + " OR ".join(match_parts) + ")")
                cursor.execute(
                    f"""
                    SELECT
                        artifact_id, run_id, artifact_type, representation, function_bit, title,
                        scope, reusability, admissibility, learning_relation, justification,
                        structured_encountered_not, structured_composed_not, boundary_shape_blob,
                        payload_json, created_at
                    FROM bssc_artifacts
                    WHERE {' AND '.join(where_parts)}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    tuple(params + [max(64, limit * 12)]),
                )
                rows = cursor.fetchall()
            finally:
                cursor.close()
            query_tokens = semantic_tokens(semantic_unit)
            matched: list[Artifact] = []
            fallback_templates: list[Artifact] = []
            priority_ids = set(input_contract_ids)
            for row in rows:
                artifact = self._hydrate_artifact_from_row(connection, row)
                if artifact is None:
                    continue
                haystack = " ".join(
                    [
                        artifact.title,
                        artifact.scope,
                        artifact.artifact_type,
                        artifact.justification,
                        json.dumps(artifact.template_schema, sort_keys=True),
                        json.dumps(artifact.content, sort_keys=True)[:4000],
                    ]
                )
                if artifact.id in priority_ids:
                    matched.append(artifact)
                elif query_tokens and (semantic_tokens(haystack) & query_tokens):
                    matched.append(artifact)
                elif artifact.reusability == "broad_reuse" and is_template_bearing_artifact_type(artifact.artifact_type):
                    fallback_templates.append(artifact)
            ordered: list[Artifact] = []
            seen: set[str] = set()
            for artifact in matched + fallback_templates:
                if artifact.id in seen:
                    continue
                ordered.append(artifact)
                seen.add(artifact.id)
                if len(ordered) >= limit:
                    break
            return ordered
        except Exception:
            return []
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    def load_recent_artifacts(self, *, limit: int = 12) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading recent artifacts.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_recent_artifacts(limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            limit: Value for `limit` used by `load_recent_artifacts`. Expected type: `int`. Defaults to `12`.

        Returns:
            list[Artifact]: Result produced by `load_recent_artifacts`.
        """
        if not self.configured() or self.backend_name is None or self.backend_module is None:
            return []

        connection = None
        try:
            connection = self._connect()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT
                        artifact_id, run_id, artifact_type, representation, function_bit, title,
                        scope, reusability, admissibility, learning_relation, justification,
                        structured_encountered_not, structured_composed_not, boundary_shape_blob,
                        payload_json, created_at
                    FROM bssc_artifacts
                    WHERE admissibility <> %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    ("rejected", max(8, limit * 4)),
                )
                rows = cursor.fetchall()
            finally:
                cursor.close()

            ordered: list[Artifact] = []
            seen: set[str] = set()
            for row in rows:
                artifact = self._hydrate_artifact_from_row(connection, row)
                if artifact is None:
                    continue
                if artifact.id in seen:
                    continue
                ordered.append(artifact)
                seen.add(artifact.id)
                if len(ordered) >= limit:
                    break
            return ordered
        except Exception:
            return []
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass


class EmbeddingGemmaEncoder:
    MODEL_REPO = "onnx-community/embeddinggemma-300m-ONNX"
    MODEL_FILE = "onnx/model_q4.onnx"
    MODEL_DATA_FILE = "onnx/model_q4.onnx_data"
    TOKENIZER_FILE = "tokenizer.json"
    CONFIG_FILE = "config.json"
    VECTOR_DIMENSION = 768

    def __init__(self) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with initializing the surrounding object with a usable starting state.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__init__()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.model_repo = os.getenv("EMBEDDING_GEMMA_REPO", self.MODEL_REPO).strip() or self.MODEL_REPO
        default_dir = Path(".runtime_models") / "embeddinggemma-300m-onnx"
        self.model_dir = Path(os.getenv("EMBEDDING_GEMMA_MODEL_DIR", str(default_dir))).expanduser()
        self.max_length = int(os.getenv("EMBEDDING_GEMMA_MAX_LENGTH", "512"))
        self._numpy: Any | None = None
        self._onnxruntime: Any | None = None
        self._tokenizers: Any | None = None
        self._hf_hub: Any | None = None
        self._module_support_checked = False
        self._module_support_available = False
        self._runtime_modules_loaded = False
        self._session: Any | None = None
        self._tokenizer: Any | None = None
        self._encode_cache: OrderedDict[str, list[float]] = OrderedDict()
        self._cache_max_entries = max(int(os.getenv("EMBEDDING_GEMMA_CACHE_SIZE", "1024")), 0)

    def _import_optional(self, module_name: str) -> Any | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with importing an optional dependency without hard-failing the caller.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_import_optional(module_name='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            module_name: Value for `module_name` used by `_import_optional`. Expected type: `str`.

        Returns:
            Any | None: Result produced by `_import_optional`.
        """
        try:
            return importlib.import_module(module_name)
        except Exception:
            return None

    def available(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling available.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `available()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `available`.
        """
        if not self._module_support_checked:
            self._module_support_available = all(
                importlib.util.find_spec(module_name) is not None
                for module_name in ("numpy", "onnxruntime", "tokenizers")
            )
            self._module_support_checked = True
        return self._module_support_available

    def _ensure_runtime_modules(self) -> bool:
        """
        High Level Purpose:
            In circumstances like vector indexing and retrieval that only occasionally need the embedding runtime, helps with loading the heavy optional modules lazily instead of at store construction time.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_runtime_modules()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `_ensure_runtime_modules`.
        """
        if self._runtime_modules_loaded:
            return self._numpy is not None and self._onnxruntime is not None and self._tokenizers is not None
        if not self.available():
            self._runtime_modules_loaded = True
            return False
        self._numpy = self._import_optional("numpy")
        self._onnxruntime = self._import_optional("onnxruntime")
        self._tokenizers = self._import_optional("tokenizers")
        self._runtime_modules_loaded = True
        return self._numpy is not None and self._onnxruntime is not None and self._tokenizers is not None

    def describe(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling describe.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `describe()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `describe`.
        """
        return {
            "repo": self.model_repo,
            "model_dir": str(self.model_dir),
            "model_file": str(self.model_dir / self.MODEL_FILE),
            "tokenizer_file": str(self.model_dir / self.TOKENIZER_FILE),
            "available": self.available(),
            "dimension": self.VECTOR_DIMENSION,
        }

    def ensure_assets(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure assets.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `ensure_assets()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `ensure_assets`.
        """
        model_path = self.model_dir / self.MODEL_FILE
        model_data_path = self.model_dir / self.MODEL_DATA_FILE
        tokenizer_path = self.model_dir / self.TOKENIZER_FILE
        config_path = self.model_dir / self.CONFIG_FILE
        if model_path.exists() and model_data_path.exists() and tokenizer_path.exists() and config_path.exists():
            return True
        if self._hf_hub is None:
            self._hf_hub = self._import_optional("huggingface_hub")
        if self._hf_hub is None:
            return False
        self.model_dir.mkdir(parents=True, exist_ok=True)
        hf_hub_download = getattr(self._hf_hub, "hf_hub_download", None)
        if hf_hub_download is None:
            return False
        try:
            for relpath in (self.TOKENIZER_FILE, self.CONFIG_FILE, self.MODEL_FILE, self.MODEL_DATA_FILE):
                hf_hub_download(self.model_repo, relpath, local_dir=str(self.model_dir))
        except Exception:
            return False
        return model_path.exists() and model_data_path.exists() and tokenizer_path.exists()

    def _load(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling load.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_load()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `_load`.
        """
        if self._session is not None and self._tokenizer is not None:
            return True
        if not self._ensure_runtime_modules() or not self.ensure_assets():
            return False
        try:
            tokenizer_cls = getattr(self._tokenizers, "Tokenizer", None)
            if tokenizer_cls is None:
                return False
            self._tokenizer = tokenizer_cls.from_file(str(self.model_dir / self.TOKENIZER_FILE))
            self._session = self._onnxruntime.InferenceSession(
                str(self.model_dir / self.MODEL_FILE),
                providers=["CPUExecutionProvider"],
            )
            return True
        except Exception:
            self._session = None
            self._tokenizer = None
            return False

    def _remember_cached_encoding(self, text: str, vector: list[float]) -> None:
        if self._cache_max_entries <= 0:
            return
        self._encode_cache[text] = list(vector)
        self._encode_cache.move_to_end(text)
        while len(self._encode_cache) > self._cache_max_entries:
            self._encode_cache.popitem(last=False)

    def _encode_uncached(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        encodings = self._tokenizer.encode_batch(texts)
        max_len = min(
            max(len(encoding.ids) for encoding in encodings),
            self.max_length,
        )
        input_ids: list[list[int]] = []
        attention_mask: list[list[int]] = []
        for encoding in encodings:
            ids = list(encoding.ids[:max_len])
            mask = list(encoding.attention_mask[:max_len])
            pad_size = max_len - len(ids)
            if pad_size > 0:
                ids.extend([0] * pad_size)
                mask.extend([0] * pad_size)
            input_ids.append(ids)
            attention_mask.append(mask)
        np = self._numpy
        ort_inputs = {
            "input_ids": np.asarray(input_ids, dtype=np.int64),
            "attention_mask": np.asarray(attention_mask, dtype=np.int64),
        }
        try:
            outputs = self._session.run(["sentence_embedding"], ort_inputs)[0]
        except Exception:
            outputs = self._session.run(None, ort_inputs)[0]
        outputs = np.asarray(outputs, dtype=np.float32)
        norms = np.linalg.norm(outputs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = outputs / norms
        return normalized.tolist()

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling encode.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `encode(texts=['mass', 'acceleration', 'force'])`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            texts: Value for `texts` used by `encode`. Expected type: `list[str]`.

        Returns:
            list[list[float]]: Result produced by `encode`.
        """
        if not texts:
            return []
        if not self._load():
            return []
        cleaned = [str(text).strip() or " " for text in texts]
        cached_results: list[list[float] | None] = [None] * len(cleaned)
        missing_positions: dict[str, list[int]] = {}
        for index, text in enumerate(cleaned):
            cached = self._encode_cache.get(text)
            if cached is not None:
                self._encode_cache.move_to_end(text)
                cached_results[index] = list(cached)
                continue
            missing_positions.setdefault(text, []).append(index)
        if missing_positions:
            uncached_texts = list(missing_positions.keys())
            uncached_vectors = self._encode_uncached(uncached_texts)
            if len(uncached_vectors) != len(uncached_texts):
                return []
            for text, vector in zip(uncached_texts, uncached_vectors, strict=False):
                normalized_vector = [float(value) for value in vector]
                self._remember_cached_encoding(text, normalized_vector)
                for index in missing_positions[text]:
                    cached_results[index] = list(normalized_vector)
        return [list(vector or []) for vector in cached_results]

    def encode_one(self, text: str) -> list[float] | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling encode one.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `encode_one(text='Compute force from mass and acceleration.')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `encode_one`. Expected type: `str`.

        Returns:
            list[float] | None: Result produced by `encode_one`.
        """
        encoded = self.encode([text])
        return encoded[0] if encoded else None


class SQLiteVectorArtifactStore:
    ARTIFACT_KEY_UNIQUE_INDEX = "uq_bssc_artifacts_notation_key_normalized"
    ARTIFACT_NOTATION_KEY_UNIQUE_INDEX = "uq_bssc_artifacts_notation_key"
    SEARCH_VECTOR_TABLES = {
        "topic": "bssc_artifact_topic_vec",
        "failure": "bssc_artifact_failure_vec",
        "repair": "bssc_artifact_repair_vec",
    }
    SEARCH_EMBEDDING_VERSION = "embeddinggemma-300m-onnx-v1"
    SEARCH_EMBEDDING_MODEL = EmbeddingGemmaEncoder.MODEL_REPO

    def __init__(self, *, fallback_store: ArtifactStore | None = None) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with initializing the surrounding object with a usable starting state.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `__init__(fallback_store=ArtifactStore(host='localhost', port=3306, database='state'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            fallback_store: Value for `fallback_store` used by `__init__`. Expected type: `ArtifactStore | None`. Defaults to `None`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.fallback_store = fallback_store or ArtifactStore()
        self.sqlite3 = importlib.import_module("sqlite3")
        self._sqlite_vec: Any | None = None
        self._sqlite_vec_available: bool | None = None
        db_name = os.getenv("STATE_DB_NAME", "realization").strip() or "realization"
        default_path = Path("state") / f"{db_name}.sqlite3"
        self.sqlite_path = Path(os.getenv("STATE_SQLITE_PATH", str(default_path))).expanduser()
        self._encoder: EmbeddingGemmaEncoder | None = None
        self.vector_mode_override: str | None = None

    @property
    def sqlite_vec(self) -> Any:
        if self._sqlite_vec is None:
            self._sqlite_vec = importlib.import_module("sqlite_vec")
        return self._sqlite_vec

    @property
    def encoder(self) -> EmbeddingGemmaEncoder:
        if self._encoder is None:
            self._encoder = EmbeddingGemmaEncoder()
        return self._encoder

    @encoder.setter
    def encoder(self, value: EmbeddingGemmaEncoder) -> None:
        self._encoder = value

    def configured(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling configured.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `configured()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `configured`.
        """
        return True

    def available(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling available.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `available()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `available`.
        """
        return self.sqlite3 is not None

    def describe(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling describe.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `describe()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `describe`.
        """
        vector_enabled = self.vector_enabled()
        if vector_enabled:
            embedding_model = self.encoder.describe()
        else:
            default_dir = Path(".runtime_models") / "embeddinggemma-300m-onnx"
            model_repo = os.getenv("EMBEDDING_GEMMA_REPO", EmbeddingGemmaEncoder.MODEL_REPO).strip() or EmbeddingGemmaEncoder.MODEL_REPO
            model_dir = Path(os.getenv("EMBEDDING_GEMMA_MODEL_DIR", str(default_dir))).expanduser()
            embedding_model = {
                "repo": model_repo,
                "model_dir": str(model_dir),
                "model_file": str(model_dir / EmbeddingGemmaEncoder.MODEL_FILE),
                "tokenizer_file": str(model_dir / EmbeddingGemmaEncoder.TOKENIZER_FILE),
                "available": False,
                "dimension": EmbeddingGemmaEncoder.VECTOR_DIMENSION,
                "reason": "vector_disabled",
            }
        return {
            "backend": "sqlite_vec",
            "configured": True,
            "path": str(self.sqlite_path),
            "vector_enabled": vector_enabled,
            "embedding_model": embedding_model,
            "fallback_backend": self.fallback_store.describe(),
        }

    def vector_enabled(self) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling vector enabled.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `vector_enabled()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `vector_enabled`.
        """
        mode = str(self.vector_mode_override if self.vector_mode_override is not None else os.getenv("STATE_VECTOR_MODE", "")).strip().lower()
        if mode in {"0", "off", "false", "disabled", "none"}:
            return False
        return self.encoder.available()

    def vector_schema_enabled(self) -> bool:
        mode = str(self.vector_mode_override if self.vector_mode_override is not None else os.getenv("STATE_VECTOR_MODE", "")).strip().lower()
        if mode in {"0", "off", "false", "disabled", "none"}:
            return False
        if self._sqlite_vec_available is not None:
            return self._sqlite_vec_available
        try:
            _ = self.sqlite_vec
        except Exception:
            self._sqlite_vec_available = False
        else:
            self._sqlite_vec_available = True
        return self._sqlite_vec_available

    def _connect(self) -> Any:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling connect.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_connect()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            Any: Result produced by `_connect`.
        """
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = self.sqlite3.connect(str(self.sqlite_path))
        try:
            connection.row_factory = self.sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            if self.vector_schema_enabled():
                connection.enable_load_extension(True)
                self.sqlite_vec.load(connection)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            return connection
        except Exception:
            connection.close()
            raise

    def _artifact_learning_projection(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact learning projection.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_artifact_learning_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `_artifact_learning_projection`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `_artifact_learning_projection`.
        """
        return self.fallback_store._artifact_learning_projection(artifact)

    def _artifact_text_surface(self, artifact: Artifact, projection: Mapping[str, Any]) -> str:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact text surface.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_artifact_text_surface(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), projection={'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']})`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `_artifact_text_surface`. Expected type: `Artifact`.
            projection: Value for `projection` used by `_artifact_text_surface`. Expected type: `Mapping[str, Any]`.

        Returns:
            str: Result produced by `_artifact_text_surface`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        notation = artifact_notation_projection(artifact)
        structured = artifact_structured_learning_from_content(artifact)
        boundary_projection = artifact_boundary_shape_projection(artifact)
        parts = [
            artifact.title,
            str(notation.get("notation_key", "")).strip(),
            " ".join(notation.get("notation_in_entries", [])),
            " ".join(notation.get("notation_out_entries", [])),
            " ".join(boundary_projection.get("boundary_shape_entries", [])),
            artifact.scope,
            artifact.artifact_type,
            artifact.justification,
            str(content.get("question", "")).strip(),
            str(content.get("answer", "")).strip(),
            str(projection.get("structured_encountered_not", "")).strip(),
            " ".join(yaml_string_list(structured.get("lookup_keys", []))),
            " ".join(yaml_string_list(structured.get("component_nots", []))),
            str(projection.get("structured_composed_not", "")).strip(),
            str(structured.get("notation_yaml", "")).strip(),
        ]
        return "\n".join(part for part in parts if part).strip()

    def _compact_search_text(self, values: Iterable[Any], *, limit: int = 12) -> str:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling compact search text.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_compact_search_text(values=[3, 4, 12], limit=3)`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            values: Value for `values` used by `_compact_search_text`. Expected type: `Iterable[Any]`.
            limit: Value for `limit` used by `_compact_search_text`. Expected type: `int`. Defaults to `12`.

        Returns:
            str: Result produced by `_compact_search_text`.
        """
        parts: list[str] = []
        for value in values:
            text = collapse_ws(str(value).strip())
            if text:
                parts.append(text)
        return " ; ".join(ordered_unique(parts)[:limit]).strip()

    def _artifact_search_projection(self, artifact: Artifact, projection: Mapping[str, Any]) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact search projection.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_artifact_search_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), projection={'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']})`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `_artifact_search_projection`. Expected type: `Artifact`.
            projection: Value for `projection` used by `_artifact_search_projection`. Expected type: `Mapping[str, Any]`.

        Returns:
            dict[str, Any]: Result produced by `_artifact_search_projection`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        notation = artifact_notation_projection(artifact)
        boundary_projection = artifact_boundary_shape_projection(artifact)
        structured_payload = artifact_structured_learning_from_content(artifact)
        semantic_unit = str(content.get("question", "")).strip() or artifact.title
        structured = normalize_not_elaboration_payload(
            semantic_unit,
            structured_payload if isinstance(structured_payload, Mapping) else None,
            boundary_shape=artifact.boundary_shape,
            related_artifact_titles=[artifact.title],
        )
        aliases = [str(item).strip() for item in content.get("aliases", []) if str(item).strip()] if isinstance(content.get("aliases", []), list) else []
        input_contract = content.get("input_contract", {}) if isinstance(content.get("input_contract", {}), Mapping) else {}
        output_contract = content.get("output_contract", {}) if isinstance(content.get("output_contract", {}), Mapping) else {}
        input_keys = [str(key).strip() for key in input_contract.keys() if str(key).strip()]
        output_keys = [str(key).strip() for key in output_contract.keys() if str(key).strip()]
        question = str(content.get("question", "")).strip()
        answer = str(content.get("answer", "")).strip()
        boundary_terms = list(boundary_projection.get("boundary_shape_entries", []))
        encountered_not = str(structured.get("encountered_not", "")).strip() or str(projection.get("structured_encountered_not", "")).strip()
        composed_not = str(structured.get("composed_not", "")).strip() or str(projection.get("structured_composed_not", "")).strip()
        action_posture = collapse_ws(str(structured.get("action_posture", "")).strip())
        unit_type = (
            "function_template"
            if int(artifact.function_bit) == 1
            else ("template_artifact" if is_template_bearing_artifact_type(artifact.artifact_type) else "artifact_value")
        )
        layer_values = [str(item).strip() for item in structured.get("misalignment_types", []) if str(item).strip()]
        origin_values = [str(item).strip() for item in structured.get("origin_layers", []) if str(item).strip()]
        degree_value = str(structured.get("degree", "")).strip() or NotDegreeKind.PARTIAL.value
        domain_value = (
            titleize_semantic_unit(composed_not)
            or titleize_semantic_unit(artifact.scope)
            or titleize_semantic_unit(artifact.title)
            or str(artifact.artifact_type)
        )
        canonical_text = self._compact_search_text(
            [
                artifact.title,
                question,
                answer,
                *aliases,
                artifact.scope,
                artifact.justification,
                encountered_not,
            ],
            limit=14,
        )
        failure_signature = self._compact_search_text(
            [
                encountered_not,
                *structured.get("unknowns", []),
                *structured.get("missing_components", []),
                *structured.get("distorted_components", []),
                *structured.get("differentiators", []),
                *structured.get("risk_of_wrong_closure", []),
                *layer_values,
                *origin_values,
                degree_value,
                action_posture,
                "boundary " + " ".join(boundary_terms) if boundary_terms else "",
            ],
            limit=18,
        )
        repair_operator = self._compact_search_text(
            [
                *structured.get("minimal_repair", []),
                *structured.get("success_criteria", []),
                *structured.get("full_repair", [])[:3],
                *input_keys,
                *output_keys,
                str(content.get("validation_check", "")).strip(),
                "invoke executable template" if int(artifact.function_bit) == 1 else "",
                action_posture,
            ],
            limit=18,
        )
        applicability = self._compact_search_text(
            [
                *structured.get("givens", []),
                *structured.get("contrastive_cases", []),
                *structured.get("lookup_keys", []),
                *notation.get("notation_in_entries", []),
                *notation.get("notation_out_entries", []),
                *input_keys,
                *output_keys,
                "boundary " + " ".join(boundary_terms) if boundary_terms else "",
                question,
                artifact.scope,
            ],
            limit=20,
        )
        exclusions = self._compact_search_text(
            [
                *structured.get("disallowed_assumptions", []),
                *structured.get("contrastive_cases", []),
                *structured.get("risk_of_wrong_closure", []),
                *artifact.constraints,
            ],
            limit=16,
        )
        topic_text = self._compact_search_text(
            [
                artifact.title,
                question,
                encountered_not,
                composed_not,
                *aliases,
                *structured.get("lookup_keys", []),
            ],
            limit=20,
        )
        return {
            "artifact_id": artifact.id,
            "domain": domain_value or str(artifact.artifact_type),
            "topic": topic_text or canonical_text,
            "unit_type": unit_type,
            "layer": ",".join(layer_values[:2]) or "completion",
            "cause": ",".join(origin_values[:2]) or "",
            "severity": degree_value,
            "artifact_type": str(artifact.artifact_type),
            "function_bit": int(artifact.function_bit),
            "canonical_text": canonical_text or artifact.title,
            "failure_signature": failure_signature or encountered_not or artifact.title,
            "repair_operator": repair_operator or canonical_text or artifact.title,
            "applicability": applicability or canonical_text or artifact.title,
            "exclusions": exclusions,
            "source_prompt_archetype": self._compact_search_text([encountered_not, action_posture, artifact.artifact_type], limit=4),
            "embedding_model": os.getenv("EMBEDDING_GEMMA_REPO", self.SEARCH_EMBEDDING_MODEL).strip() or self.SEARCH_EMBEDDING_MODEL,
            "embedding_version": self.SEARCH_EMBEDDING_VERSION,
            "boundary_shape_blob": " | ".join(boundary_terms),
            "action_posture": action_posture,
            "updated_at": artifact.created_at,
            "topic_text": topic_text or canonical_text or artifact.title,
            "failure_text": failure_signature or canonical_text or artifact.title,
            "repair_text": repair_operator or canonical_text or artifact.title,
        }

    def _column_exists(self, connection: Any, table_name: str, column_name: str) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling column exists.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_column_exists(connection=3, table_name='force', column_name='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_column_exists`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_column_exists`. Expected type: `str`.
            column_name: Value for `column_name` used by `_column_exists`. Expected type: `str`.

        Returns:
            bool: Result produced by `_column_exists`.
        """
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return any(str(row["name"]) == column_name for row in rows)

    def _ensure_column(self, connection: Any, table_name: str, column_name: str, column_sql: str) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure column.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_column(connection=3, table_name='force', column_name='force', column_sql='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_column`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_ensure_column`. Expected type: `str`.
            column_name: Value for `column_name` used by `_ensure_column`. Expected type: `str`.
            column_sql: Value for `column_sql` used by `_ensure_column`. Expected type: `str`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self._column_exists(connection, table_name, column_name):
            return
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")

    def _index_exists(self, connection: Any, index_name: str) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling index exists.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_index_exists(connection=3, index_name='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_index_exists`. Expected type: `Any`.
            index_name: Value for `index_name` used by `_index_exists`. Expected type: `str`.

        Returns:
            bool: Result produced by `_index_exists`.
        """
        rows = connection.execute("PRAGMA index_list(bssc_artifacts)").fetchall()
        return any(str(row["name"]) == index_name for row in rows)

    def _table_exists(self, connection: Any, table_name: str) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling table exists.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_table_exists(connection=3, table_name='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_table_exists`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_table_exists`. Expected type: `str`.

        Returns:
            bool: Result produced by `_table_exists`.
        """
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ? LIMIT 1",
            (table_name,),
        ).fetchone()
        return row is not None

    def _backfill_artifact_notation_columns(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact notation columns.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_notation_columns(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_notation_columns`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT artifact_id, payload_json
            FROM bssc_artifacts
            WHERE
                COALESCE(notation_key_normalized, '') = ''
            LIMIT 512
            """
        ).fetchall()
        for row in rows:
            artifact_id = str(row["artifact_id"])
            payload_json = str(row["payload_json"])
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
                notation = artifact_notation_projection(artifact)
            except Exception:
                continue
            connection.execute(
                """
                UPDATE bssc_artifacts
                SET
                    notation_key = ?,
                    notation_key_normalized = ?
                WHERE artifact_id = ?
                """,
                (
                    notation["notation_key"],
                    notation["notation_key_normalized"],
                    artifact_id,
                ),
            )

    def _backfill_artifact_function_bits(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact function bits.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_function_bits(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_function_bits`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT artifact_id, payload_json, COALESCE(function_bit, 0) AS function_bit
            FROM bssc_artifacts
            """
        ).fetchall()
        for row in rows:
            artifact_id = str(row["artifact_id"])
            payload_json = str(row["payload_json"])
            stored_function_bit = int(row["function_bit"])
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            function_bit = infer_function_bit(
                artifact_type=artifact.artifact_type,
                representation=artifact.representation,
                content=artifact.content,
                explicit=artifact.function_bit,
            )
            if stored_function_bit == function_bit:
                continue
            connection.execute(
                "UPDATE bssc_artifacts SET function_bit = ? WHERE artifact_id = ?",
                (function_bit, artifact_id),
            )

    def _backfill_artifact_boundary_shape_columns(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact boundary shape columns.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_boundary_shape_columns(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_boundary_shape_columns`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT artifact_id, payload_json
            FROM bssc_artifacts
            WHERE COALESCE(boundary_shape_blob, '') = ''
            LIMIT 512
            """
        ).fetchall()
        for row in rows:
            artifact_id = str(row["artifact_id"])
            payload_json = str(row["payload_json"])
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            projection = artifact_boundary_shape_projection(artifact)
            connection.execute(
                "UPDATE bssc_artifacts SET boundary_shape_blob = ? WHERE artifact_id = ?",
                (projection["boundary_shape_blob"], artifact_id),
            )

    def _replace_notation_item_rows(self, connection: Any, notation: Mapping[str, Any]) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace notation item rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_replace_notation_item_rows(connection=3, notation={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_notation_item_rows`. Expected type: `Any`.
            notation: Value for `notation` used by `_replace_notation_item_rows`. Expected type: `Mapping[str, Any]`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        notation_key = str(notation.get("notation_key", "")).strip()
        if not notation_key:
            return
        connection.execute("DELETE FROM bssc_artifact_in_items WHERE notation_key = ?", (notation_key,))
        connection.execute("DELETE FROM bssc_artifact_out_items WHERE notation_key = ?", (notation_key,))
        for item_index, item_text, item_normalized in notation_item_rows(notation.get("notation_in_entries", [])):
            connection.execute(
                """
                INSERT INTO bssc_artifact_in_items (notation_key, item_index, item_text, item_normalized)
                VALUES (?, ?, ?, ?)
                """,
                (notation_key, item_index, item_text, item_normalized),
            )
        for item_index, item_text, item_normalized in notation_item_rows(notation.get("notation_out_entries", [])):
            connection.execute(
                """
                INSERT INTO bssc_artifact_out_items (notation_key, item_index, item_text, item_normalized)
                VALUES (?, ?, ?, ?)
                """,
                (notation_key, item_index, item_text, item_normalized),
            )

    def _replace_boundary_shape_term_rows(self, connection: Any, artifact: Artifact) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace boundary shape term rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_boundary_shape_term_rows(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_boundary_shape_term_rows`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_replace_boundary_shape_term_rows`. Expected type: `Artifact`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection.execute("DELETE FROM bssc_artifact_boundary_shape_terms WHERE artifact_id = ?", (artifact.id,))
        for artifact_id, term_index, boundary_term in boundary_shape_term_rows(artifact.id, artifact.boundary_shape):
            connection.execute(
                """
                INSERT INTO bssc_artifact_boundary_shape_terms (artifact_id, term_index, boundary_term)
                VALUES (?, ?, ?)
                """,
                (artifact_id, term_index, boundary_term),
            )

    def _replace_artifact_text_rows(self, connection: Any, table_name: str, artifact_id: str, items: Iterable[Any], *, column_name: str = "item_text") -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace artifact text rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_artifact_text_rows(connection=3, table_name='force', artifact_id='artifact-force', items=['mass', 'acceleration', 'force'])`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_artifact_text_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_replace_artifact_text_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_replace_artifact_text_rows`. Expected type: `str`.
            items: Value for `items` used by `_replace_artifact_text_rows`. Expected type: `Iterable[Any]`.
            column_name: Value for `column_name` used by `_replace_artifact_text_rows`. Expected type: `str`. Defaults to `'item_text'`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection.execute(f"DELETE FROM {table_name} WHERE artifact_id = ?", (artifact_id,))
        for item_index, item_text in artifact_list_item_rows(items):
            connection.execute(
                f"""
                INSERT INTO {table_name} (artifact_id, item_index, {column_name})
                VALUES (?, ?, ?)
                """,
                (artifact_id, item_index, item_text),
            )

    def _replace_artifact_contract_rows(self, connection: Any, table_name: str, artifact_id: str, contract: Mapping[str, Any] | None) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace artifact contract rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_artifact_contract_rows(connection=3, table_name='force', artifact_id='artifact-force', contract={'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_artifact_contract_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_replace_artifact_contract_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_replace_artifact_contract_rows`. Expected type: `str`.
            contract: Value for `contract` used by `_replace_artifact_contract_rows`. Expected type: `Mapping[str, Any] | None`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection.execute(f"DELETE FROM {table_name} WHERE artifact_id = ?", (artifact_id,))
        for item_index, item_key, item_value_yaml in artifact_contract_rows(contract):
            connection.execute(
                f"""
                INSERT INTO {table_name} (artifact_id, item_index, item_key, item_value_yaml)
                VALUES (?, ?, ?, ?)
                """,
                (artifact_id, item_index, item_key, item_value_yaml),
            )

    def _artifact_row_exists(self, connection: Any, artifact_id: str) -> bool:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact row exists.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_artifact_row_exists(connection=3, artifact_id='artifact-force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_artifact_row_exists`. Expected type: `Any`.
            artifact_id: Value for `artifact_id` used by `_artifact_row_exists`. Expected type: `str`.

        Returns:
            bool: Result produced by `_artifact_row_exists`.
        """
        artifact_id = str(artifact_id).strip()
        if not artifact_id:
            return False
        row = connection.execute(
            "SELECT 1 AS present FROM bssc_artifacts WHERE artifact_id = ? LIMIT 1",
            (artifact_id,),
        ).fetchone()
        return row is not None

    def _replace_artifact_normalized_rows(self, connection: Any, artifact: Artifact) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace artifact normalized rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_artifact_normalized_rows(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_artifact_normalized_rows`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_replace_artifact_normalized_rows`. Expected type: `Artifact`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        projection = artifact_normalized_projection(artifact)
        scalar_detail = projection["scalar_detail"]
        yaml_detail = projection["yaml_detail"]
        list_detail = projection["list_detail"]
        structured = projection["structured"]
        template = projection["template"]
        connection.execute("DELETE FROM bssc_artifact_detail WHERE artifact_id = ?", (artifact.id,))
        connection.execute(
            """
            INSERT INTO bssc_artifact_detail (
                artifact_id, question, answer, source_path, source_document, entrypoint, script_language,
                python_script, input_form, output_form, affordance, relation_to_evidence,
                implementing_ability_artifact_id, output_field, compute_expression, validation_check,
                limits_yaml, parameter_aliases_yaml, default_invocation_payload_yaml, extra_content_yaml
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact.id,
                scalar_detail.get("question", ""),
                scalar_detail.get("answer", ""),
                scalar_detail.get("source_path", ""),
                scalar_detail.get("source_document", ""),
                scalar_detail.get("entrypoint", ""),
                scalar_detail.get("script_language", ""),
                scalar_detail.get("python_script", ""),
                scalar_detail.get("input_form", ""),
                scalar_detail.get("output_form", ""),
                scalar_detail.get("affordance", ""),
                scalar_detail.get("relation_to_evidence", ""),
                scalar_detail.get("implementing_ability_artifact_id", ""),
                scalar_detail.get("output_field", ""),
                scalar_detail.get("compute_expression", ""),
                scalar_detail.get("validation_check", ""),
                yaml_detail.get("limits", ""),
                yaml_detail.get("parameter_aliases", ""),
                yaml_detail.get("default_invocation_payload", ""),
                projection["extra_content_yaml"],
            ),
        )
        self._replace_artifact_text_rows(connection, "bssc_artifact_provenance_items", artifact.id, artifact.provenance)
        self._replace_artifact_text_rows(connection, "bssc_artifact_related_items", artifact.id, artifact.related_artifact_ids, column_name="related_artifact_id")
        self._replace_artifact_text_rows(connection, "bssc_artifact_constraint_items", artifact.id, artifact.constraints, column_name="constraint_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_alias_items", artifact.id, list_detail.get("aliases", []), column_name="alias_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_dependency_items", artifact.id, list_detail.get("dependencies", []), column_name="dependency_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_lookup_key_items", artifact.id, structured.get("lookup_keys", []), column_name="lookup_key")
        self._replace_artifact_text_rows(connection, "bssc_artifact_component_not_items", artifact.id, structured.get("component_nots", []), column_name="component_not")
        self._replace_artifact_contract_rows(connection, "bssc_artifact_input_contract_items", artifact.id, projection["input_contract"])
        self._replace_artifact_contract_rows(connection, "bssc_artifact_output_contract_items", artifact.id, projection["output_contract"])
        connection.execute("DELETE FROM bssc_artifact_template_schema WHERE artifact_id = ?", (artifact.id,))
        connection.execute(
            """
            INSERT INTO bssc_artifact_template_schema (
                artifact_id, governed_function, scope_of_reuse, bssc_awareness_yaml, holdon_awareness_yaml
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                artifact.id,
                template.get("governed_function", ""),
                template.get("scope_of_reuse", ""),
                template.get("bssc_awareness_yaml", ""),
                template.get("holdon_awareness_yaml", ""),
            ),
        )
        self._replace_artifact_text_rows(connection, "bssc_artifact_template_precondition_items", artifact.id, template.get("preconditions", []), column_name="condition_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_template_completion_items", artifact.id, template.get("completion_conditions", []), column_name="condition_text")
        self._replace_artifact_text_rows(connection, "bssc_artifact_template_failure_items", artifact.id, template.get("failure_conditions", []), column_name="condition_text")

    def _fetch_text_item_rows(self, connection: Any, table_name: str, artifact_id: str, *, column_name: str = "item_text") -> list[str]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch text item rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_fetch_text_item_rows(connection=3, table_name='force', artifact_id='artifact-force', column_name='force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_text_item_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_fetch_text_item_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_fetch_text_item_rows`. Expected type: `str`.
            column_name: Value for `column_name` used by `_fetch_text_item_rows`. Expected type: `str`. Defaults to `'item_text'`.

        Returns:
            list[str]: Result produced by `_fetch_text_item_rows`.
        """
        rows = connection.execute(
            f"SELECT {column_name} FROM {table_name} WHERE artifact_id = ? ORDER BY item_index ASC",
            (artifact_id,),
        ).fetchall()
        values: list[str] = []
        for row in rows:
            text = str(row[column_name] if isinstance(row, Mapping) else row[0] or "").strip()
            if text:
                values.append(text)
        return values

    def _fetch_contract_rows(self, connection: Any, table_name: str, artifact_id: str) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch contract rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_fetch_contract_rows(connection=3, table_name='force', artifact_id='artifact-force')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_contract_rows`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_fetch_contract_rows`. Expected type: `str`.
            artifact_id: Value for `artifact_id` used by `_fetch_contract_rows`. Expected type: `str`.

        Returns:
            dict[str, Any]: Result produced by `_fetch_contract_rows`.
        """
        rows = connection.execute(
            f"SELECT item_key, item_value_yaml FROM {table_name} WHERE artifact_id = ? ORDER BY item_index ASC",
            (artifact_id,),
        ).fetchall()
        contract: dict[str, Any] = {}
        for row in rows:
            item_key = str(row["item_key"] if isinstance(row, Mapping) else row[0] or "").strip()
            if not item_key:
                continue
            raw_value = row["item_value_yaml"] if isinstance(row, Mapping) else row[1]
            contract[item_key] = yaml_load_storage(raw_value, default=str(raw_value or "").strip())
        return contract

    def _fetch_boundary_shape_terms(self, connection: Any, artifact_id: str, *, fallback_blob: str = "") -> tuple[BoundaryShapeTerm, ...]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch boundary shape terms.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_fetch_boundary_shape_terms(connection=3, artifact_id='artifact-force', fallback_blob='force')`
            Output: ('Physics', 'Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_boundary_shape_terms`. Expected type: `Any`.
            artifact_id: Value for `artifact_id` used by `_fetch_boundary_shape_terms`. Expected type: `str`.
            fallback_blob: Value for `fallback_blob` used by `_fetch_boundary_shape_terms`. Expected type: `str`. Defaults to `''`.

        Returns:
            tuple[BoundaryShapeTerm, ...]: Result produced by `_fetch_boundary_shape_terms`.
        """
        rows = connection.execute(
            """
            SELECT boundary_term
            FROM bssc_artifact_boundary_shape_terms
            WHERE artifact_id = ?
            ORDER BY term_index ASC
            """,
            (artifact_id,),
        ).fetchall()
        if rows:
            return normalize_boundary_shape(
                [row["boundary_term"] if isinstance(row, Mapping) else row[0] for row in rows],
                default=(BoundaryShapeTerm.OUTPUT_VALUE,),
            )
        if fallback_blob:
            return normalize_boundary_shape(
                [item.strip() for item in str(fallback_blob).split("|") if item.strip()],
                default=(BoundaryShapeTerm.OUTPUT_VALUE,),
            )
        return normalize_boundary_shape((BoundaryShapeTerm.OUTPUT_VALUE,), default=(BoundaryShapeTerm.OUTPUT_VALUE,))

    def _hydrate_artifact_from_row(self, connection: Any, row: Any) -> Artifact | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling hydrate artifact from row.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_hydrate_artifact_from_row(connection=3, row=3)`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_hydrate_artifact_from_row`. Expected type: `Any`.
            row: Value for `row` used by `_hydrate_artifact_from_row`. Expected type: `Any`.

        Returns:
            Artifact | None: Result produced by `_hydrate_artifact_from_row`.
        """
        artifact_id = str(row["artifact_id"] if isinstance(row, Mapping) else row[0] or "").strip()
        payload_json = row["payload_json"] if isinstance(row, Mapping) else row[14]
        if not artifact_id:
            return None
        detail_row = connection.execute(
            """
            SELECT question, answer, source_path, source_document, entrypoint, script_language,
                   python_script, input_form, output_form, affordance, relation_to_evidence,
                   implementing_ability_artifact_id, output_field, compute_expression, validation_check,
                   limits_yaml, parameter_aliases_yaml, default_invocation_payload_yaml, extra_content_yaml
            FROM bssc_artifact_detail
            WHERE artifact_id = ?
            LIMIT 1
            """,
            (artifact_id,),
        ).fetchone()
        template_row = connection.execute(
            """
            SELECT governed_function, scope_of_reuse, bssc_awareness_yaml, holdon_awareness_yaml
            FROM bssc_artifact_template_schema
            WHERE artifact_id = ?
            LIMIT 1
            """,
            (artifact_id,),
        ).fetchone()
        if detail_row is None and payload_json:
            try:
                return Artifact.from_dict(json.loads(str(payload_json)))
            except Exception:
                return None
        detail = dict(detail_row) if detail_row is not None else {}
        content: dict[str, Any] = {}
        for key in ARTIFACT_DETAIL_SCALAR_FIELDS:
            value = str(detail.get(key, "") or "").strip()
            if value:
                content[key] = value
        for key in ARTIFACT_DETAIL_YAML_FIELDS:
            value = yaml_load_storage(detail.get(f"{key}_yaml", ""), default=None)
            if value not in (None, "", [], {}):
                content[key] = value
        extra_content = yaml_load_storage(detail.get("extra_content_yaml", ""), default={})
        structured_extras = {}
        if isinstance(extra_content, Mapping):
            for key, value in extra_content.items():
                if str(key) == "structured_learning_extras" and isinstance(value, Mapping):
                    structured_extras = {
                        str(extra_key): json_safe(extra_value)
                        for extra_key, extra_value in value.items()
                        if extra_value not in (None, "", [], {})
                    }
                    continue
                if key not in content and value not in (None, "", [], {}):
                    content[str(key)] = json_safe(value)
        aliases = self._fetch_text_item_rows(connection, "bssc_artifact_alias_items", artifact_id, column_name="alias_text")
        if aliases:
            content["aliases"] = aliases
        dependencies = self._fetch_text_item_rows(connection, "bssc_artifact_dependency_items", artifact_id, column_name="dependency_text")
        if dependencies:
            content["dependencies"] = dependencies
        input_contract = self._fetch_contract_rows(connection, "bssc_artifact_input_contract_items", artifact_id)
        if input_contract:
            content["input_contract"] = input_contract
        output_contract = self._fetch_contract_rows(connection, "bssc_artifact_output_contract_items", artifact_id)
        if output_contract:
            content["output_contract"] = output_contract
        encountered_not = str(row["structured_encountered_not"] or "").strip()
        composed_not = str(row["structured_composed_not"] or "").strip()
        lookup_keys = self._fetch_text_item_rows(connection, "bssc_artifact_lookup_key_items", artifact_id, column_name="lookup_key")
        component_nots = self._fetch_text_item_rows(connection, "bssc_artifact_component_not_items", artifact_id, column_name="component_not")
        if encountered_not or lookup_keys or component_nots or composed_not:
            semantic_unit = str(content.get("question", "")).strip() or str(row["title"] or "").strip()
            content["structured_learning"] = {
                "encountered_not": encountered_not,
                "lookup_keys": lookup_keys,
                "component_nots": component_nots,
                "composed_not": composed_not,
                **structured_extras,
                "notation_yaml": render_structured_learning_yaml(
                    semantic_unit=semantic_unit or encountered_not or artifact_id,
                    encountered_not=encountered_not or titleize_semantic_unit(semantic_unit),
                    component_nots=component_nots,
                    composed_not=composed_not,
                    related_artifact_titles=[],
                    intended_object=collapse_ws(str(structured_extras.get("intended_object", "")).strip()),
                    success_criteria=structured_text_list(structured_extras.get("success_criteria", [])) if isinstance(structured_extras.get("success_criteria", []), list) else [],
                    actual_realization=collapse_ws(str(structured_extras.get("actual_realization", "")).strip()),
                    givens=structured_text_list(structured_extras.get("givens", [])) if isinstance(structured_extras.get("givens", []), list) else [],
                    unknowns=structured_text_list(structured_extras.get("unknowns", [])) if isinstance(structured_extras.get("unknowns", []), list) else [],
                    missing_components=structured_text_list(structured_extras.get("missing_components", [])) if isinstance(structured_extras.get("missing_components", []), list) else [],
                    distorted_components=structured_text_list(structured_extras.get("distorted_components", [])) if isinstance(structured_extras.get("distorted_components", []), list) else [],
                    differentiators=structured_text_list(structured_extras.get("differentiators", [])) if isinstance(structured_extras.get("differentiators", []), list) else [],
                    contrastive_cases=structured_text_list(structured_extras.get("contrastive_cases", [])) if isinstance(structured_extras.get("contrastive_cases", []), list) else [],
                    risk_of_wrong_closure=structured_text_list(structured_extras.get("risk_of_wrong_closure", [])) if isinstance(structured_extras.get("risk_of_wrong_closure", []), list) else [],
                    disallowed_assumptions=structured_text_list(structured_extras.get("disallowed_assumptions", [])) if isinstance(structured_extras.get("disallowed_assumptions", []), list) else [],
                    misalignment_types=normalize_not_misalignment_list(structured_extras.get("misalignment_types", [])),
                    origin_layers=normalize_not_origin_list(structured_extras.get("origin_layers", [])),
                    degree=normalize_not_degree(structured_extras.get("degree"), default=NotDegreeKind.PARTIAL),
                    remainder_shapes=normalize_remainder_shape_list(structured_extras.get("remainder_shapes", [])),
                    why_it_matters=structured_text_list(structured_extras.get("why_it_matters", [])) if isinstance(structured_extras.get("why_it_matters", []), list) else [],
                    minimal_repair=structured_text_list(structured_extras.get("minimal_repair", [])) if isinstance(structured_extras.get("minimal_repair", []), list) else [],
                    full_repair=structured_text_list(structured_extras.get("full_repair", [])) if isinstance(structured_extras.get("full_repair", []), list) else [],
                    action_posture=collapse_ws(str(structured_extras.get("action_posture", "")).strip()),
                ),
            }
        template_schema: dict[str, Any] = {}
        if template_row is not None:
            preconditions = self._fetch_text_item_rows(connection, "bssc_artifact_template_precondition_items", artifact_id, column_name="condition_text")
            completion_conditions = self._fetch_text_item_rows(connection, "bssc_artifact_template_completion_items", artifact_id, column_name="condition_text")
            failure_conditions = self._fetch_text_item_rows(connection, "bssc_artifact_template_failure_items", artifact_id, column_name="condition_text")
            governed_function = str(template_row["governed_function"] or "").strip()
            scope_of_reuse = str(template_row["scope_of_reuse"] or "").strip()
            bssc_awareness = yaml_load_storage(template_row["bssc_awareness_yaml"], default={})
            holdon_awareness = yaml_load_storage(template_row["holdon_awareness_yaml"], default={})
            if governed_function or scope_of_reuse or preconditions or completion_conditions or failure_conditions or bssc_awareness or holdon_awareness:
                template_schema = {
                    "preconditions": preconditions,
                    "governed_function": governed_function,
                    "completion_conditions": completion_conditions,
                    "failure_conditions": failure_conditions,
                    "scope_of_reuse": scope_of_reuse,
                    "bssc_awareness": bssc_awareness if isinstance(bssc_awareness, Mapping) else {},
                    "holdon_awareness": holdon_awareness if isinstance(holdon_awareness, Mapping) else {},
                }
        provenance = self._fetch_text_item_rows(connection, "bssc_artifact_provenance_items", artifact_id)
        related_artifact_ids = self._fetch_text_item_rows(connection, "bssc_artifact_related_items", artifact_id, column_name="related_artifact_id")
        constraints = self._fetch_text_item_rows(connection, "bssc_artifact_constraint_items", artifact_id, column_name="constraint_text")
        boundary_shape = self._fetch_boundary_shape_terms(connection, artifact_id, fallback_blob=str(row["boundary_shape_blob"] or ""))
        return artifact_build_from_normalized(
            artifact_id=artifact_id,
            artifact_type=row["artifact_type"],
            representation=row["representation"],
            function_bit=row["function_bit"],
            title=row["title"],
            scope=row["scope"],
            provenance=provenance,
            reusability=row["reusability"],
            admissibility=row["admissibility"],
            template_schema=template_schema,
            learning_relation=row["learning_relation"],
            related_artifact_ids=related_artifact_ids,
            content=content,
            justification=row["justification"],
            boundary_shape=boundary_shape,
            constraints=constraints,
            created_at=row["created_at"],
        )

    def _backfill_notation_item_rows(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill notation item rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_backfill_notation_item_rows(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_notation_item_rows`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT payload_json
            FROM bssc_artifacts
            WHERE COALESCE(notation_key, '') <> ''
            ORDER BY created_at ASC
            """
        ).fetchall()
        for row in rows:
            payload_json = str(row["payload_json"])
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
                notation = artifact_notation_projection(artifact)
            except Exception:
                continue
            self._replace_notation_item_rows(connection, notation)

    def _backfill_boundary_shape_term_rows(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill boundary shape term rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_boundary_shape_term_rows(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_boundary_shape_term_rows`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT payload_json
            FROM bssc_artifacts
            ORDER BY created_at ASC
            """
        ).fetchall()
        for row in rows:
            payload_json = str(row["payload_json"])
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            self._replace_boundary_shape_term_rows(connection, artifact)

    def _ensure_notation_item_tables(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure notation item tables.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_notation_item_tables(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_notation_item_tables`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if not self._index_exists(connection, self.ARTIFACT_NOTATION_KEY_UNIQUE_INDEX):
            connection.execute(
                f"CREATE UNIQUE INDEX {self.ARTIFACT_NOTATION_KEY_UNIQUE_INDEX} ON bssc_artifacts(notation_key)"
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_in_items (
                notation_key TEXT NOT NULL,
                item_index INTEGER NOT NULL,
                item_text TEXT NOT NULL,
                item_normalized TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (notation_key, item_index),
                FOREIGN KEY (notation_key) REFERENCES bssc_artifacts(notation_key)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_in_items_item_normalized ON bssc_artifact_in_items(item_normalized)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_out_items (
                notation_key TEXT NOT NULL,
                item_index INTEGER NOT NULL,
                item_text TEXT NOT NULL,
                item_normalized TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (notation_key, item_index),
                FOREIGN KEY (notation_key) REFERENCES bssc_artifacts(notation_key)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_out_items_item_normalized ON bssc_artifact_out_items(item_normalized)"
        )
        artifact_count = int(
            connection.execute(
                "SELECT COUNT(*) AS count_value FROM bssc_artifacts WHERE COALESCE(notation_key, '') <> ''"
            ).fetchone()["count_value"]
        )
        in_count = int(connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifact_in_items").fetchone()["count_value"])
        out_count = int(connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifact_out_items").fetchone()["count_value"])
        if artifact_count > 0 and in_count == 0 and out_count == 0:
            self._backfill_notation_item_rows(connection)

    def _ensure_boundary_shape_term_table(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure boundary shape term table.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_ensure_boundary_shape_term_table(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_boundary_shape_term_table`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_boundary_shape_terms (
                artifact_id TEXT NOT NULL,
                term_index INTEGER NOT NULL,
                boundary_term TEXT NOT NULL,
                PRIMARY KEY (artifact_id, term_index),
                FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_boundary_shape_terms_term ON bssc_artifact_boundary_shape_terms(boundary_term)"
        )
        artifact_count = int(
            connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifacts").fetchone()["count_value"]
        )
        term_count = int(
            connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifact_boundary_shape_terms").fetchone()["count_value"]
        )
        if artifact_count > 0 and term_count == 0:
            self._backfill_boundary_shape_term_rows(connection)

    def _ensure_artifact_normalized_tables(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure artifact normalized tables.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_ensure_artifact_normalized_tables(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_artifact_normalized_tables`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_detail (
                artifact_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_document TEXT NOT NULL,
                entrypoint TEXT NOT NULL,
                script_language TEXT NOT NULL,
                python_script TEXT NOT NULL,
                input_form TEXT NOT NULL,
                output_form TEXT NOT NULL,
                affordance TEXT NOT NULL,
                relation_to_evidence TEXT NOT NULL,
                implementing_ability_artifact_id TEXT NOT NULL,
                output_field TEXT NOT NULL,
                compute_expression TEXT NOT NULL,
                validation_check TEXT NOT NULL,
                limits_yaml TEXT NOT NULL,
                parameter_aliases_yaml TEXT NOT NULL,
                default_invocation_payload_yaml TEXT NOT NULL,
                extra_content_yaml TEXT NOT NULL,
                FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )
        text_tables = (
            ("bssc_artifact_provenance_items", "item_text"),
            ("bssc_artifact_related_items", "related_artifact_id"),
            ("bssc_artifact_constraint_items", "constraint_text"),
            ("bssc_artifact_alias_items", "alias_text"),
            ("bssc_artifact_dependency_items", "dependency_text"),
            ("bssc_artifact_lookup_key_items", "lookup_key"),
            ("bssc_artifact_component_not_items", "component_not"),
            ("bssc_artifact_template_precondition_items", "condition_text"),
            ("bssc_artifact_template_completion_items", "condition_text"),
            ("bssc_artifact_template_failure_items", "condition_text"),
        )
        for table_name, column_name in text_tables:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    artifact_id TEXT NOT NULL,
                    item_index INTEGER NOT NULL,
                    {column_name} TEXT NOT NULL,
                    PRIMARY KEY (artifact_id, item_index),
                    FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
                """
            )
        for table_name in ("bssc_artifact_input_contract_items", "bssc_artifact_output_contract_items"):
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    artifact_id TEXT NOT NULL,
                    item_index INTEGER NOT NULL,
                    item_key TEXT NOT NULL,
                    item_value_yaml TEXT NOT NULL,
                    PRIMARY KEY (artifact_id, item_index),
                    FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
                """
            )
            connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_item_key ON {table_name}(item_key)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_template_schema (
                artifact_id TEXT PRIMARY KEY,
                governed_function TEXT NOT NULL,
                scope_of_reuse TEXT NOT NULL,
                bssc_awareness_yaml TEXT NOT NULL,
                holdon_awareness_yaml TEXT NOT NULL,
                FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )
        artifact_count = int(connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifacts").fetchone()["count_value"])
        detail_count = int(connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifact_detail").fetchone()["count_value"])
        if artifact_count > 0 and detail_count == 0:
            self._backfill_artifact_normalized_rows(connection)

    def _replace_artifact_search_rows(self, connection: Any, artifact: Artifact, projection: Mapping[str, Any]) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling replace artifact search rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_replace_artifact_search_rows(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), projection={'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']})`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_replace_artifact_search_rows`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_replace_artifact_search_rows`. Expected type: `Artifact`.
            projection: Value for `projection` used by `_replace_artifact_search_rows`. Expected type: `Mapping[str, Any]`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        search_projection = self._artifact_search_projection(artifact, projection)
        self._replace_artifact_search_rows_precomputed(connection, artifact, search_projection)

    def _backfill_artifact_search_rows(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact search rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_search_rows(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_search_rows`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT
                artifact_id, run_id, artifact_type, representation, function_bit, title,
                scope, reusability, admissibility, learning_relation, justification,
                structured_encountered_not, structured_composed_not, boundary_shape_blob,
                payload_json, created_at
            FROM bssc_artifacts
            WHERE admissibility <> ?
            ORDER BY created_at ASC
            """,
            ("rejected",),
        ).fetchall()
        for row in rows:
            artifact = self._hydrate_artifact_from_row(connection, row)
            if artifact is None:
                continue
            projection = self._artifact_learning_projection(artifact)
            self._replace_artifact_search_rows(connection, artifact, projection)

    def _ensure_artifact_search_tables(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure artifact search tables.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_ensure_artifact_search_tables(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_artifact_search_tables`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_search_units (
                artifact_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                topic TEXT NOT NULL,
                unit_type TEXT NOT NULL,
                layer TEXT NOT NULL,
                cause TEXT NOT NULL,
                severity TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                function_bit INTEGER NOT NULL DEFAULT 0,
                canonical_text TEXT NOT NULL,
                failure_signature TEXT NOT NULL,
                repair_operator TEXT NOT NULL,
                applicability TEXT NOT NULL,
                exclusions TEXT NOT NULL,
                source_prompt_archetype TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                embedding_version TEXT NOT NULL,
                boundary_shape_blob TEXT NOT NULL DEFAULT '',
                action_posture TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                FOREIGN KEY (artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_search_units_type ON bssc_artifact_search_units(unit_type, artifact_type)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_search_units_layer ON bssc_artifact_search_units(layer)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_search_units_cause ON bssc_artifact_search_units(cause)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_search_units_severity ON bssc_artifact_search_units(severity)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_bssc_artifact_search_units_posture ON bssc_artifact_search_units(action_posture)"
        )
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS bssc_artifact_search_fts
            USING fts5(
                artifact_id UNINDEXED,
                canonical_text,
                failure_signature,
                repair_operator,
                applicability,
                exclusions,
                domain,
                layer,
                cause,
                severity,
                unit_type,
                artifact_type,
                tokenize='unicode61'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifact_search_links (
                from_artifact_id TEXT NOT NULL,
                to_artifact_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                PRIMARY KEY (from_artifact_id, to_artifact_id, relation_type),
                FOREIGN KEY (from_artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (to_artifact_id) REFERENCES bssc_artifacts(artifact_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )
        if self.vector_enabled():
            for table_name in self.SEARCH_VECTOR_TABLES.values():
                connection.execute(
                    f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS {table_name}
                    USING vec0(
                        artifact_id TEXT,
                        embedding FLOAT[{self.encoder.VECTOR_DIMENSION}]
                    )
                    """
                )
        artifact_count = int(connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifacts").fetchone()["count_value"])
        search_count = int(connection.execute("SELECT COUNT(*) AS count_value FROM bssc_artifact_search_units").fetchone()["count_value"])
        if artifact_count > 0 and search_count == 0:
            self._backfill_artifact_search_rows(connection)

    def _backfill_artifact_core_columns(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact core columns.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_core_columns(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_core_columns`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT artifact_id, payload_json
            FROM bssc_artifacts
            WHERE COALESCE(learning_relation, '') = '' OR COALESCE(justification, '') = ''
            LIMIT 512
            """
        ).fetchall()
        for row in rows:
            artifact_id = str(row["artifact_id"])
            payload_json = str(row["payload_json"])
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            connection.execute(
                "UPDATE bssc_artifacts SET learning_relation = ?, justification = ? WHERE artifact_id = ?",
                (artifact.learning_relation, artifact.justification, artifact_id),
            )

    def _backfill_artifact_normalized_rows(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling backfill artifact normalized rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_backfill_artifact_normalized_rows(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_backfill_artifact_normalized_rows`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT artifact_id, payload_json
            FROM bssc_artifacts
            ORDER BY created_at ASC
            """
        ).fetchall()
        for row in rows:
            artifact_id = str(row["artifact_id"])
            payload_json = str(row["payload_json"])
            if not artifact_id or not payload_json:
                continue
            try:
                artifact = Artifact.from_dict(json.loads(payload_json))
            except Exception:
                continue
            self._replace_artifact_normalized_rows(connection, artifact)

    def _dedupe_artifact_keys(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling dedupe artifact keys.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_dedupe_artifact_keys(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_dedupe_artifact_keys`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rows = connection.execute(
            """
            SELECT artifact_id, notation_key_normalized, created_at
            FROM bssc_artifacts
            WHERE COALESCE(notation_key_normalized, '') <> ''
            ORDER BY created_at DESC, artifact_id DESC
            """
        ).fetchall()
        seen: set[str] = set()
        for row in rows:
            artifact_id = str(row["artifact_id"])
            normalized_key = str(row["notation_key_normalized"])
            if normalized_key in seen:
                self._delete_search_rows_for_artifact(connection, artifact_id)
                connection.execute("DELETE FROM bssc_artifacts WHERE artifact_id = ?", (artifact_id,))
                continue
            seen.add(normalized_key)

    def _artifact_id_for_notation_key(self, connection: Any, normalized_key: str) -> str | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling artifact id for notation key.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_artifact_id_for_notation_key(connection=3, normalized_key='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_artifact_id_for_notation_key`. Expected type: `Any`.
            normalized_key: Value for `normalized_key` used by `_artifact_id_for_notation_key`. Expected type: `str`.

        Returns:
            str | None: Result produced by `_artifact_id_for_notation_key`.
        """
        if not normalized_key:
            return None
        row = connection.execute(
            "SELECT artifact_id FROM bssc_artifacts WHERE notation_key_normalized = ? LIMIT 1",
            (normalized_key,),
        ).fetchone()
        if row is None:
            return None
        return str(row["artifact_id"])

    def _canonicalize_artifact_for_storage(
        self,
        connection: Any,
        artifact: Artifact,
        *,
        staged_notation_ids: Mapping[str, str] | None = None,
    ) -> Artifact:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with canonicalizing artifact for storage.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_canonicalize_artifact_for_storage(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_canonicalize_artifact_for_storage`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_canonicalize_artifact_for_storage`. Expected type: `Artifact`.

        Returns:
            Artifact: Result produced by `_canonicalize_artifact_for_storage`.
        """
        notation = artifact_notation_projection(artifact)
        normalized_key = notation["notation_key_normalized"]
        if staged_notation_ids:
            staged_existing_id = str(staged_notation_ids.get(normalized_key, "")).strip()
            if staged_existing_id:
                return artifact_with_id(artifact, staged_existing_id)
        existing_id = self._artifact_id_for_notation_key(connection, normalized_key)
        if existing_id:
            return artifact_with_id(artifact, existing_id)
        return artifact

    def _ensure_schema(self, connection: Any) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling ensure schema.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_ensure_schema(connection=3)`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_ensure_schema`. Expected type: `Any`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_artifacts (
                artifact_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                representation TEXT NOT NULL,
                function_bit INTEGER NOT NULL DEFAULT 0,
                title TEXT NOT NULL,
                notation_key TEXT NOT NULL DEFAULT '',
                notation_key_normalized TEXT NOT NULL DEFAULT '',
                scope TEXT NOT NULL,
                reusability TEXT NOT NULL,
                admissibility TEXT NOT NULL,
                learning_relation TEXT NOT NULL DEFAULT 'new_family',
                justification TEXT NOT NULL,
                structured_encountered_not TEXT NOT NULL DEFAULT '',
                structured_lookup_blob TEXT NOT NULL,
                structured_composed_not TEXT NOT NULL DEFAULT '',
                boundary_shape_blob TEXT NOT NULL DEFAULT '',
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._ensure_column(connection, "bssc_artifacts", "notation_key", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(connection, "bssc_artifacts", "function_bit", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column(connection, "bssc_artifacts", "notation_key_normalized", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(connection, "bssc_artifacts", "boundary_shape_blob", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(connection, "bssc_artifacts", "learning_relation", "TEXT NOT NULL DEFAULT 'new_family'")
        self._ensure_column(connection, "bssc_artifacts", "justification", "TEXT NOT NULL DEFAULT ''")
        self._backfill_artifact_notation_columns(connection)
        self._backfill_artifact_core_columns(connection)
        self._backfill_artifact_function_bits(connection)
        self._backfill_artifact_boundary_shape_columns(connection)
        self._ensure_notation_item_tables(connection)
        self._ensure_boundary_shape_term_table(connection)
        self._ensure_artifact_normalized_tables(connection)
        self._ensure_artifact_search_tables(connection)
        self._dedupe_artifact_keys(connection)
        if not self._index_exists(connection, self.ARTIFACT_KEY_UNIQUE_INDEX):
            connection.execute(
                f"CREATE UNIQUE INDEX {self.ARTIFACT_KEY_UNIQUE_INDEX} ON bssc_artifacts(notation_key_normalized)"
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bssc_discovery_audits (
                audit_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                pain_class TEXT NOT NULL,
                gain_class TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        if self.vector_schema_enabled():
            connection.execute(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS bssc_artifact_vec
                USING vec0(
                    artifact_id TEXT,
                    embedding FLOAT[{EmbeddingGemmaEncoder.VECTOR_DIMENSION}]
                )
                """
            )

    def _artifact_payload_json(self, artifact: Artifact) -> str:
        return json.dumps(artifact_compatibility_payload(artifact), sort_keys=True)

    def _fetch_existing_payload_json_map(self, connection: Any, artifact_ids: list[str]) -> dict[str, str]:
        ordered_ids = [str(item).strip() for item in artifact_ids if str(item).strip()]
        if not ordered_ids:
            return {}
        existing: dict[str, str] = {}
        chunk_size = 250
        for start in range(0, len(ordered_ids), chunk_size):
            chunk = ordered_ids[start : start + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            rows = connection.execute(
                f"""
                SELECT artifact_id, payload_json
                FROM bssc_artifacts
                WHERE artifact_id IN ({placeholders})
                """,
                chunk,
            ).fetchall()
            for row in rows:
                artifact_id = str(row["artifact_id"] if isinstance(row, Mapping) else row[0] or "").strip()
                payload_json = str(row["payload_json"] if isinstance(row, Mapping) else row[1] or "")
                if artifact_id:
                    existing[artifact_id] = payload_json
        return existing

    def _upsert_artifact_core_row(
        self,
        connection: Any,
        artifact: Artifact,
        *,
        run_id: str,
        projection: Mapping[str, Any],
        notation: Mapping[str, Any],
        payload_json: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO bssc_artifacts (
                artifact_id, run_id, artifact_type, representation, function_bit, title, notation_key, notation_key_normalized,
                scope, reusability, admissibility, learning_relation, justification,
                structured_encountered_not, structured_lookup_blob,
                structured_composed_not, boundary_shape_blob,
                payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_id) DO UPDATE SET
                artifact_type = excluded.artifact_type,
                representation = excluded.representation,
                function_bit = excluded.function_bit,
                title = excluded.title,
                notation_key = excluded.notation_key,
                notation_key_normalized = excluded.notation_key_normalized,
                scope = excluded.scope,
                reusability = excluded.reusability,
                admissibility = excluded.admissibility,
                learning_relation = excluded.learning_relation,
                justification = excluded.justification,
                structured_encountered_not = excluded.structured_encountered_not,
                structured_lookup_blob = excluded.structured_lookup_blob,
                structured_composed_not = excluded.structured_composed_not,
                boundary_shape_blob = excluded.boundary_shape_blob,
                payload_json = excluded.payload_json,
                created_at = excluded.created_at
            """,
            (
                artifact.id,
                run_id,
                artifact.artifact_type,
                projection["representation"],
                artifact.function_bit,
                artifact.title,
                notation["notation_key"],
                notation["notation_key_normalized"],
                artifact.scope,
                artifact.reusability,
                artifact.admissibility,
                artifact.learning_relation,
                artifact.justification,
                projection["structured_encountered_not"],
                projection["structured_lookup_blob"],
                projection["structured_composed_not"],
                projection["boundary_shape_blob"],
                payload_json,
                artifact.created_at,
            ),
        )

    def _replace_artifact_search_rows_precomputed(
        self,
        connection: Any,
        artifact: Artifact,
        search_projection: Mapping[str, Any],
        *,
        encoded_views: list[list[float]] | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO bssc_artifact_search_units (
                artifact_id, domain, topic, unit_type, layer, cause, severity, artifact_type,
                function_bit, canonical_text, failure_signature, repair_operator, applicability,
                exclusions, source_prompt_archetype, embedding_model, embedding_version,
                boundary_shape_blob, action_posture, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_id) DO UPDATE SET
                domain = excluded.domain,
                topic = excluded.topic,
                unit_type = excluded.unit_type,
                layer = excluded.layer,
                cause = excluded.cause,
                severity = excluded.severity,
                artifact_type = excluded.artifact_type,
                function_bit = excluded.function_bit,
                canonical_text = excluded.canonical_text,
                failure_signature = excluded.failure_signature,
                repair_operator = excluded.repair_operator,
                applicability = excluded.applicability,
                exclusions = excluded.exclusions,
                source_prompt_archetype = excluded.source_prompt_archetype,
                embedding_model = excluded.embedding_model,
                embedding_version = excluded.embedding_version,
                boundary_shape_blob = excluded.boundary_shape_blob,
                action_posture = excluded.action_posture,
                updated_at = excluded.updated_at
            """,
            (
                search_projection["artifact_id"],
                search_projection["domain"],
                search_projection["topic"],
                search_projection["unit_type"],
                search_projection["layer"],
                search_projection["cause"],
                search_projection["severity"],
                search_projection["artifact_type"],
                search_projection["function_bit"],
                search_projection["canonical_text"],
                search_projection["failure_signature"],
                search_projection["repair_operator"],
                search_projection["applicability"],
                search_projection["exclusions"],
                search_projection["source_prompt_archetype"],
                search_projection["embedding_model"],
                search_projection["embedding_version"],
                search_projection["boundary_shape_blob"],
                search_projection["action_posture"],
                search_projection["updated_at"],
            ),
        )
        connection.execute("DELETE FROM bssc_artifact_search_fts WHERE artifact_id = ?", (artifact.id,))
        connection.execute(
            """
            INSERT INTO bssc_artifact_search_fts (
                artifact_id, canonical_text, failure_signature, repair_operator, applicability,
                exclusions, domain, layer, cause, severity, unit_type, artifact_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact.id,
                search_projection["canonical_text"],
                search_projection["failure_signature"],
                search_projection["repair_operator"],
                search_projection["applicability"],
                search_projection["exclusions"],
                search_projection["domain"],
                search_projection["layer"],
                search_projection["cause"],
                search_projection["severity"],
                search_projection["unit_type"],
                search_projection["artifact_type"],
            ),
        )
        connection.execute("DELETE FROM bssc_artifact_search_links WHERE from_artifact_id = ?", (artifact.id,))
        for related_artifact_id in artifact.related_artifact_ids:
            related_id = str(related_artifact_id).strip()
            if not related_id:
                continue
            if not self._artifact_row_exists(connection, related_id):
                continue
            connection.execute(
                """
                INSERT OR REPLACE INTO bssc_artifact_search_links (from_artifact_id, to_artifact_id, relation_type)
                VALUES (?, ?, ?)
                """,
                (artifact.id, related_id, "related_artifact"),
            )
        if self.vector_enabled():
            if encoded_views is None:
                encoded_views = self.encoder.encode(
                    [
                        search_projection["topic_text"],
                        search_projection["failure_text"],
                        search_projection["repair_text"],
                    ]
                )
            for table_name, vector in zip(self.SEARCH_VECTOR_TABLES.values(), encoded_views or [], strict=False):
                connection.execute(f"DELETE FROM {table_name} WHERE artifact_id = ?", (artifact.id,))
                if vector:
                    connection.execute(
                        f"INSERT INTO {table_name}(artifact_id, embedding) VALUES (?, ?)",
                        (artifact.id, self.sqlite_vec.serialize_float32([float(value) for value in vector])),
                    )

    def _index_artifact(self, connection: Any, artifact: Artifact, projection: Mapping[str, Any]) -> None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling index artifact.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_index_artifact(connection=3, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), projection={'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']})`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_index_artifact`. Expected type: `Any`.
            artifact: Value for `artifact` used by `_index_artifact`. Expected type: `Artifact`.
            projection: Value for `projection` used by `_index_artifact`. Expected type: `Mapping[str, Any]`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self.vector_enabled():
            vector = self.encoder.encode_one(self._artifact_text_surface(artifact, projection))
            if vector:
                connection.execute("DELETE FROM bssc_artifact_vec WHERE artifact_id = ?", (artifact.id,))
                connection.execute(
                    "INSERT INTO bssc_artifact_vec(artifact_id, embedding) VALUES (?, ?)",
                    (artifact.id, self.sqlite_vec.serialize_float32([float(value) for value in vector])),
                )
        self._replace_artifact_search_rows(connection, artifact, projection)

    def persist_artifacts(self, artifacts: Iterable[Artifact], *, run_id: str = "artifact_import") -> dict[str, Any]:
        vector_enabled = self.vector_enabled()
        report = {
            "backend": "sqlite_vec",
            "configured": True,
            "database": str(self.sqlite_path),
            "persisted_artifacts": 0,
            "unchanged_artifacts": 0,
            "error_artifacts": 0,
            "status": "skipped",
            "reason": "",
            "vector_enabled": vector_enabled,
            "reports": [],
            "timings": {},
        }
        artifact_list = list(artifacts)
        if not artifact_list:
            report["reason"] = "nothing_to_persist"
            report["timings"] = {"total_seconds": 0.0}
            return report

        timings: dict[str, float] = {}
        total_started = time.perf_counter()
        connection = None
        try:
            connect_started = time.perf_counter()
            connection = self._connect()
            timings["connect_seconds"] = _elapsed_seconds(connect_started)

            ensure_started = time.perf_counter()
            self._ensure_schema(connection)
            timings["ensure_schema_seconds"] = _elapsed_seconds(ensure_started)

            prepare_started = time.perf_counter()
            staged: list[dict[str, Any]] = []
            prepared: list[dict[str, Any]] = []
            reports: list[dict[str, Any]] = []
            staged_notation_ids: dict[str, str] = {}
            for artifact in artifact_list:
                canonicalize_started = time.perf_counter()
                artifact = self._canonicalize_artifact_for_storage(
                    connection,
                    artifact,
                    staged_notation_ids=staged_notation_ids,
                )
                notation = artifact_notation_projection(artifact)
                normalized_key = str(notation.get("notation_key_normalized", "")).strip()
                if normalized_key and artifact.id:
                    staged_notation_ids.setdefault(normalized_key, artifact.id)
                report_item = {
                    "backend": "sqlite_vec",
                    "configured": True,
                    "database": str(self.sqlite_path),
                    "artifact_id": artifact.id,
                    "persisted_artifacts": 0,
                    "status": "skipped",
                    "reason": "",
                    "vector_enabled": vector_enabled,
                    "timings": {
                        "canonicalize_seconds": _elapsed_seconds(canonicalize_started),
                    },
                }
                payload_json = self._artifact_payload_json(artifact)
                payload_digest = _payload_semantic_digest_json(payload_json)
                report_item["payload_digest"] = payload_digest
                staged.append(
                    {
                        "artifact": artifact,
                        "payload_json": payload_json,
                        "payload_digest": payload_digest,
                        "report": report_item,
                    }
                )
                reports.append(report_item)
            existing_lookup_started = time.perf_counter()
            existing_payload_map = self._fetch_existing_payload_json_map(
                connection,
                [item["artifact"].id for item in staged],
            )
            existing_lookup_seconds = _elapsed_seconds(existing_lookup_started)
            timings["existing_payload_batch_lookup_seconds"] = existing_lookup_seconds
            lookup_seconds_per_artifact = existing_lookup_seconds / max(len(staged), 1)
            staged_payload_digests: dict[str, str] = {}
            for item in staged:
                artifact = item["artifact"]
                payload_json = item["payload_json"]
                payload_digest = item["payload_digest"]
                report_item = item["report"]
                report_item["timings"]["existing_payload_lookup_seconds"] = lookup_seconds_per_artifact
                prior_staged_digest = str(staged_payload_digests.get(artifact.id, "")).strip()
                if prior_staged_digest and prior_staged_digest == payload_digest:
                    report_item["status"] = "unchanged"
                    report_item["timings"]["total_seconds"] = (
                        report_item["timings"].get("canonicalize_seconds", 0.0)
                        + report_item["timings"].get("existing_payload_lookup_seconds", 0.0)
                    )
                    continue
                existing_payload_json = existing_payload_map.get(artifact.id, "")
                if existing_payload_json and _payload_semantic_digest_json(existing_payload_json) == payload_digest:
                    report_item["status"] = "unchanged"
                    report_item["timings"]["total_seconds"] = (
                        report_item["timings"].get("canonicalize_seconds", 0.0)
                        + report_item["timings"].get("existing_payload_lookup_seconds", 0.0)
                    )
                    staged_payload_digests[artifact.id] = payload_digest
                    continue
                projection = self._artifact_learning_projection(artifact)
                notation = artifact_notation_projection(artifact)
                write_rows_started = time.perf_counter()
                self._upsert_artifact_core_row(
                    connection,
                    artifact,
                    run_id=run_id,
                    projection=projection,
                    notation=notation,
                    payload_json=payload_json,
                )
                self._replace_notation_item_rows(connection, notation)
                self._replace_boundary_shape_term_rows(connection, artifact)
                self._replace_artifact_normalized_rows(connection, artifact)
                report_item["timings"]["write_rows_seconds"] = _elapsed_seconds(write_rows_started)
                prepared.append(
                    {
                        "artifact": artifact,
                        "projection": projection,
                        "notation": notation,
                        "payload_json": payload_json,
                        "report": report_item,
                    }
                )
                staged_payload_digests[artifact.id] = payload_digest
            timings["prepare_seconds"] = _elapsed_seconds(prepare_started)

            index_started = time.perf_counter()
            if prepared:
                artifact_vectors: list[list[float]] = []
                search_vectors: list[list[list[float]]] = []
                search_projections = [
                    self._artifact_search_projection(item["artifact"], item["projection"])
                    for item in prepared
                ]
                if vector_enabled:
                    main_surfaces = [
                        self._artifact_text_surface(item["artifact"], item["projection"])
                        for item in prepared
                    ]
                    flat_search_surfaces: list[str] = []
                    for search_projection in search_projections:
                        flat_search_surfaces.extend(
                            [
                                search_projection["topic_text"],
                                search_projection["failure_text"],
                                search_projection["repair_text"],
                            ]
                        )
                    encoded_surfaces = self.encoder.encode(main_surfaces + flat_search_surfaces)
                    artifact_vectors = encoded_surfaces[: len(main_surfaces)]
                    encoded_search = encoded_surfaces[len(main_surfaces) :]
                    search_vectors = [
                        encoded_search[index : index + 3]
                        for index in range(0, len(encoded_search), 3)
                    ]
                else:
                    search_vectors = [[] for _ in prepared]

                timings["index_seconds"] = _elapsed_seconds(index_started)
                for index, item in enumerate(prepared):
                    artifact = item["artifact"]
                    if vector_enabled:
                        vector = artifact_vectors[index] if index < len(artifact_vectors) else []
                        connection.execute("DELETE FROM bssc_artifact_vec WHERE artifact_id = ?", (artifact.id,))
                        if vector:
                            connection.execute(
                                "INSERT INTO bssc_artifact_vec(artifact_id, embedding) VALUES (?, ?)",
                                (artifact.id, self.sqlite_vec.serialize_float32([float(value) for value in vector])),
                            )
                    self._replace_artifact_search_rows_precomputed(
                        connection,
                        artifact,
                        search_projections[index],
                        encoded_views=search_vectors[index] if index < len(search_vectors) else [],
                    )
                    item["report"]["persisted_artifacts"] = 1
                    item["report"]["status"] = "persisted"
                    item["report"]["timings"]["index_seconds"] = timings["index_seconds"]
                    item["report"]["timings"].setdefault(
                        "total_seconds",
                        item["report"]["timings"].get("canonicalize_seconds", 0.0)
                        + item["report"]["timings"].get("existing_payload_lookup_seconds", 0.0)
                        + item["report"]["timings"].get("write_rows_seconds", 0.0)
                        + item["report"]["timings"].get("index_seconds", 0.0),
                    )
            commit_started = time.perf_counter()
            connection.commit()
            timings["commit_seconds"] = _elapsed_seconds(commit_started)

            report["persisted_artifacts"] = sum(
                int(item.get("persisted_artifacts", 0) or 0)
                for item in reports
                if str(item.get("status", "")).strip().lower() == "persisted"
            )
            report["unchanged_artifacts"] = sum(
                1 for item in reports if str(item.get("status", "")).strip().lower() == "unchanged"
            )
            if report["persisted_artifacts"] > 0:
                report["status"] = "persisted"
            elif report["unchanged_artifacts"] > 0 and not report["error_artifacts"]:
                report["status"] = "unchanged"
            else:
                report["status"] = "skipped"
            report["reports"] = reports
            timings["total_seconds"] = _elapsed_seconds(total_started)
            report["timings"] = timings
            return report
        except Exception as exc:
            if connection is not None:
                try:
                    connection.rollback()
                except Exception:
                    pass
            if self.fallback_store is not None:
                fallback = self.fallback_store.persist_artifacts(artifact_list, run_id=run_id)
                fallback["reason"] = str(exc)
                fallback["fallback_from"] = "sqlite_vec"
                return fallback
            report["status"] = "error"
            report["reason"] = str(exc)
            report["error_artifacts"] = len(artifact_list)
            report["timings"] = {**timings, "total_seconds": _elapsed_seconds(total_started)}
            return report
        finally:
            if connection is not None:
                connection.close()

    def persist(self, state: SystemState) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling persist.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `persist(state=SystemState.bootstrap(prompt='Compute force from mass and acceleration.'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            state: Value for `state` used by `persist`. Expected type: `SystemState`.

        Returns:
            dict[str, Any]: Result produced by `persist`.
        """
        report = {
            "backend": "sqlite_vec",
            "configured": True,
            "database": str(self.sqlite_path),
            "persisted_artifacts": 0,
            "persisted_discovery_audits": 0,
            "status": "skipped",
            "reason": "",
            "vector_enabled": self.vector_enabled(),
        }
        if not state.artifacts and not state.discovery_audits:
            report["reason"] = "nothing_to_persist"
            return report

        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            for artifact in state.artifacts.values():
                artifact = self._canonicalize_artifact_for_storage(connection, artifact)
                projection = self._artifact_learning_projection(artifact)
                notation = artifact_notation_projection(artifact)
                connection.execute(
                    """
                    INSERT INTO bssc_artifacts (
                    artifact_id, run_id, artifact_type, representation, function_bit, title, notation_key, notation_key_normalized,
                    scope, reusability, admissibility, learning_relation, justification,
                    structured_encountered_not, structured_lookup_blob,
                    structured_composed_not, boundary_shape_blob,
                    payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(artifact_id) DO UPDATE SET
                        artifact_type = excluded.artifact_type,
                        representation = excluded.representation,
                        function_bit = excluded.function_bit,
                        title = excluded.title,
                        notation_key = excluded.notation_key,
                        notation_key_normalized = excluded.notation_key_normalized,
                        scope = excluded.scope,
                        reusability = excluded.reusability,
                        admissibility = excluded.admissibility,
                        learning_relation = excluded.learning_relation,
                        justification = excluded.justification,
                        structured_encountered_not = excluded.structured_encountered_not,
                        structured_lookup_blob = excluded.structured_lookup_blob,
                        structured_composed_not = excluded.structured_composed_not,
                        boundary_shape_blob = excluded.boundary_shape_blob,
                        payload_json = excluded.payload_json,
                        created_at = excluded.created_at
                    """,
                    (
                        artifact.id,
                        state.run_id,
                        artifact.artifact_type,
                        projection["representation"],
                        artifact.function_bit,
                        artifact.title,
                        notation["notation_key"],
                        notation["notation_key_normalized"],
                        artifact.scope,
                        artifact.reusability,
                        artifact.admissibility,
                        artifact.learning_relation,
                        artifact.justification,
                        projection["structured_encountered_not"],
                        projection["structured_lookup_blob"],
                        projection["structured_composed_not"],
                        projection["boundary_shape_blob"],
                        json.dumps(artifact_compatibility_payload(artifact), sort_keys=True),
                        artifact.created_at,
                    ),
                )
                self._replace_notation_item_rows(connection, notation)
                self._replace_boundary_shape_term_rows(connection, artifact)
                self._replace_artifact_normalized_rows(connection, artifact)
                self._index_artifact(connection, artifact, projection)
                report["persisted_artifacts"] += 1
            for audit in state.discovery_audits.values():
                connection.execute(
                    """
                    INSERT INTO bssc_discovery_audits (
                        audit_id, run_id, node_id, pain_class, gain_class, payload_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(audit_id) DO UPDATE SET
                        pain_class = excluded.pain_class,
                        gain_class = excluded.gain_class,
                        payload_json = excluded.payload_json,
                        created_at = excluded.created_at
                    """,
                    (
                        audit.id,
                        state.run_id,
                        audit.node_id,
                        audit.pain_class,
                        audit.gain_class,
                        json.dumps(audit.to_dict(), sort_keys=True),
                        audit.created_at,
                    ),
                )
                report["persisted_discovery_audits"] += 1
            connection.commit()
            report["status"] = "persisted"
            return report
        except Exception as exc:
            if self.fallback_store is not None:
                fallback = self.fallback_store.persist(state)
                fallback["reason"] = str(exc)
                fallback["fallback_from"] = "sqlite_vec"
                return fallback
            report["status"] = "error"
            report["reason"] = str(exc)
            return report
        finally:
            if connection is not None:
                connection.close()

    def persist_artifact(self, artifact: Artifact, *, run_id: str = "artifact_import") -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with persisting artifact.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `persist_artifact(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), run_id='artifact-force')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `persist_artifact`. Expected type: `Artifact`.
            run_id: Value for `run_id` used by `persist_artifact`. Expected type: `str`. Defaults to `'artifact_import'`.

        Returns:
            dict[str, Any]: Result produced by `persist_artifact`.
        """
        report = {
            "backend": "sqlite_vec",
            "configured": True,
            "database": str(self.sqlite_path),
            "artifact_id": artifact.id,
            "persisted_artifacts": 0,
            "status": "skipped",
            "reason": "",
            "vector_enabled": self.vector_enabled(),
            "timings": {},
        }
        connection = None
        total_started = time.perf_counter()
        timings: dict[str, float] = {}
        try:
            connect_started = time.perf_counter()
            connection = self._connect()
            timings["connect_seconds"] = _elapsed_seconds(connect_started)
            ensure_started = time.perf_counter()
            self._ensure_schema(connection)
            timings["ensure_schema_seconds"] = _elapsed_seconds(ensure_started)
            canonicalize_started = time.perf_counter()
            artifact = self._canonicalize_artifact_for_storage(connection, artifact)
            timings["canonicalize_seconds"] = _elapsed_seconds(canonicalize_started)
            report["artifact_id"] = artifact.id
            payload_json = self._artifact_payload_json(artifact)
            payload_digest = _payload_semantic_digest_json(payload_json)
            report["payload_digest"] = payload_digest
            existing_lookup_started = time.perf_counter()
            existing_payload_json = self._fetch_existing_payload_json_map(connection, [artifact.id]).get(artifact.id, "")
            timings["existing_payload_lookup_seconds"] = _elapsed_seconds(existing_lookup_started)
            if existing_payload_json and _payload_semantic_digest_json(existing_payload_json) == payload_digest:
                report["status"] = "unchanged"
                timings["total_seconds"] = _elapsed_seconds(total_started)
                report["timings"] = timings
                return report
            projection_started = time.perf_counter()
            projection = self._artifact_learning_projection(artifact)
            notation = artifact_notation_projection(artifact)
            timings["projection_seconds"] = _elapsed_seconds(projection_started)
            write_started = time.perf_counter()
            self._upsert_artifact_core_row(
                connection,
                artifact,
                run_id=run_id,
                projection=projection,
                notation=notation,
                payload_json=payload_json,
            )
            self._replace_notation_item_rows(connection, notation)
            self._replace_boundary_shape_term_rows(connection, artifact)
            self._replace_artifact_normalized_rows(connection, artifact)
            timings["write_rows_seconds"] = _elapsed_seconds(write_started)
            index_started = time.perf_counter()
            self._index_artifact(connection, artifact, projection)
            timings["index_seconds"] = _elapsed_seconds(index_started)
            commit_started = time.perf_counter()
            connection.commit()
            timings["commit_seconds"] = _elapsed_seconds(commit_started)
            report["persisted_artifacts"] = 1
            report["status"] = "persisted"
            timings["total_seconds"] = _elapsed_seconds(total_started)
            report["timings"] = timings
            return report
        except Exception as exc:
            if self.fallback_store is not None:
                fallback = self.fallback_store.persist_artifact(artifact, run_id=run_id)
                fallback["reason"] = str(exc)
                fallback["fallback_from"] = "sqlite_vec"
                return fallback
            report["status"] = "error"
            report["reason"] = str(exc)
            timings["total_seconds"] = _elapsed_seconds(total_started)
            report["timings"] = timings
            return report
        finally:
            if connection is not None:
                connection.close()

    def load_artifact_by_id(self, artifact_id: str) -> Artifact | None:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading artifact by id.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_artifact_by_id(artifact_id='artifact-force')`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact_id: Value for `artifact_id` used by `load_artifact_by_id`. Expected type: `str`.

        Returns:
            Artifact | None: Result produced by `load_artifact_by_id`.
        """
        if not artifact_id:
            return None
        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            row = connection.execute(
                """
                SELECT
                    artifact_id, run_id, artifact_type, representation, function_bit, title,
                    scope, reusability, admissibility, learning_relation, justification,
                    structured_encountered_not, structured_composed_not, boundary_shape_blob,
                    payload_json, created_at
                FROM bssc_artifacts
                WHERE artifact_id = ?
                LIMIT 1
                """,
                (artifact_id,),
            ).fetchone()
            if row is None:
                return self.fallback_store.load_artifact_by_id(artifact_id)
            artifact = self._hydrate_artifact_from_row(connection, row)
            if artifact is not None:
                return artifact
            return self.fallback_store.load_artifact_by_id(artifact_id)
        except Exception:
            return self.fallback_store.load_artifact_by_id(artifact_id)
        finally:
            if connection is not None:
                connection.close()

    def load_all_artifacts(self) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading all artifacts.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_all_artifacts()`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            list[Artifact]: Result produced by `load_all_artifacts`.
        """
        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            rows = connection.execute(
                """
                SELECT
                    artifact_id, run_id, artifact_type, representation, function_bit, title,
                    scope, reusability, admissibility, learning_relation, justification,
                    structured_encountered_not, structured_composed_not, boundary_shape_blob,
                    payload_json, created_at
                FROM bssc_artifacts
                WHERE admissibility <> ?
                ORDER BY created_at ASC
                """
                ,
                ("rejected",),
            ).fetchall()
            artifacts: list[Artifact] = []
            seen: set[str] = set()
            for row in rows:
                artifact = self._hydrate_artifact_from_row(connection, row)
                if artifact is None:
                    continue
                if artifact.id in seen:
                    continue
                seen.add(artifact.id)
                artifacts.append(artifact)
            if artifacts:
                return artifacts
            return self.fallback_store.load_all_artifacts()
        except Exception:
            return self.fallback_store.load_all_artifacts()
        finally:
            if connection is not None:
                connection.close()

    def _fetch_artifacts_by_ids(self, connection: Any, artifact_ids: list[str], *, limit: int) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch artifacts by ids.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_fetch_artifacts_by_ids(connection=3, artifact_ids=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_artifacts_by_ids`. Expected type: `Any`.
            artifact_ids: Value for `artifact_ids` used by `_fetch_artifacts_by_ids`. Expected type: `list[str]`.
            limit: Value for `limit` used by `_fetch_artifacts_by_ids`. Expected type: `int`.

        Returns:
            list[Artifact]: Result produced by `_fetch_artifacts_by_ids`.
        """
        if not artifact_ids:
            return []
        ordered_unique_ids = []
        seen: set[str] = set()
        for artifact_id in artifact_ids:
            if artifact_id and artifact_id not in seen:
                ordered_unique_ids.append(artifact_id)
                seen.add(artifact_id)
        placeholders = ",".join("?" for _ in ordered_unique_ids)
        rows = connection.execute(
            f"""
            SELECT
                artifact_id, run_id, artifact_type, representation, function_bit, title,
                scope, reusability, admissibility, learning_relation, justification,
                structured_encountered_not, structured_composed_not, boundary_shape_blob,
                payload_json, created_at
            FROM bssc_artifacts
            WHERE artifact_id IN ({placeholders})
            """,
            tuple(ordered_unique_ids),
        ).fetchall()
        row_by_id = {str(row["artifact_id"]): row for row in rows}
        ordered: list[Artifact] = []
        for artifact_id in ordered_unique_ids:
            row = row_by_id.get(artifact_id)
            if row is None:
                continue
            artifact = self._hydrate_artifact_from_row(connection, row)
            if artifact is None:
                continue
            ordered.append(artifact)
            if len(ordered) >= limit:
                break
        return ordered

    def _fts_match_expression(self, text: str) -> str:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fts match expression.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_fts_match_expression(text='Compute force from mass and acceleration.')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `_fts_match_expression`. Expected type: `str`.

        Returns:
            str: Result produced by `_fts_match_expression`.
        """
        tokens = ordered_unique(
            [str(item).strip().lower() for item in semantic_tokens(text) if str(item).strip()]
            + learning_lookup_keys(text)
        )
        quoted = [f'"{token.replace("\"", "\"\"")}"' for token in tokens if len(token) >= 2][:10]
        return " OR ".join(quoted)

    def _query_search_projection(self, semantic_unit: str) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling query search projection.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_query_search_projection(semantic_unit='Physics / Force / Force From Mass And Acceleration')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_unit: Value for `semantic_unit` used by `_query_search_projection`. Expected type: `str`.

        Returns:
            dict[str, Any]: Result produced by `_query_search_projection`.
        """
        structured = normalize_not_elaboration_payload(semantic_unit, None)
        topic_text = self._compact_search_text(
            [
                semantic_unit,
                structured.get("encountered_not", ""),
                structured.get("composed_not", ""),
                *structured.get("lookup_keys", []),
            ],
            limit=18,
        )
        failure_text = self._compact_search_text(
            [
                structured.get("encountered_not", ""),
                *structured.get("unknowns", []),
                *structured.get("missing_components", []),
                *structured.get("distorted_components", []),
                *structured.get("differentiators", []),
                *structured.get("risk_of_wrong_closure", []),
                *structured.get("misalignment_types", []),
                *structured.get("origin_layers", []),
                structured.get("degree", ""),
                structured.get("action_posture", ""),
            ],
            limit=18,
        )
        repair_text = self._compact_search_text(
            [
                *structured.get("minimal_repair", []),
                *structured.get("success_criteria", []),
                *structured.get("full_repair", []),
                structured.get("action_posture", ""),
            ],
            limit=18,
        )
        return {
            "structured": structured,
            "topic_text": topic_text or semantic_unit,
            "failure_text": failure_text or topic_text or semantic_unit,
            "repair_text": repair_text or topic_text or semantic_unit,
        }

    def _vector_candidate_scores(self, connection: Any, table_name: str, query_text: str, *, limit: int) -> dict[str, float]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling vector candidate scores.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_vector_candidate_scores(connection=3, table_name='force', query_text='Compute force from mass and acceleration.', limit=3)`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_vector_candidate_scores`. Expected type: `Any`.
            table_name: Value for `table_name` used by `_vector_candidate_scores`. Expected type: `str`.
            query_text: Value for `query_text` used by `_vector_candidate_scores`. Expected type: `str`.
            limit: Value for `limit` used by `_vector_candidate_scores`. Expected type: `int`.

        Returns:
            dict[str, float]: Result produced by `_vector_candidate_scores`.
        """
        if not self.vector_enabled() or not query_text:
            return {}
        vector = self.encoder.encode_one(query_text)
        if not vector:
            return {}
        rows = connection.execute(
            f"SELECT artifact_id, distance FROM {table_name} WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (
                self.sqlite_vec.serialize_float32([float(value) for value in vector]),
                max(limit * 4, 16),
            ),
        ).fetchall()
        scores: dict[str, float] = {}
        for index, row in enumerate(rows):
            artifact_id = str(row["artifact_id"] or "").strip()
            if not artifact_id:
                continue
            distance = float(row["distance"] or 0.0)
            similarity = 1.0 / (1.0 + max(distance, 0.0))
            order_bonus = 1.0 / float(index + 1)
            scores[artifact_id] = max(scores.get(artifact_id, 0.0), (0.70 * similarity) + (0.30 * order_bonus))
        return scores

    def _exact_semantic_candidate_ids(self, connection: Any, semantic_unit: str, *, limit: int) -> list[str]:
        normalized = " ".join(str(semantic_unit or "").strip().lower().split())
        if not normalized:
            return []
        rows = connection.execute(
            """
            SELECT artifact_id
            FROM bssc_artifacts
            WHERE admissibility <> ?
              AND (
                LOWER(TRIM(COALESCE(title, ''))) = ?
                OR LOWER(TRIM(COALESCE(notation_key_normalized, ''))) = ?
              )
            ORDER BY created_at DESC
            LIMIT ?
            """,
            ("rejected", normalized, normalized, max(limit * 4, 16)),
        ).fetchall()
        return [str(row["artifact_id"]) for row in rows if row["artifact_id"]]

    def _fts_candidate_scores(self, connection: Any, query_text: str, *, limit: int) -> dict[str, float]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fts candidate scores.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_fts_candidate_scores(connection=3, query_text='Compute force from mass and acceleration.', limit=3)`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fts_candidate_scores`. Expected type: `Any`.
            query_text: Value for `query_text` used by `_fts_candidate_scores`. Expected type: `str`.
            limit: Value for `limit` used by `_fts_candidate_scores`. Expected type: `int`.

        Returns:
            dict[str, float]: Result produced by `_fts_candidate_scores`.
        """
        expression = self._fts_match_expression(query_text)
        if not expression:
            return {}
        rows = connection.execute(
            """
            SELECT artifact_id, bm25(bssc_artifact_search_fts) AS rank_score
            FROM bssc_artifact_search_fts
            WHERE bssc_artifact_search_fts MATCH ?
            LIMIT ?
            """,
            (expression, max(limit * 4, 16)),
        ).fetchall()
        scores: dict[str, float] = {}
        for index, row in enumerate(rows):
            artifact_id = str(row["artifact_id"] or "").strip()
            if not artifact_id:
                continue
            rank_score = float(row["rank_score"] or 0.0)
            bm25_score = 1.0 / (1.0 + max(rank_score, 0.0))
            order_bonus = 1.0 / float(index + 1)
            scores[artifact_id] = max(scores.get(artifact_id, 0.0), (0.50 * bm25_score) + (0.50 * order_bonus))
        return scores

    def _input_contract_candidate_ids(self, connection: Any, named_input_keys: list[str], *, limit: int) -> list[str]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling input contract candidate ids.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `_input_contract_candidate_ids(connection=3, named_input_keys=['mass', 'acceleration', 'force'], limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_input_contract_candidate_ids`. Expected type: `Any`.
            named_input_keys: Value for `named_input_keys` used by `_input_contract_candidate_ids`. Expected type: `list[str]`.
            limit: Value for `limit` used by `_input_contract_candidate_ids`. Expected type: `int`.

        Returns:
            list[str]: Result produced by `_input_contract_candidate_ids`.
        """
        if not named_input_keys:
            return []
        item_placeholders = ",".join("?" for _ in named_input_keys)
        rows = connection.execute(
            f"""
            SELECT DISTINCT bssc_artifacts.artifact_id
            FROM bssc_artifacts
            LEFT JOIN bssc_artifact_input_contract_items input_items
              ON input_items.artifact_id = bssc_artifacts.artifact_id
            WHERE bssc_artifacts.admissibility <> ?
              AND (
                LOWER(COALESCE(input_items.item_key, '')) IN ({item_placeholders})
                OR {' OR '.join(
                    [
                        """
                        EXISTS (
                            SELECT 1
                            FROM bssc_artifact_in_items notation_in_item
                            WHERE notation_in_item.notation_key = bssc_artifacts.notation_key
                              AND notation_in_item.item_normalized LIKE ?
                        )
                        """
                        for _ in named_input_keys
                    ]
                )}
              )
            LIMIT ?
            """,
            tuple(["rejected", *[item.lower() for item in named_input_keys], *[f"{item.lower()}:%" for item in named_input_keys], max(limit * 8, 32)]),
        ).fetchall()
        return [str(row["artifact_id"]) for row in rows if row["artifact_id"]]

    def _fetch_search_unit_rows(self, connection: Any, artifact_ids: list[str]) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling fetch search unit rows.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_fetch_search_unit_rows(connection=3, artifact_ids=[{'title': 'Physics / Force / Force From Mass And Acceleration'}])`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_fetch_search_unit_rows`. Expected type: `Any`.
            artifact_ids: Value for `artifact_ids` used by `_fetch_search_unit_rows`. Expected type: `list[str]`.

        Returns:
            dict[str, Any]: Result produced by `_fetch_search_unit_rows`.
        """
        if not artifact_ids:
            return {}
        placeholders = ",".join("?" for _ in artifact_ids)
        rows = connection.execute(
            f"""
            SELECT
                artifact_id, unit_type, layer, cause, severity, artifact_type, function_bit,
                applicability, exclusions, boundary_shape_blob, action_posture
            FROM bssc_artifact_search_units
            WHERE artifact_id IN ({placeholders})
            """,
            tuple(artifact_ids),
        ).fetchall()
        return {str(row["artifact_id"]): row for row in rows}

    def _hybrid_candidate_ids(self, connection: Any, semantic_unit: str, *, limit: int) -> list[str]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling hybrid candidate ids.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_hybrid_candidate_ids(connection=3, semantic_unit='Physics / Force / Force From Mass And Acceleration', limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_hybrid_candidate_ids`. Expected type: `Any`.
            semantic_unit: Value for `semantic_unit` used by `_hybrid_candidate_ids`. Expected type: `str`.
            limit: Value for `limit` used by `_hybrid_candidate_ids`. Expected type: `int`.

        Returns:
            list[str]: Result produced by `_hybrid_candidate_ids`.
        """
        query_projection = self._query_search_projection(semantic_unit)
        structured = query_projection["structured"]
        named_input_keys = semantic_named_input_keys(semantic_unit)
        exact_ids = self._exact_semantic_candidate_ids(connection, semantic_unit, limit=limit)
        input_contract_ids = self._input_contract_candidate_ids(connection, named_input_keys, limit=limit)
        lexical_scores: dict[str, float] = {}
        for query_text in (query_projection["topic_text"], query_projection["failure_text"], query_projection["repair_text"]):
            for artifact_id, score in self._fts_candidate_scores(connection, query_text, limit=limit).items():
                lexical_scores[artifact_id] = max(lexical_scores.get(artifact_id, 0.0), score)
        if exact_ids:
            topic_scores: dict[str, float] = {}
            failure_scores: dict[str, float] = {}
            repair_scores: dict[str, float] = {}
        else:
            topic_scores = self._vector_candidate_scores(connection, self.SEARCH_VECTOR_TABLES["topic"], query_projection["topic_text"], limit=limit)
            failure_scores = self._vector_candidate_scores(connection, self.SEARCH_VECTOR_TABLES["failure"], query_projection["failure_text"], limit=limit)
            repair_scores = self._vector_candidate_scores(connection, self.SEARCH_VECTOR_TABLES["repair"], query_projection["repair_text"], limit=limit)
        candidate_ids = ordered_unique(
            exact_ids
            + input_contract_ids
            + list(topic_scores.keys())
            + list(failure_scores.keys())
            + list(repair_scores.keys())
            + list(lexical_scores.keys())
        )[: max(limit * 8, 32)]
        search_rows = self._fetch_search_unit_rows(connection, candidate_ids)
        query_layer_values = {str(item).strip() for item in structured.get("misalignment_types", []) if str(item).strip()}
        query_origin_values = {str(item).strip() for item in structured.get("origin_layers", []) if str(item).strip()}
        query_boundary_values = {str(item).strip() for item in structured.get("boundary_shape", []) if str(item).strip()}
        query_degree = str(structured.get("degree", "")).strip()
        query_posture = str(structured.get("action_posture", "")).strip()
        exclusion_tokens = {
            *learning_lookup_keys(" ".join(str(item) for item in structured.get("unknowns", []))),
            *learning_lookup_keys(" ".join(str(item) for item in structured.get("differentiators", []))),
            *learning_lookup_keys(" ".join(str(item) for item in structured.get("risk_of_wrong_closure", []))),
        }
        scored_ids: list[tuple[float, str]] = []
        input_contract_id_set = set(input_contract_ids)
        for artifact_id in candidate_ids:
            row = search_rows.get(artifact_id)
            lexical_score = lexical_scores.get(artifact_id, 0.0)
            topic_score = topic_scores.get(artifact_id, 0.0)
            failure_score = failure_scores.get(artifact_id, 0.0)
            repair_score = repair_scores.get(artifact_id, 0.0)
            metadata_bonus = 0.0
            exclusion_penalty = 0.0
            if row is not None:
                row_layers = {item.strip() for item in str(row["layer"] or "").split(",") if item.strip()}
                row_origins = {item.strip() for item in str(row["cause"] or "").split(",") if item.strip()}
                row_boundary = {item.strip() for item in str(row["boundary_shape_blob"] or "").split("|") if item.strip()}
                row_posture = str(row["action_posture"] or "").strip()
                applicability = str(row["applicability"] or "").lower()
                exclusions = str(row["exclusions"] or "").lower()
                if query_posture and row_posture == query_posture:
                    metadata_bonus += 0.10
                if query_layer_values and row_layers.intersection(query_layer_values):
                    metadata_bonus += 0.06
                if query_origin_values and row_origins.intersection(query_origin_values):
                    metadata_bonus += 0.04
                if query_degree and str(row["severity"] or "").strip() == query_degree:
                    metadata_bonus += 0.03
                if query_boundary_values and row_boundary:
                    if query_boundary_values.issubset(row_boundary):
                        metadata_bonus += 0.10
                    elif query_boundary_values.intersection(row_boundary):
                        metadata_bonus += 0.05
                if query_posture == "compute_or_template":
                    if int(row["function_bit"] or 0) == 1:
                        metadata_bonus += 0.12
                    elif named_input_keys:
                        exclusion_penalty += 0.04
                elif int(row["function_bit"] or 0) == 1 and query_posture in {"direct_resolution", "next_step_guidance", "clarify_before_acting"}:
                    exclusion_penalty += 0.02
                if named_input_keys:
                    covered_named_inputs = sum(1 for key in named_input_keys if key.lower() in applicability)
                    metadata_bonus += min(covered_named_inputs, len(named_input_keys)) * 0.04
                if exclusions and exclusion_tokens:
                    overlap = sum(1 for token in exclusion_tokens if token and token in exclusions)
                    exclusion_penalty += min(overlap, 4) * 0.03
            if artifact_id in input_contract_id_set:
                metadata_bonus += 0.12
            if artifact_id in exact_ids:
                metadata_bonus += 0.40
            final_score = (
                (0.30 * topic_score)
                + (0.35 * failure_score)
                + (0.20 * repair_score)
                + (0.15 * lexical_score)
                + metadata_bonus
                - exclusion_penalty
            )
            scored_ids.append((final_score, artifact_id))
        scored_ids.sort(key=lambda item: (-item[0], item[1]))
        return [artifact_id for _, artifact_id in scored_ids[: max(limit * 4, 16)]]

    def _legacy_candidate_ids(self, connection: Any, semantic_unit: str, *, limit: int) -> list[str]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with handling legacy candidate ids.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory.

        Example Input Output:
            Input: `_legacy_candidate_ids(connection=3, semantic_unit='Physics / Force / Force From Mass And Acceleration', limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            connection: Value for `connection` used by `_legacy_candidate_ids`. Expected type: `Any`.
            semantic_unit: Value for `semantic_unit` used by `_legacy_candidate_ids`. Expected type: `str`.
            limit: Value for `limit` used by `_legacy_candidate_ids`. Expected type: `int`.

        Returns:
            list[str]: Result produced by `_legacy_candidate_ids`.
        """
        exact_ids = self._exact_semantic_candidate_ids(connection, semantic_unit, limit=limit)
        artifact_ids: list[str] = list(exact_ids)
        if self.vector_enabled() and not exact_ids:
            query_vector = self.encoder.encode_one(semantic_unit)
            if query_vector:
                rows = connection.execute(
                    "SELECT artifact_id, distance FROM bssc_artifact_vec WHERE embedding MATCH ? AND k = ? ORDER BY distance",
                    (
                        self.sqlite_vec.serialize_float32([float(value) for value in query_vector]),
                        max(limit * 4, 16),
                    ),
                ).fetchall()
                artifact_ids.extend(str(row["artifact_id"]) for row in rows if row["artifact_id"])

        query_keys = ordered_unique(learning_lookup_keys(semantic_unit))
        named_input_keys = semantic_named_input_keys(semantic_unit)
        input_contract_ids = self._input_contract_candidate_ids(connection, named_input_keys, limit=limit)
        lexical_ids: list[str] = []
        if query_keys:
            clauses: list[str] = []
            params: list[Any] = []
            for key in query_keys:
                clauses.append("LOWER(COALESCE(structured_encountered_not, '')) = ?")
                params.append(key)
            for key in query_keys:
                clauses.append("COALESCE(notation_key_normalized, '') = ?")
                params.append(key)
            for key in query_keys:
                clauses.append("LOWER(COALESCE(structured_lookup_blob, '')) LIKE ?")
                params.append(f"%{key}%")
            for key in query_keys:
                clauses.append(
                    """
                    EXISTS (
                        SELECT 1
                        FROM bssc_artifact_in_items notation_in_item
                        WHERE notation_in_item.notation_key = bssc_artifacts.notation_key
                          AND notation_in_item.item_normalized LIKE ?
                    )
                    """
                )
                params.append(f"%{key}%")
            for key in query_keys:
                clauses.append(
                    """
                    EXISTS (
                        SELECT 1
                        FROM bssc_artifact_out_items notation_out_item
                        WHERE notation_out_item.notation_key = bssc_artifacts.notation_key
                          AND notation_out_item.item_normalized LIKE ?
                    )
                    """
                )
                params.append(f"%{key}%")
            for key in query_keys[:2]:
                clauses.append("LOWER(COALESCE(title, '')) LIKE ?")
                clauses.append("LOWER(COALESCE(scope, '')) LIKE ?")
                params.extend([f"%{key}%", f"%{key}%"])
            clauses.append("(reusability = ? AND artifact_type <> ?)")
            params.extend(["broad_reuse", "knowledge"])
            rows = connection.execute(
                f"""
                SELECT artifact_id
                FROM bssc_artifacts
                WHERE admissibility <> ? AND ({' OR '.join(clauses)})
                ORDER BY created_at DESC
                LIMIT ?
                """,
                tuple(["rejected", *params, max(limit * 8, 32)]),
            ).fetchall()
            lexical_ids.extend(str(row["artifact_id"]) for row in rows if row["artifact_id"])

        return ordered_unique(exact_ids + input_contract_ids + artifact_ids + lexical_ids)[: max(limit * 4, 16)]

    def load_relevant_artifacts(self, semantic_unit: str, *, limit: int = 8) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading relevant artifacts.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_relevant_artifacts(semantic_unit='Physics / Force / Force From Mass And Acceleration', limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_unit: Value for `semantic_unit` used by `load_relevant_artifacts`. Expected type: `str`.
            limit: Value for `limit` used by `load_relevant_artifacts`. Expected type: `int`. Defaults to `8`.

        Returns:
            list[Artifact]: Result produced by `load_relevant_artifacts`.
        """
        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            hybrid_ids = self._hybrid_candidate_ids(connection, semantic_unit, limit=limit)
            hybrid_results = self._fetch_artifacts_by_ids(connection, hybrid_ids, limit=limit)
            normalized_semantic_unit = " ".join(str(semantic_unit or "").strip().lower().split())
            if hybrid_results and any(
                " ".join(str(item.title or "").strip().lower().split()) == normalized_semantic_unit
                for item in hybrid_results
            ):
                return hybrid_results
            legacy_ids = self._legacy_candidate_ids(connection, semantic_unit, limit=limit)
            ordered_ids = ordered_unique(hybrid_ids + legacy_ids)[: max(limit * 4, 16)]
            results = self._fetch_artifacts_by_ids(connection, ordered_ids, limit=limit)
            if results:
                return results
            return self.fallback_store.load_relevant_artifacts(semantic_unit, limit=limit)
        except Exception:
            return self.fallback_store.load_relevant_artifacts(semantic_unit, limit=limit)
        finally:
            if connection is not None:
                connection.close()

    def load_recent_artifacts(self, *, limit: int = 12) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with loading recent artifacts.

        Reference to Theory:
            Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `load_recent_artifacts(limit=3)`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            limit: Value for `limit` used by `load_recent_artifacts`. Expected type: `int`. Defaults to `12`.

        Returns:
            list[Artifact]: Result produced by `load_recent_artifacts`.
        """
        connection = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            rows = connection.execute(
                """
                SELECT
                    artifact_id, run_id, artifact_type, representation, function_bit, title,
                    scope, reusability, admissibility, learning_relation, justification,
                    structured_encountered_not, structured_composed_not, boundary_shape_blob,
                    payload_json, created_at
                FROM bssc_artifacts
                WHERE admissibility <> ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                ("rejected", max(8, limit * 4)),
            ).fetchall()
            ordered: list[Artifact] = []
            seen: set[str] = set()
            for row in rows:
                artifact = self._hydrate_artifact_from_row(connection, row)
                if artifact is None:
                    continue
                if artifact.id in seen:
                    continue
                ordered.append(artifact)
                seen.add(artifact.id)
                if len(ordered) >= limit:
                    break
            if ordered:
                return ordered
            return self.fallback_store.load_recent_artifacts(limit=limit)
        except Exception:
            return self.fallback_store.load_recent_artifacts(limit=limit)
        finally:
            if connection is not None:
                connection.close()


def build_artifact_store() -> SQLiteVectorArtifactStore:
    """
    High Level Purpose:
        In circumstances like artifact persistence, retrieval, indexing, and cross-run reuse, helps with building artifact store.

    Reference to Theory:
        Materializes the semantic graph in SQLite/vector storage so title-depth reuse, artifact persistence, and composition can survive across runs under the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `build_artifact_store()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        None.

    Returns:
        SQLiteVectorArtifactStore: Result produced by `build_artifact_store`.
    """
    return SQLiteVectorArtifactStore(fallback_store=ArtifactStore())
