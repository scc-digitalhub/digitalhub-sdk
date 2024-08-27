from __future__ import annotations

import typing

from digitalhub_core.context.builder import check_context
from digitalhub_core.entities._base.crud import (
    delete_entity_api_ctx,
    list_entity_api_ctx,
    read_entity_api_ctx,
    read_entity_api_ctx_versions,
)
from digitalhub_core.entities.entity_types import EntityTypes
from digitalhub_core.entities.function.builder import function_from_dict, function_from_parameters
from digitalhub_core.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub_core.entities.function.entity import Function

ENTITY_TYPE = EntityTypes.FUNCTION.value


def new_function(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = True,
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
        ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
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
    check_context(project)
    obj = function_from_parameters(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        **kwargs,
    )
    obj.save()
    return obj


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
    obj = read_entity_api_ctx(
        identifier,
        ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )
    return function_from_dict(obj)


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
    obj = read_entity_api_ctx_versions(
        identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        **kwargs,
    )
    return [function_from_dict(o) for o in obj]


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
    objs = list_entity_api_ctx(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )
    return [function_from_dict(obj) for obj in objs]


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
    obj = read_yaml(file)
    if isinstance(obj, list):
        func_dict = obj[0]
        task_dicts = obj[1:]
    else:
        func_dict = obj
        task_dicts = []
    check_context(func_dict.get("project"))
    func = function_from_dict(func_dict)
    func.import_tasks(task_dicts)
    return func


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
    return delete_entity_api_ctx(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
        **kwargs,
    )
