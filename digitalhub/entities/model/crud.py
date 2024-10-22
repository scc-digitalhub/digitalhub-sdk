from __future__ import annotations

import typing

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
from digitalhub.entities.utils.utils import build_log_path_from_source, eval_local_source

if typing.TYPE_CHECKING:
    from digitalhub.entities.model._base.entity import Model


ENTITY_TYPE = EntityTypes.MODEL.value


def new_model(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = True,
    path: str | None = None,
    **kwargs,
) -> Model:
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
    Model
        Object instance.

    Examples
    --------
    >>> obj = new_model(project="my-project",
    >>>                    name="my-model",
    >>>                    kind="model",
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


def log_model(
    project: str,
    name: str,
    kind: str,
    source: list[str] | str,
    path: str | None = None,
    **kwargs,
) -> Model:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    source : str
        Model location on local path.
    path : str
        Destination path of the model. If not provided, it's generated.
    **kwargs : dict
        New model spec parameters.

    Returns
    -------
    Model
        Object instance.

    Examples
    --------
    >>> obj = log_model(project="my-project",
    >>>                 name="my-model",
    >>>                 kind="model",
    >>>                 source="./local-path")
    """
    eval_local_source(source)

    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        path = build_log_path_from_source(project, ENTITY_TYPE, name, uuid, source)

    obj = new_model(project=project, name=name, kind=kind, path=path, **kwargs)
    obj.upload(source)
    return obj


def get_model(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    **kwargs,
) -> Model:
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
    Model
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_model("store://my-model-key")

    Using entity name:
    >>> obj = get_model("my-model-name"
    >>>                 project="my-project",
    >>>                 entity_id="my-model-id")
    """
    return get_material_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )


def get_model_versions(
    identifier: str,
    project: str | None = None,
    **kwargs,
) -> list[Model]:
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
    list[Model]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> objs = get_model_versions("store://my-model-key")

    Using entity name:
    >>> objs = get_model_versions("my-model-name",
    >>>                           project="my-project")
    """
    return get_material_entity_versions(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        **kwargs,
    )


def list_models(project: str, **kwargs) -> list[Model]:
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
    list[Model]
        List of object instances.

    Examples
    --------
    >>> objs = list_models(project="my-project")
    """
    return list_material_entities(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def import_model(file: str) -> Model:
    """
    Import object from a YAML file.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Model
        Object instance.

    Examples
    --------
    >>> obj = import_model("my-model.yaml")
    """
    return import_context_entity(file)


def update_model(entity: Model) -> Model:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Model
        Object to update.

    Returns
    -------
    Model
        Entity updated.

    Examples
    --------
    >>> obj = get_model("store://my-model-key")
    """
    return entity.save(update=True)


def delete_model(
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
    >>> obj = delete_model("store://my-model-key")

    Otherwise:
    >>> obj = delete_model("my-model-name",
    >>>                    project="my-project",
    >>>                    delete_all_versions=True)
    """
    return delete_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        **kwargs,
    )
