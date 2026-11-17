# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.entities.dataitem.table.utils as table_utils
import digitalhub.stores.readers.data.api as reader_api


def test_read_data_sample_dispatches_source_list_by_first_path(monkeypatch) -> None:
    source = ["first.csv", "second.csv"]
    reader = Mock()
    reader.get_limit_arg_name.return_value = "n_rows"
    store = Mock()
    store.read_df.return_value = "dataframe"
    get_store = Mock(return_value=store)
    monkeypatch.setattr(reader_api, "get_reader_by_engine", Mock(return_value=reader))
    monkeypatch.setattr(table_utils, "get_store", get_store)

    result = table_utils.read_data_sample(source, file_format="csv", engine="polars")

    assert result == "dataframe"
    get_store.assert_called_once_with("first.csv")
    store.read_df.assert_called_once_with(
        source,
        file_format="csv",
        engine="polars",
        n_rows=10,
    )


def test_process_data_kwargs_builds_path_from_explicit_default_store(monkeypatch) -> None:
    data = object()
    reader = Mock()
    reader.get_schema.return_value = {"fields": []}
    monkeypatch.setattr(reader_api, "get_reader_by_object", Mock(return_value=reader))
    monkeypatch.setattr(table_utils, "build_uuid", Mock(return_value="entity-id"))
    build_path = Mock(return_value="s3://bucket/project/dataitem/table/entity-id/table.parquet")
    monkeypatch.setattr(table_utils, "build_log_path_from_filename", build_path)

    result = table_utils.process_data_kwargs(
        "project",
        "table",
        data,
        default_store="s3://bucket",
        filename="table.parquet",
    )

    assert result == {
        "uuid": "entity-id",
        "path": "s3://bucket/project/dataitem/table/entity-id/table.parquet",
        "schema": {"fields": []},
    }
    build_path.assert_called_once_with(
        "project",
        "dataitem",
        "table",
        "entity-id",
        "table.parquet",
        default_store="s3://bucket",
    )


def test_process_data_kwargs_preserves_positional_path_argument(monkeypatch) -> None:
    data = object()
    reader = Mock()
    reader.get_schema.return_value = {"fields": []}
    monkeypatch.setattr(reader_api, "get_reader_by_object", Mock(return_value=reader))

    result = table_utils.process_data_kwargs(
        "project",
        "table",
        data,
        "s3://bucket/custom/path",
        ["input.csv"],
        None,
    )

    assert result == {"path": "s3://bucket/custom/path", "schema": {"fields": []}}
