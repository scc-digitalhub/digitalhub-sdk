# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import crud_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.trigger._base.entity import Trigger


ENTITY_TYPE = EntityTypes.TRIGGER.value


def new_trigger(
    project: str,
    name: str,
    kind: str,
    task: str,
    function: str | None = None,
    workflow: str | None = None,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    template: dict | None = None,
    **kwargs,
) -> Trigger:
    """
    Create a new trigger entity in the backend.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Entity name.
    kind : str
        Entity kind.
    task : str
        Task reference.
    function : str, optional
        Function reference. Provide either ``function`` or ``workflow``.
    workflow : str, optional
        Workflow reference. Provide either ``workflow`` or ``function``. If
        both are provided, the workflow is used.
    uuid : str, optional
        Entity identifier.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    embedded : bool, default=False
        Whether to embed the entity specification in the project specification.
    template : dict, optional
        Trigger template. If omitted, a template is built from ``task`` and the
        selected executable reference.
    **kwargs : dict
        Additional entity specification parameters.

    Returns
    -------
    Trigger
        Created trigger entity.
    """
    if workflow is None:
        if function is None:
            raise ValueError("Workflow or function must be provided")
        executable_type = "function"
        executable = function
    else:
        executable_type = "workflow"
        executable = workflow

    # Prepare kwargs
    if kwargs is None:
        kwargs = {}
    kwargs["task"] = task
    kwargs[executable_type] = executable

    # Template handling
    if template is None:
        template = {}
    if not isinstance(template, dict):
        raise TypeError("Template must be a dictionary")
    template["task"] = task
    template[executable_type] = executable
    template["local_execution"] = False
    kwargs["template"] = template

    return crud_processor.create_context_entity(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def get_trigger(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> Trigger:
    """
    Get a trigger entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity name or entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``).
    project : str, optional
        Project name. Required when ``identifier`` is an entity name.
    entity_id : str, optional
        Entity identifier. If omitted, the latest version is returned.

    Returns
    -------
    Trigger
        Retrieved trigger entity.
    """
    return crud_processor.read_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
    )


def list_triggers(
    project: str,
    q: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    user: str | None = None,
    state: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    versions: str | None = None,
    task: str | None = None,
) -> list[Trigger]:
    """
    List trigger entities in a project.

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
    versions : str, optional
        Version filter. Defaults to the latest version.
    task : str, optional
        Task reference used to filter results.

    Returns
    -------
    list[Trigger]
        Trigger entities matching the filters.
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
        versions=versions,
        task=task,
    )


def import_trigger(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Trigger:
    """
    Import a trigger entity from a YAML file or entity key.

    Parameters
    ----------
    file : str, optional
        Path to a YAML file containing the entity descriptor. Provide either
        ``file`` or ``key``.
    key : str, optional
        Entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``). Provide either
        ``file`` or ``key``.
    reset_id : bool, default=False
        Whether to generate a new entity identifier instead of preserving the
        identifier from the imported entity.
    context : str, optional
        Project name used for context resolution. If omitted, the project from
        the entity descriptor is used.

    Returns
    -------
    Trigger
        Imported trigger entity.
    """
    return crud_processor.import_context_entity(file, key, reset_id, context)


def load_trigger(file: str) -> Trigger:
    """
    Load a trigger entity from a YAML file.

    Parameters
    ----------
    file : str
        Path to a YAML file containing the entity descriptor.

    Returns
    -------
    Trigger
        Loaded trigger entity. An existing entity is updated when it can be
        identified; otherwise, a new entity is created.
    """
    return crud_processor.load_context_entity(file)


def update_trigger(entity: Trigger) -> Trigger:
    """
    Update a trigger entity in the backend.

    Parameters
    ----------
    entity : Trigger
        Entity to update. The entity specification is immutable.

    Returns
    -------
    Trigger
        Updated trigger entity.
    """
    return crud_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_trigger(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> dict:
    """
    Delete a trigger entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity name or entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``).
    project : str, optional
        Project name. Required when ``identifier`` is an entity name.
    entity_id : str, optional
        Identifier of the version to delete. Required when ``identifier`` does
        not contain the version identifier.

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
    )
