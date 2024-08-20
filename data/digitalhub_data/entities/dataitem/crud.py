from __future__ import annotations

import typing
from typing import Any

from digitalhub_core.context.builder import check_context
from digitalhub_core.entities._base.crud import (
    delete_entity_api_ctx,
    list_entity_api_ctx,
    read_entity_api_ctx,
    read_entity_api_ctx_versions,
)
from digitalhub_core.entities._builders.uuid import build_uuid
from digitalhub_core.utils.env_utils import get_s3_bucket
from digitalhub_core.utils.io_utils import read_yaml
from digitalhub_data.entities.dataitem.builder import dataitem_from_dict, dataitem_from_parameters
from digitalhub_data.entities.entity_types import EntityTypes
from digitalhub_data.readers.builder import get_reader_by_object

if typing.TYPE_CHECKING:
    from digitalhub_data.entities.dataitem.entity._base import Dataitem


ENTITY_TYPE = EntityTypes.DATAITEM.value


def new_dataitem(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = True,
    path: str | None = None,
    **kwargs,
) -> Dataitem:
    """
    Create a new object instance.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    uuid : str
        ID of the object (UUID4).
    description : str
        Description of the object (human readable).
    labels : list[str]
        List of labels.
    embedded : bool
        Flag to determine if object must be embedded in project.
    path : str
        Object path on local file system or remote storage.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Dataitem
        Object instance.
    """
    check_context(project)
    obj = dataitem_from_parameters(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        path=path,
        **kwargs,
    )
    obj.save()
    return obj


def get_dataitem(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    **kwargs,
) -> Dataitem:
    """
    Get object from backend.

    Parameters
    ----------
    identifier : str
        Entity key or name.
    project : str
        Project name.
    entity_id : str
        Entity ID.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    Dataitem
        Object instance.
    """
    obj = read_entity_api_ctx(
        identifier,
        ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )
    entity = dataitem_from_dict(obj)
    entity._get_files_info()
    return entity


def get_dataitem_versions(
    identifier: str,
    project: str | None = None,
    **kwargs,
) -> list[Dataitem]:
    """
    Get object versions from backend.

    Parameters
    ----------
    identifier : str
        Entity key or name.
    project : str
        Project name.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    list[Dataitem]
        List of object instances.
    """
    objs = read_entity_api_ctx_versions(
        identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        **kwargs,
    )
    objects = []
    for o in objs:
        entity = dataitem_from_dict(o)
        entity._get_files_info()
        objects.append(entity)
    return objects


def import_dataitem(file: str) -> Dataitem:
    """
    Import an Dataitem object from a file using the specified file path.

    Parameters
    ----------
    file : str
        Path to the file.

    Returns
    -------
    Dataitem
        Object instance.
    """
    obj: dict = read_yaml(file)
    return dataitem_from_dict(obj)


def delete_dataitem(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
    **kwargs,
) -> dict:
    """
    Delete object from backend.

    Parameters
    ----------
    identifier : str
        Entity key or name.
    project : str
        Project name.
    entity_id : str
        Entity ID.
    delete_all_versions : bool
        Delete all versions of the named entity.
        Use entity name instead of entity key as identifier.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    dict
        Response from backend.
    """
    return delete_entity_api_ctx(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        **kwargs,
    )


def update_dataitem(entity: Dataitem) -> Dataitem:
    """
    Update object in backend.

    Parameters
    ----------
    entity : Dataitem
        The object to update.

    Returns
    -------
    Dataitem
        Entity updated.
    """
    return entity.save(update=True)


def list_dataitems(project: str, **kwargs) -> list[Dataitem]:
    """
    List all objects from backend.

    Parameters
    ----------
    project : str
        Project name.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    list[Dataitem]
        List of dataitems.
    """
    objs = list_entity_api_ctx(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )
    objects = []
    for o in objs:
        entity = dataitem_from_dict(o)
        entity._get_files_info()
        objects.append(entity)
    return objects


def log_dataitem(
    project: str,
    name: str,
    kind: str,
    data: Any,
    path: str | None = None,
    extension: str | None = None,
    **kwargs,
) -> Dataitem:
    """
    Log a dataitem to the project.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    data : Any
        Dataframe to log.
    path : str
        Destination path of the dataitem. If not provided, it's generated.
    extension : str
        Extension of the dataitem.
    **kwargs : dict
        New dataitem parameters.

    Returns
    -------
    Dataitem
        Object instance.
    """
    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        path = f"s3://{get_s3_bucket()}/{project}/{ENTITY_TYPE}/{name}/{uuid}/data.parquet"

    dataitem = dataitem_from_parameters(project=project, name=name, kind=kind, path=path, **kwargs)
    if kind == "table":
        dataitem.write_df(df=data, extension=extension)
        reader = get_reader_by_object(data)
        dataitem.spec.schema = reader.get_schema(data)
        dataitem.status.preview = reader.get_preview(data)
    dataitem.save()
    return dataitem
