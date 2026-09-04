from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities.dataitem._base.crud as base_crud
import digitalhub.entities.dataitem.croissant.crud as croissant_crud
import digitalhub.entities.dataitem.crud as context_crud
import digitalhub.entities.dataitem.dataitem.crud as dataitem_crud
import digitalhub.entities.dataitem.generic.crud as generic_crud
import digitalhub.entities.dataitem.table.crud as table_crud
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes


def test_register_dataitem_delegates_to_base_with_specific_kind(monkeypatch) -> None:
    register_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(dataitem_crud, "register_base_dataitem", register_base_dataitem)

    result = dataitem_crud.register_dataitem(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        name="data",
    )

    assert result == "dataitem"
    register_base_dataitem.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        entity_kind=EntityKinds.DATAITEM_DATAITEM.value,
        name="data",
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_register_generic_dataitem_passes_dynamic_kind(monkeypatch) -> None:
    register_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(generic_crud, "register_base_dataitem", register_base_dataitem)

    result = generic_crud.register_generic_dataitem(
        project="my-project",
        kind="custom-dataitem",
        source="s3://my-bucket/data/data.csv",
    )

    assert result == "dataitem"
    register_base_dataitem.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        entity_kind="custom-dataitem",
        name=None,
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_register_base_dataitem_passes_source_as_path(monkeypatch) -> None:
    new_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(base_crud, "new_dataitem", new_dataitem)

    result = base_crud.register_base_dataitem(
        project="my-project",
        source=["s3://my-bucket/data/data.csv"],
        entity_kind=EntityKinds.DATAITEM_DATAITEM.value,
        name="data",
        format=None,
    )

    assert result == "dataitem"
    new_dataitem.assert_called_once_with(
        project="my-project",
        name="data",
        kind=EntityKinds.DATAITEM_DATAITEM.value,
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        path="s3://my-bucket/data/data.csv",
        extensions=None,
    )


@pytest.mark.parametrize(
    ("crud_module", "register_name", "entity_kind"),
    [
        (table_crud, "register_table", EntityKinds.DATAITEM_TABLE.value),
        (croissant_crud, "register_croissant", EntityKinds.DATAITEM_CROISSANT.value),
    ],
)
def test_register_dataitem_specialized_delegates_to_base(crud_module, register_name, entity_kind, monkeypatch) -> None:
    register_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(crud_module, "register_base_dataitem", register_base_dataitem)

    result = getattr(crud_module, register_name)(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        name="data",
    )

    assert result == "dataitem"
    expected_kwargs = {
        "project": "my-project",
        "source": "s3://my-bucket/data/data.csv",
        "entity_kind": entity_kind,
        "name": "data",
        "uuid": None,
        "version": None,
        "description": None,
        "labels": None,
        "embedded": False,
        "extensions": None,
    }
    if register_name == "register_table":
        expected_kwargs["schema"] = None
    register_base_dataitem.assert_called_once_with(**expected_kwargs)


def test_new_dataitem_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="dataitem")
    monkeypatch.setattr(base_crud.crud_processor, "create_context_entity", create_entity)

    result = base_crud.new_dataitem(
        project="my-project",
        name="data",
        kind="custom-dataitem",
        uuid="data-id",
        version="1",
        description="A dataitem",
        labels=["raw"],
        embedded=True,
        path="s3://bucket/data.csv",
        extensions=[{"key": "value"}],
        format="csv",
    )

    assert result == "dataitem"
    create_entity.assert_called_once_with(
        project="my-project",
        name="data",
        kind="custom-dataitem",
        uuid="data-id",
        version="1",
        description="A dataitem",
        labels=["raw"],
        embedded=True,
        entity_type=EntityTypes.DATAITEM.value,
        path="s3://bucket/data.csv",
        extensions=[{"key": "value"}],
        format="csv",
    )


def test_log_base_dataitem_validates_source_and_builds_storage_kwargs(monkeypatch) -> None:
    eval_source = Mock()
    build_name = Mock(return_value="inferred-data")
    build_kwargs = Mock(return_value={"path": "s3://bucket/data.csv", "format": "csv"})
    log_entity = Mock(return_value="dataitem")
    monkeypatch.setattr(base_crud, "eval_local_source", eval_source)
    monkeypatch.setattr(base_crud, "build_log_name_from_source", build_name)
    monkeypatch.setattr(base_crud, "build_log_kwargs", build_kwargs)
    monkeypatch.setattr(base_crud.material_processor, "log_material_entity", log_entity)

    source = ["./data.csv"]
    result = base_crud.log_base_dataitem(
        project="my-project",
        kind="custom-dataitem",
        source=source,
        drop_existing=True,
        path="s3://bucket/data.csv",
        version="1",
        description="A dataitem",
        labels=["raw"],
        format="csv",
    )

    assert result == "dataitem"
    eval_source.assert_called_once_with(source)
    build_name.assert_called_once_with(source)
    build_kwargs.assert_called_once_with(
        "my-project",
        "inferred-data",
        entity_type=EntityTypes.DATAITEM.value,
        source=source,
        path="s3://bucket/data.csv",
        format="csv",
    )
    log_entity.assert_called_once_with(
        source=source,
        project="my-project",
        name="inferred-data",
        kind="custom-dataitem",
        drop_existing=True,
        entity_type=EntityTypes.DATAITEM.value,
        version="1",
        description="A dataitem",
        labels=["raw"],
        path="s3://bucket/data.csv",
        format="csv",
    )


def test_log_generic_dataitem_delegates_to_base(monkeypatch) -> None:
    log_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(generic_crud, "log_base_dataitem", log_base_dataitem)

    result = generic_crud.log_generic_dataitem(
        project="my-project",
        kind="custom-dataitem",
        source="./data.csv",
        name="data",
        drop_existing=True,
        path="s3://bucket/data.csv",
        version="1",
        description="A dataitem",
        labels=["raw"],
        format="csv",
    )

    assert result == "dataitem"
    log_base_dataitem.assert_called_once_with(
        project="my-project",
        name="data",
        kind="custom-dataitem",
        source="./data.csv",
        drop_existing=True,
        path="s3://bucket/data.csv",
        version="1",
        description="A dataitem",
        labels=["raw"],
        format="csv",
    )


def test_log_dataitem_warns_and_delegates_to_base(monkeypatch) -> None:
    kind_warning = Mock()
    log_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(dataitem_crud, "kind_warning", kind_warning)
    monkeypatch.setattr(dataitem_crud, "log_base_dataitem", log_base_dataitem)

    result = dataitem_crud.log_dataitem(
        project="my-project",
        source="./data.csv",
        name="data",
        kind="wrong-kind",
    )

    assert result == "dataitem"
    kind_warning.assert_called_once_with(
        requested_kind="wrong-kind",
        set_kind=EntityKinds.DATAITEM_DATAITEM.value,
        entity_type=EntityTypes.DATAITEM.value,
    )
    log_base_dataitem.assert_called_once_with(
        project="my-project",
        name="data",
        kind=EntityKinds.DATAITEM_DATAITEM.value,
        source="./data.csv",
        drop_existing=False,
        path=None,
        version=None,
        description=None,
        labels=None,
    )


@pytest.mark.parametrize(
    ("source", "data", "sql", "expected"),
    [
        ("data.csv", None, None, "source"),
        (None, object(), None, "data"),
        (None, None, "select * from data", "sql"),
    ],
)
def test_eval_source_selects_exactly_one_source(source, data, sql, expected) -> None:
    assert table_crud._eval_source(source=source, data=data, sql=sql) == expected


@pytest.mark.parametrize(
    ("source", "data", "sql"),
    [
        (None, None, None),
        ("data.csv", object(), None),
        ("data.csv", None, "select * from data"),
        (None, object(), "select * from data"),
    ],
)
def test_eval_source_rejects_zero_or_multiple_sources(source, data, sql) -> None:
    with pytest.raises(ValueError, match="Either source, data, or sql must be provided"):
        table_crud._eval_source(source=source, data=data, sql=sql)


@pytest.mark.parametrize(
    ("crud_module", "log_name", "kind"),
    [
        (table_crud, "log_table", EntityKinds.DATAITEM_TABLE.value),
        (croissant_crud, "log_croissant", EntityKinds.DATAITEM_CROISSANT.value),
    ],
)
def test_log_dataitem_specialized_delegates_to_implementation(crud_module, log_name, kind, monkeypatch) -> None:
    if log_name == "log_croissant":
        implementation = Mock(return_value="dataitem")
        dataitem = SimpleNamespace(
            metadata=SimpleNamespace(name=None, description=None, labels=None),
            save=Mock(),
        )
        implementation.return_value = dataitem
        monkeypatch.setattr(crud_module, "log_base_dataitem", implementation)
        monkeypatch.setattr(crud_module, "validate_croissant_source", Mock(return_value="metadata.json"))
        monkeypatch.setattr(crud_module, "build_croissant_kwargs", Mock(return_value={}))
        monkeypatch.setattr(crud_module, "get_croissant_dataset", Mock(return_value=object()))
        monkeypatch.setattr(crud_module, "get_files_from_croissant", Mock(return_value=[]))
        monkeypatch.setattr(crud_module, "get_metadata_fields_from_croissant", Mock(return_value=(None, None, None)))
        result = getattr(crud_module, log_name)(project="my-project", name="data", source="metadata.json")
        assert result is dataitem
        implementation.assert_called_once()
        assert implementation.call_args.kwargs["kind"] == kind
        dataitem.save.assert_called_once_with(update=True)
        return

    log_entity = Mock(return_value="dataitem")
    monkeypatch.setattr(crud_module.material_processor, "log_material_entity", log_entity)
    monkeypatch.setattr(crud_module, "read_data_sample", Mock(return_value=object()))
    monkeypatch.setattr(crud_module, "process_data_kwargs", Mock(return_value={}))
    monkeypatch.setattr(crud_module, "post_process", Mock(return_value="dataitem"))

    result = getattr(crud_module, log_name)(project="my-project", source="data.csv", name="data")

    assert result == "dataitem"
    log_entity.assert_called_once_with(
        source="data.csv",
        project="my-project",
        name="data",
        kind=kind,
        entity_type=EntityTypes.DATAITEM.value,
        drop_existing=False,
        description=None,
        labels=None,
    )


def test_update_dataitem_delegates_entity_fields(monkeypatch) -> None:
    entity = SimpleNamespace(
        project="my-project",
        ENTITY_TYPE=EntityTypes.DATAITEM.value,
        id="dataitem-id",
        to_dict=Mock(return_value={"metadata": {"name": "data"}}),
    )
    update_entity = Mock(return_value="dataitem")
    monkeypatch.setattr(context_crud.crud_processor, "update_context_entity", update_entity)

    result = context_crud.update_dataitem(entity)

    assert result == "dataitem"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.DATAITEM.value,
        entity_id="dataitem-id",
        entity_dict={"metadata": {"name": "data"}},
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_dataitem",
            "read_context_entity",
            {"identifier": "data-key", "project": "my-project", "entity_id": "data-id"},
            {
                "identifier": "data-key",
                "entity_type": EntityTypes.DATAITEM.value,
                "project": "my-project",
                "entity_id": "data-id",
            },
        ),
        (
            "get_dataitem_versions",
            "read_context_entity_versions",
            {"identifier": "data", "project": "my-project"},
            {"identifier": "data", "entity_type": EntityTypes.DATAITEM.value, "project": "my-project"},
        ),
        (
            "list_dataitems",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "data",
                "kind": "table",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.DATAITEM.value,
                "q": "query",
                "name": "data",
                "kind": "table",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "import_dataitem",
            "import_context_entity",
            {"file": "data.yaml", "key": "data-key", "reset_id": True, "context": "project"},
            {"file": "data.yaml", "key": "data-key", "reset_id": True, "context": "project"},
        ),
        ("load_dataitem", "load_context_entity", {"file": "data.yaml"}, {"file": "data.yaml"}),
    ],
)
def test_dataitem_read_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict,
    monkeypatch,
) -> None:
    processor = Mock(return_value="dataitem")
    monkeypatch.setattr(context_crud.crud_processor, processor_name, processor)

    result = getattr(context_crud, function_name)(**kwargs)

    assert result == "dataitem"
    if function_name == "import_dataitem":
        processor.assert_called_once_with(
            expected_kwargs["file"],
            expected_kwargs["key"],
            expected_kwargs["reset_id"],
            expected_kwargs["context"],
        )
    elif function_name == "load_dataitem":
        processor.assert_called_once_with(expected_kwargs["file"])
    else:
        processor.assert_called_once_with(**expected_kwargs)
