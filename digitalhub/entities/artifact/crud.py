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
from digitalhub.entities.artifact._base.entity import Artifact
from digitalhub.entities.utils.entity_types import EntityTypes
from digitalhub.entities.utils.utils import build_log_path_from_source, eval_local_source

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact._base.entity import Artifact


ENTITY_TYPE = EntityTypes.ARTIFACT.value


def new_artifact(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    path: str | None = None,
    **kwargs,
) -> Artifact:
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
    Artifact
        Object instance.

    Examples
    --------
    >>> obj = new_artifact(project="my-project",
    >>>                    name="my-artifact",
    >>>                    kind="artifact",
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


def log_artifact(
    project: str,
    name: str,
    kind: str,
    source: list[str] | str,
    path: str | None = None,
    **kwargs,
) -> Artifact:
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
        Artifact location on local path.
    path : str
        Destination path of the artifact. If not provided, it's generated.
    **kwargs : dict
        New artifact spec parameters.

    Returns
    -------
    Artifact
        Object instance.

    Examples
    --------
    >>> obj = log_artifact(project="my-project",
    >>>                    name="my-artifact",
    >>>                    kind="artifact",
    >>>                    source="./local-path")
    """
    eval_local_source(source)

    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        path = build_log_path_from_source(project, ENTITY_TYPE, name, uuid, source)

    obj = new_artifact(project=project, name=name, kind=kind, path=path, **kwargs)
    obj.upload(source)
    return obj


def get_artifact(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    **kwargs,
) -> Artifact:
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
    Artifact
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_artifact("store://my-artifact-key")

    Using entity name:
    >>> obj = get_artifact("my-artifact-name"
    >>>                    project="my-project",
    >>>                    entity_id="my-artifact-id")
    """
    return get_material_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )


def get_artifact_versions(
    identifier: str,
    project: str | None = None,
    **kwargs,
) -> list[Artifact]:
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
    list[Artifact]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> obj = get_artifact_versions("store://my-artifact-key")

    Using entity name:
    >>> obj = get_artifact_versions("my-artifact-name"
    >>>                             project="my-project")
    """
    return get_material_entity_versions(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        **kwargs,
    )


def list_artifacts(project: str, **kwargs) -> list[Artifact]:
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
    list[Artifact]
        List of object instances.

    Examples
    --------
    >>> objs = list_artifacts(project="my-project")
    """
    return list_material_entities(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def import_artifact(file: str) -> Artifact:
    """
    Import object from a YAML file.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Artifact
        Object instance.

    Examples
    --------
    >>> obj = import_artifact("my-artifact.yaml")
    """
    return import_context_entity(file)


def update_artifact(entity: Artifact) -> Artifact:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Artifact
        Object to update.

    Returns
    -------
    Artifact
        Entity updated.

    Examples
    --------
    >>> obj = update_artifact(obj)
    """
    return entity.save(update=True)


def delete_artifact(
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
    >>> delete_artifact("store://my-artifact-key")

    Otherwise:
    >>> delete_artifact("my-artifact-name",
    >>>                  project="my-project",
    >>>                  delete_all_versions=True)
    """
    return delete_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        **kwargs,
    )
