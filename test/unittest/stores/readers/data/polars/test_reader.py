from unittest.mock import Mock

import pytest


@pytest.mark.parametrize(
    ("schema", "target_table"),
    [
        ("analytics", "analytics.items"),
        (None, "items"),
    ],
)
def test_write_table_uses_schema_in_target_table_name(schema: str | None, target_table: str) -> None:
    pytest.importorskip("polars")
    from digitalhub.stores.readers.data.polars.reader import DataframeReaderPolars

    dataframe = Mock()
    engine = Mock()

    DataframeReaderPolars.write_table(dataframe, "items", engine, schema=schema, if_exists="replace")

    dataframe.write_database.assert_called_once_with(
        table_name=target_table,
        connection=engine,
        if_table_exists="replace",
    )
