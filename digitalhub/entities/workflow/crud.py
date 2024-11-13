from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._operations.processor import processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.workflow._base.entity import Workflow


ENTITY_TYPE = EntityTypes.WORKFLOW.value


def new_workflow(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    **kwargs,
) -> Workflow:
    """
    Create a new object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
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
    Workflow
        Object instance.

    Examples
    --------
    >>> obj = new_function(project="my-project",
    >>>                    name="my-workflow",
    >>>                    kind="kfp",
    >>>                    code_src="pipeline.py",
    >>>                    handler="pipeline-handler")
    """
    return processor.create_context_entity(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        **kwargs,
    )


def get_workflow(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    **kwargs,
) -> Workflow:
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
    Workflow
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_workflow("store://my-workflow-key")

    Using entity name:
    >>> obj = get_workflow("my-workflow-name"
    >>>                    project="my-project",
    >>>                    entity_id="my-workflow-id")
    """
    return processor.read_context_entity(
        identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        **kwargs,
    )


def get_workflow_versions(
    identifier: str,
    project: str | None = None,
    **kwargs,
) -> list[Workflow]:
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
    list[Workflow]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> obj = get_workflow_versions("store://my-workflow-key")

    Using entity name:
    >>> obj = get_workflow_versions("my-workflow-name"
    >>>                             project="my-project")
    """
    return processor.read_context_entity_versions(
        identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        **kwargs,
    )


def list_workflows(project: str, **kwargs) -> list[Workflow]:
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
    list[Workflow]
        List of object instances.

    Examples
    --------
    >>> objs = list_workflows(project="my-project")
    """
    return processor.list_context_entities(
        project=project,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def import_workflow(file: str) -> Workflow:
    """
    Import object from a YAML file and create a new object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Workflow
        Object instance.

    Examples
    --------
    >>> obj = import_workflow("my-workflow.yaml")
    """
    return processor.import_executable_entity(file)


def load_workflow(file: str) -> Workflow:
    """
    Load object from a YAML file and update an existing object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Workflow
        Object instance.

    Examples
    --------
    >>> obj = load_workflow("my-workflow.yaml")
    """
    return processor.load_executable_entity(file)


def update_workflow(entity: Workflow) -> Workflow:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Workflow
        Object to update.

    Returns
    -------
    Workflow
        Entity updated.

    Examples
    --------
    >>> obj = update_workflow(obj)
    """
    return processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_workflow(
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
    >>> obj = delete_workflow("store://my-workflow-key")

    Otherwise:
    >>> obj = delete_workflow("workflow-name",
    >>>                       project="my-project",
    >>>                       delete_all_versions=True)
    """
    return processor.delete_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
        **kwargs,
    )
