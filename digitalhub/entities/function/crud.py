from __future__ import annotations

import typing

from digitalhub.entities._base.crud import (
    delete_entity,
    get_context_entity_versions,
    get_versioned_entity,
    import_executable_entity,
    list_context_entities,
    new_context_entity,
)
from digitalhub.entities.utils.entity_types import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities.function._base.entity import Function

ENTITY_TYPE = EntityTypes.FUNCTION.value


def new_function(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    **kwargs,
) -> Function:
    """
    Create a Function instance with the given parameters.

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
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Function
        Object instance.

    Examples
    --------
    >>> obj = new_function(project="my-project",
    >>>                    name="my-function",
    >>>                    kind="python",
    >>>                    code_src="function.py",
    >>>                    handler="function-handler")
    """
    return new_context_entity(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        **kwargs,
    )


def get_function(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    **kwargs,
) -> Function:
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
    Function
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_function("store://my-function-key")

    Using entity name:
    >>> obj = get_function("my-function-name"
    >>>                    project="my-project",
    >>>                    entity_id="my-function-id")
    """
    return get_versioned_entity(
        identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )


def get_function_versions(
    identifier: str,
    project: str | None = None,
    **kwargs,
) -> list[Function]:
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
    list[Function]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> obj = get_function_versions("store://my-function-key")

    Using entity name:
    >>> obj = get_function_versions("my-function-name"
    >>>                             project="my-project")
    """
    return get_context_entity_versions(
        identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        **kwargs,
    )


def list_functions(project: str, **kwargs) -> list[Function]:
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
    list[Function]
        List of object instances.

    Examples
    --------
    >>> objs = list_functions(project="my-project")
    """
    return list_context_entities(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def import_function(file: str) -> Function:
    """
    Get object from file.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Function
        Object instance.

    Examples
    --------
    >>> obj = import_function("my-function.yaml")
    """
    return import_executable_entity(file)


def update_function(entity: Function) -> Function:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Function
        Object to update.

    Returns
    -------
    Function
        Entity updated.

    Examples
    --------
    >>> obj = update_function(obj)
    """
    return entity.save(update=True)


def delete_function(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
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
    cascade : bool
        Cascade delete.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    dict
        Response from backend.

    Examples
    --------
    If delete_all_versions is False:
    >>> obj = delete_function("store://my-function-key")

    Otherwise:
    >>> obj = delete_function("function-name",
    >>>                       project="my-project",
    >>>                       delete_all_versions=True)
    """
    return delete_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
        **kwargs,
    )