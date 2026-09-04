# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import crud_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


ENTITY_TYPE = EntityTypes.RUN.value


def new_run(
    project: str,
    kind: str,
    uuid: str | None = None,
    name: str | None = None,
    labels: list[str] | None = None,
    task: str | None = None,
    **kwargs,
) -> Run:
    """
    Create a new run entity in the backend.

    Parameters
    ----------
    project : str
        Project name.
    kind : str
        Entity kind.
    uuid : str, optional
        Entity identifier.
    name : str, optional
        Entity name.
    labels : list[str], optional
        Entity labels.
    task : str, optional
        Task reference associated with the run.
    **kwargs : dict
        Additional entity specification parameters.

    Returns
    -------
    Run
        Created run entity.
    """
    return crud_processor.create_context_entity(
        project=project,
        kind=kind,
        uuid=uuid,
        name=name,
        labels=labels,
        task=task,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def get_run(
    identifier: str,
    project: str | None = None,
) -> Run:
    """
    Get an unversioned run entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity ID or entity key in the format
        ``store://<project>/<entity_type>/<kind>/<uuid>``.
    project : str, optional
        Project name. Required when ``identifier`` is an entity ID.

    Returns
    -------
    Run
        Retrieved run entity.
    """
    return crud_processor.read_unversioned_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
    )


def list_runs(
    project: str,
    q: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    user: str | None = None,
    state: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    function: str | None = None,
    workflow: str | None = None,
    task: str | None = None,
    action: str | None = None,
) -> list[Run]:
    """
    List run entities in a project.

    Parameters
    ----------
    project : str
        Project name.
    q : str, optional
        Query string used to filter entities.
    name : str, optional
        Entity name used to filter results.
    kind : str, optional
        Entity kind used to filter results.
    user : str, optional
        User who created the entity.
    state : str, optional
        Entity state used to filter results.
    created : str, optional
        Creation date filter.
    updated : str, optional
        Update date filter.
    function : str, optional
        Function reference used to filter results.
    workflow : str, optional
        Workflow reference used to filter results.
    task : str, optional
        Task reference used to filter results.
    action : str, optional
        Action name used to filter results.

    Returns
    -------
    list[Run]
        Run entities matching the filters.
    """
    return crud_processor.list_context_entities(
        project=project,
        entity_type=ENTITY_TYPE,
        q=q,
        name=name,
        kind=kind,
        user=user,
        state=state,
        created=created,
        updated=updated,
        function=function,
        workflow=workflow,
        task=task,
        action=action,
    )


def import_run(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Run:
    """
    Import a run entity from a YAML file or entity key.

    Parameters
    ----------
    file : str, optional
        Path to a YAML file containing the entity descriptor. Provide either
        ``file`` or ``key``.
    key : str, optional
        Entity key in the format
        ``store://<project>/<entity_type>/<kind>/<uuid>``. Provide either
        ``file`` or ``key``.
    reset_id : bool, default=False
        Whether to generate a new entity identifier instead of preserving the
        identifier from the imported entity.
    context : str, optional
        Project name used for context resolution. If omitted, the project from
        the entity descriptor is used.

    Returns
    -------
    Run
        Imported run entity.
    """
    return crud_processor.import_context_entity(file, key, reset_id, context)


def load_run(file: str) -> Run:
    """
    Load a run entity from a YAML file.

    Parameters
    ----------
    file : str
        Path to a YAML file containing the entity descriptor.

    Returns
    -------
    Run
        Loaded run entity. An existing entity is updated when it can be
        identified; otherwise, a new entity is created.
    """
    return crud_processor.load_context_entity(file)


def update_run(entity: Run) -> Run:
    """
    Update a run entity in the backend.

    Parameters
    ----------
    entity : Run
        Entity to update. The entity specification is immutable.

    Returns
    -------
    Run
        Updated run entity.
    """
    return crud_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_run(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> dict:
    """
    Delete an unversioned run entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity ID or entity key in the format
        ``store://<project>/<entity_type>/<kind>/<uuid>``.
    project : str, optional
        Project name. Required when ``identifier`` is an entity ID.
    entity_id : str, optional
        Identifier of the entity to delete. If omitted, ``identifier`` is
        used.

    Returns
    -------
    dict
        Response data from the backend.
    """
    return crud_processor.delete_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        unversioned=True,
    )
