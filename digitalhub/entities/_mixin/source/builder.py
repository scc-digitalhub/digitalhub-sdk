# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol, cast, get_args

from digitalhub.entities._mixin.source.models import SourceCode
from digitalhub.utils.exceptions import BuilderError

if TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import Spec


class _SourceBuilderBase(Protocol):
    ENTITY_SPEC_CLASS: type[Spec]

    def build(self, *args: Any, **kwargs: Any) -> Any: ...

    def from_dict(self, obj: dict) -> Any: ...


class _SourceBuildResult(Protocol):
    def _post_build_source_check(self) -> Any: ...


def _find_source_model(annotation: Any) -> type[SourceCode] | None:
    if isinstance(annotation, type) and issubclass(annotation, SourceCode):
        return annotation
    for argument in get_args(annotation):
        model = _find_source_model(argument)
        if model is not None:
            return model
    return None


class SourceBuilderMixin:
    """Collect source-specific build inputs and validate local source files."""

    def _get_source_model(self) -> type[SourceCode]:
        builder = cast(_SourceBuilderBase, self)
        source_field = builder.ENTITY_SPEC_CLASS.model_fields.get("source")
        source_model = _find_source_model(source_field.annotation) if source_field is not None else None
        if source_model is None:
            raise BuilderError("ENTITY_SPEC_CLASS must declare a SourceCode 'source' field.")
        return source_model

    def _prepare_source_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        builder = cast(_SourceBuilderBase, self)
        source_model = self._get_source_model()
        spec_fields = set(builder.ENTITY_SPEC_CLASS.model_fields)
        source_fields = [
            field_name
            for field_name in source_model.model_fields
            if field_name != "source" and field_name not in spec_fields
        ]
        if "code_src" not in spec_fields:
            source_fields.append("code_src")

        prepared = dict(kwargs)
        top_level_source = {
            field_name: prepared.pop(field_name) for field_name in source_fields if field_name in prepared
        }

        nested_source = prepared.get("source")
        if nested_source is None:
            source = {}
        elif isinstance(nested_source, Mapping):
            source = dict(nested_source)
        elif isinstance(nested_source, SourceCode):
            source = nested_source.model_dump(mode="python", exclude_none=True)
        else:
            if top_level_source:
                raise BuilderError(
                    "Top-level source parameters require 'source' to be a mapping or SourceCode instance."
                )
            return prepared

        for field_name, value in top_level_source.items():
            source.setdefault(field_name, value)
        prepared["source"] = source
        return prepared

    def _prepare_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Hook for runtime-specific non-source parameters."""
        return kwargs

    def build(self, *args: Any, **kwargs: Any) -> Any:
        prepared = self._prepare_source_kwargs(kwargs)
        prepared = self._prepare_kwargs(prepared)
        entity = cast(_SourceBuilderBase, super()).build(*args, **prepared)
        return cast(_SourceBuildResult, entity)._post_build_source_check()

    def from_dict(self, obj: dict) -> Any:
        entity = cast(_SourceBuilderBase, super()).from_dict(obj)
        return cast(_SourceBuildResult, entity)._post_build_source_check()
