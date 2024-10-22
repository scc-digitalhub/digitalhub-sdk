from __future__ import annotations

import typing
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from digitalhub.entities._base.crud import (
    delete_entity,
    get_material_entity,
    get_material_entity_versions,
    import_context_entity,
    list_material_entities,
    new_context_entity,
)
from digitalhub.entities._base.entity._constructors.uuid import build_uuid
from digitalhub.entities.utils.entity_types import EntityTypes
from digitalhub.entities.utils.utils import build_log_path_from_filename, build_log_path_from_source, eval_local_source
from digitalhub.factory.api import build_entity_from_params
from digitalhub.readers.api import get_reader_by_object
from digitalhub.stores.api import get_store
from digitalhub.utils.generic_utils import slugify_string

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem


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
    Create a new object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    uuid : str
        ID of the object.
    description : str
        Description of the object (human readable).
    labels : list[str]
        List of labels.
    embedded : bool
        Flag to determine if object spec must be embedded in project spec.
    path : str
        Object path on local file system or remote storage. It is also the destination path of upload() method.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = new_dataitem(project="my-project",
    >>>                    name="my-dataitem",
    >>>                    kind="dataitem",
    >>>                    path="s3://my-bucket/my-key")
    """
    return new_context_entity(
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


def log_dataitem(
    project: str,
    name: str,
    kind: str,
    source: list[str] | str | None = None,
    data: Any | None = None,
    extension: str | None = None,
    path: str | None = None,
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
    source : str
        Dataitem location on local path.
    data : Any
        Dataframe to log. Alternative to source.
    extension : str
        Extension of the output dataframe.
    path : str
        Destination path of the dataitem. If not provided, it's generated.
    **kwargs : dict
        New dataitem spec parameters.

    Returns
    -------
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = log_dataitem(project="my-project",
    >>>                    name="my-dataitem",
    >>>                    kind="table",
    >>>                    data=df)
    """
    if (source is None) == (data is None):
        raise ValueError("You must provide source or data.")

    # Case where source is provided
    if source is not None:
        eval_local_source(source)

        if path is None:
            uuid = build_uuid()
            kwargs["uuid"] = uuid
            path = build_log_path_from_source(project, ENTITY_TYPE, name, uuid, source)

        obj = new_dataitem(project=project, name=name, kind=kind, path=path, **kwargs)
        obj.upload(source)

    # Case where data is provided
    else:
        extension = extension if extension is not None else "parquet"
        if path is None:
            uuid = build_uuid()
            kwargs["uuid"] = uuid
            slug = slugify_string(name) + f".{extension}"
            path = build_log_path_from_filename(project, ENTITY_TYPE, name, uuid, slug)

        obj = build_entity_from_params(project=project, name=name, kind=kind, path=path, **kwargs)
        if kind == "table":
            dst = obj.write_df(df=data, extension=extension)
            reader = get_reader_by_object(data)
            obj.spec.schema = reader.get_schema(data)
            obj.status.preview = reader.get_preview(data)
            store = get_store(obj.spec.path)
            src = Path(urlparse(obj.spec.path).path).name
            paths = [(dst, src)]
            infos = store.get_file_info(paths)
            obj.status.add_files_info(infos)
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
        Entity key (store://...) or entity name.
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

    Examples
    --------
    Using entity key:
    >>> obj = get_dataitem("store://my-dataitem-key")

    Using entity name:
    >>> obj = get_dataitem("my-dataitem-name"
    >>>                    project="my-project",
    >>>                    entity_id="my-dataitem-id")
    """
    return get_material_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )


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
        Entity key (store://...) or entity name.
    project : str
        Project name.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    list[Dataitem]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> objs = get_dataitem_versions("store://my-dataitem-key")

    Using entity name:
    >>> objs = get_dataitem_versions("my-dataitem-name",
    >>>                              project="my-project")
    """
    return get_material_entity_versions(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        **kwargs,
    )


def list_dataitems(project: str, **kwargs) -> list[Dataitem]:
    """
    List all latest version objects from backend.

    Parameters
    ----------
    project : str
        Project name.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    list[Dataitem]
        List of object instances.

    Examples
    --------
    >>> objs = list_dataitems(project="my-project")
    """
    return list_material_entities(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def import_dataitem(file: str) -> Dataitem:
    """
    Import object from a YAML file.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = import_dataitem("my-dataitem.yaml")
    """
    return import_context_entity(file)


def update_dataitem(entity: Dataitem) -> Dataitem:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Dataitem
        Object to update.

    Returns
    -------
    Dataitem
        Entity updated.

    Examples
    --------
    >>> obj = update_dataitem(obj)
    """
    return entity.save(update=True)


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
        Entity key (store://...) or entity name.
    project : str
        Project name.
    entity_id : str
        Entity ID.
    delete_all_versions : bool
        Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    dict
        Response from backend.

    Examples
    --------
    If delete_all_versions is False:
    >>> obj = delete_dataitem("store://my-dataitem-key")

    Otherwise:
    >>> obj = delete_dataitem("my-dataitem-name",
    >>>                       project="my-project",
    >>>                       delete_all_versions=True)
    """
    return delete_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        **kwargs,
    )
