from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities.dataitem.table.crud as table_crud
import digitalhub.entities.dataitem.table.processor as table_processor_module
from digitalhub.entities._processors.context.material import ContextEntityMaterialProcessor
from digitalhub.entities.dataitem.table.processor import DataitemTableProcessor


def test_log_table_writes_the_dataframe_as_parquet_through_the_table_processor(monkeypatch) -> None:
    entity = Mock()

    def log_entity_with_upload(upload_fn, **kwargs):
        upload_fn(entity)
        return entity

    monkeypatch.setattr(table_crud, "process_data_kwargs", Mock(return_value={}))
    monkeypatch.setattr(table_crud, "post_process", lambda obj, data: obj)
    monkeypatch.setattr(ContextEntityMaterialProcessor, "log_entity_with_upload", staticmethod(log_entity_with_upload))
    write_df = Mock()
    monkeypatch.setattr(DataitemTableProcessor, "write_df", write_df)

    assert table_crud.log_table("project", data="df", name="table") is entity

    write_df.assert_called_once_with(entity, "df", extension="parquet")
    entity.write_df.assert_not_called()


def test_write_df_records_the_written_file(monkeypatch) -> None:
    # log_table(data=df) used to write the file without recording it, so
    # the dataitem had no status.files, unlike log_table(source=...).
    store = Mock()
    store.write_df.return_value = "s3://bucket/project/table.parquet"
    store.get_file_info.return_value = [{"path": "table.parquet", "size": 10}]
    monkeypatch.setattr(table_processor_module, "get_store", Mock(return_value=store))
    dataitem = SimpleNamespace(
        project="project",
        spec=SimpleNamespace(path="s3://bucket/project/table.parquet"),
        status=SimpleNamespace(files=None),
    )

    written = DataitemTableProcessor().write_df(dataitem, "df", extension="parquet")

    store.write_df.assert_called_once_with("df", "s3://bucket/project/table.parquet", extension="parquet")
    store.get_file_info.assert_called_once_with(
        "s3://bucket/project/table.parquet", [("s3://bucket/project/table.parquet", "table.parquet")]
    )
    assert written == "s3://bucket/project/table.parquet"
    assert dataitem.status.files == [{"path": "table.parquet", "size": 10}]
