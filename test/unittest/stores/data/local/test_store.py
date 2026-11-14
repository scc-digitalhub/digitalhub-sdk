from pathlib import Path
from unittest.mock import Mock

import pytest

from digitalhub.stores.data.local.store import LocalStore
from digitalhub.utils.exceptions import StoreError


def test_read_df_directory_infers_extension_per_regular_file(tmp_path) -> None:
    directory = tmp_path / "data"
    directory.mkdir()
    (directory / "table.csv").write_text("csv")
    (directory / "table.json").write_text("json")
    (directory / ".hidden.csv").write_text("hidden")
    (directory / "subdirectory").mkdir()

    store = object.__new__(LocalStore)
    reader = Mock()
    reader.read_df.side_effect = ["csv-frame", "json-frame"]
    reader.concat_dfs.return_value = "combined"
    store._get_reader = Mock(return_value=reader)

    assert store.read_df(str(directory)) == "combined"

    read_calls = {Path(call.args[0]).name: call.args[1] for call in reader.read_df.call_args_list}
    assert read_calls == {"table.csv": "csv", "table.json": "json"}
    reader.concat_dfs.assert_called_once_with(["csv-frame", "json-frame"])


def test_read_df_infers_extension_per_source_in_list(tmp_path) -> None:
    csv_path = tmp_path / "table.csv"
    json_path = tmp_path / "table.json"
    csv_path.write_text("csv")
    json_path.write_text("json")

    store = object.__new__(LocalStore)
    reader = Mock()
    reader.read_df.side_effect = ["csv-frame", "json-frame"]
    reader.concat_dfs.return_value = "combined"
    store._get_reader = Mock(return_value=reader)

    assert store.read_df([str(csv_path), str(json_path)]) == "combined"

    assert [call.args[1] for call in reader.read_df.call_args_list] == ["csv", "json"]


def test_read_df_empty_directory_raises_store_error(tmp_path) -> None:
    store = object.__new__(LocalStore)
    reader = Mock()
    store._get_reader = Mock(return_value=reader)
    directory = tmp_path / "empty"
    directory.mkdir()

    with pytest.raises(StoreError, match="No readable data files found"):
        store.read_df(str(directory))

    reader.concat_dfs.assert_not_called()
