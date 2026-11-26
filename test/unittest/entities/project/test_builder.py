# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest

from digitalhub.entities.project._base.builder import ProjectProjectBuilder


def test_project_builder_preserves_extensions(monkeypatch) -> None:
    builder = ProjectProjectBuilder()
    build_entity = Mock(return_value="project")
    monkeypatch.setattr(builder, "build_entity", build_entity)
    extensions = [{"key": "value"}]

    result = builder.build(
        name="project",
        kind="project/project",
        extensions=extensions,
    )

    assert result == "project"
    build_entity.assert_called_once_with(
        name="project",
        kind="project/project",
        metadata=build_entity.call_args.kwargs["metadata"],
        spec=build_entity.call_args.kwargs["spec"],
        status=build_entity.call_args.kwargs["status"],
        extensions=extensions,
    )


def test_project_builder_parses_extensions_from_dict(monkeypatch) -> None:
    builder = ProjectProjectBuilder()
    project = Mock(_obj_attr=())
    build_entity = Mock(return_value=project)
    monkeypatch.setattr(builder, "build_entity", build_entity)
    extensions = [{"key": "value"}]

    result = builder.from_dict(
        {
            "name": "project",
            "kind": "project/project",
            "metadata": {},
            "spec": {},
            "status": {},
            "extensions": extensions,
        }
    )

    assert result is project
    assert build_entity.call_args.kwargs["extensions"] == extensions


def test_project_builder_rejects_unknown_spec_fields() -> None:
    builder = ProjectProjectBuilder()

    with pytest.raises(TypeError, match="Unexpected spec parameter.*future_backend_field"):
        builder.build(
            name="project",
            kind="project/project",
            future_backend_field="value",
        )


def test_project_builder_from_dict_preserves_forward_compatible_spec_fields(monkeypatch) -> None:
    builder = ProjectProjectBuilder()
    project = Mock(_obj_attr=())
    build_entity = Mock(return_value=project)
    monkeypatch.setattr(builder, "build_entity", build_entity)

    result = builder.from_dict(
        {
            "name": "project",
            "kind": "project/project",
            "metadata": {},
            "spec": {"future_backend_field": "value"},
            "status": {},
        }
    )

    assert result is project
    assert build_entity.call_args.kwargs["spec"].future_backend_field == "value"
