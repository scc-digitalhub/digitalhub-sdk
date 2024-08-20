from __future__ import annotations

import typing

from digitalhub_core.context.builder import check_context
from digitalhub_core.entities._base.crud import delete_entity_api_ctx, list_entity_api_ctx, read_entity_api_ctx
from digitalhub_core.entities.entity_types import EntityTypes
from digitalhub_core.entities.run.builder import run_from_dict, run_from_parameters
from digitalhub_core.utils.exceptions import EntityError
from digitalhub_core.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub_core.entities.run.entity import Run


ENTITY_TYPE = EntityTypes.RUN.value


def new_run(
    project: str,
    task: str,
    kind: str,
    uuid: str | None = None,
    labels: list[str] | None = None,
    local_execution: bool = False,
    **kwargs,
) -> Run:
    """
    Create run.

    Parameters
    ----------
    project : str
        Project name.
    task : str
        Name of the task associated with the run.
    kind : str
        Kind the object.
    uuid : str
        ID of the object (UUID4).
    labels : list[str]
        List of labels.
    local_execution : bool
        Flag to determine if object has local execution.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Run
        Run object.
    """
    check_context(project)
    obj = run_from_parameters(
        project=project,
        task=task,
        kind=kind,
        uuid=uuid,
        labels=labels,
        local_execution=local_execution,
        **kwargs,
    )
    obj.save()
    return obj


def get_run(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    **kwargs,
) -> Run:
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
    Run
        Object instance.
    """
    if not identifier.startswith("store://"):
        raise EntityError("Run has no name. Use key instead.")
    obj = read_entity_api_ctx(
        identifier,
        ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )
    return run_from_dict(obj)


def import_run(file: str) -> Run:
    """
    Get object from file.

    Parameters
    ----------
    file : str
        Path to the file.

    Returns
    -------
    Run
        Object instance.
    """
    obj: dict = read_yaml(file)
    return run_from_dict(obj)


def delete_run(
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
        Entity key or name.
    project : str
        Project name.
    entity_id : str
        Entity ID.
    delete_all_versions : bool
        Delete all versions of the named entity.
        Use entity name instead of entity key as identifier.
    cascade : bool
        Cascade delete.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    dict
        Response from backend.
    """
    if not identifier.startswith("store://"):
        raise EntityError("Run has no name. Use key instead.")
    return delete_entity_api_ctx(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
        **kwargs,
    )


def update_run(entity: Run) -> Run:
    """
    Update object in backend.

    Parameters
    ----------
    entity : Run
        The object to update.

    Returns
    -------
    Run
        Entity updated.
    """
    return entity.save(update=True)


def list_runs(project: str, **kwargs) -> list[Run]:
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
    list[Run]
        List of runs.
    """
    objs = list_entity_api_ctx(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )
    return [run_from_dict(obj) for obj in objs]
