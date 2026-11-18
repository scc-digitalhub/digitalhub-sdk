# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.entities._processors.context.material as material_module
from digitalhub.entities._processors.context.material import ContextEntityMaterialProcessor


def test_build_log_kwargs_preserves_explicit_path(monkeypatch) -> None:
    get_default_store = Mock()
    monkeypatch.setattr(material_module, "get_default_store", get_default_store)
    processor = ContextEntityMaterialProcessor(Mock())

    result = processor.build_log_kwargs(
        "project",
        "data",
        "dataitem",
        "./data.csv",
        path="s3://bucket/existing.csv",
        format="csv",
    )

    assert result == {"path": "s3://bucket/existing.csv", "format": "csv"}
    get_default_store.assert_not_called()


def test_build_log_kwargs_generates_partition_path(monkeypatch) -> None:
    get_default_store = Mock(return_value="s3://bucket")
    build_path = Mock(return_value="s3://bucket/project/dataitem/data/id/data.csv")
    monkeypatch.setattr(material_module, "get_default_store", get_default_store)
    monkeypatch.setattr(material_module, "build_uuid", Mock(return_value="id"))
    monkeypatch.setattr(material_module, "build_log_path_from_source", build_path)
    processor = ContextEntityMaterialProcessor(Mock())

    result = processor.build_log_kwargs(
        "project",
        "data",
        "dataitem",
        "./data.csv",
        format="csv",
    )

    assert result == {
        "uuid": "id",
        "path": "s3://bucket/project/dataitem/data/id/data.csv",
        "format": "csv",
    }
    get_default_store.assert_called_once_with("project")
    build_path.assert_called_once_with(
        "project",
        "dataitem",
        "data",
        "id",
        "./data.csv",
        default_store="s3://bucket",
    )
