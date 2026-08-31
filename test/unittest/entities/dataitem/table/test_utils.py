from unittest.mock import Mock

import digitalhub.entities.dataitem.table.utils as table_utils


def test_read_data_sample_dispatches_source_list_by_first_path(monkeypatch) -> None:
    source = ["first.csv", "second.csv"]
    reader = Mock()
    reader.get_limit_arg_name.return_value = "n_rows"
    store = Mock()
    store.read_df.return_value = "dataframe"
    get_store = Mock(return_value=store)
    monkeypatch.setattr(table_utils, "get_reader_by_engine", Mock(return_value=reader))
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
