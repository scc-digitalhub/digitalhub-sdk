# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import crud_processor, executable_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.function._base.entity import Function

ENTITY_TYPE = EntityTypes.FUNCTION.value


def new_function(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    **kwargs,
) -> Function:
    """
    Create a new function entity in the backend.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Entity name.
    kind : str
        Entity kind.
    uuid : str, optional
        Entity identifier.
    version : str, optional
        Entity version.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    embedded : bool, default=False
        Whether to embed the entity specification in the project specification.
    **kwargs : dict
        Additional entity specification parameters.

    Returns
    -------
    Function
        Created function entity.
    """
    return crud_processor.create_context_entity(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )


def get_function(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> Function:
    """
    Get a function entity from the backend.

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
    Function
        Retrieved function entity.
    """
    return crud_processor.read_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
    )


def get_function_versions(
    identifier: str,
    project: str | None = None,
) -> list[Function]:
    """
    Get all versions of a function entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity name or entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``).
    project : str, optional
        Project name. Required when ``identifier`` is an entity name.

    Returns
    -------
    list[Function]
        All versions of the function entity.
    """
    return crud_processor.read_context_entity_versions(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
    )


def list_functions(
    project: str,
    q: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    user: str | None = None,
    state: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    versions: str | None = None,
) -> list[Function]:
    """
    List function entities in a project.

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

    Returns
    -------
    list[Function]
        Function entities matching the filters.
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
    )


def import_function(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Function:
    """
    Import a function entity from a YAML file or entity key.

    Parameters
    ----------
    file : str, optional
        Path to a YAML file containing the entity descriptor. Provide either
        ``file`` or ``key``.
    key : str, optional
        Entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``). Provide
        either ``file`` or ``key``.
    reset_id : bool, default=False
        Whether to generate a new entity identifier instead of preserving the
        identifier from the imported entity.
    context : str, optional
        Project name used for context resolution. If omitted, the project from
        the entity descriptor is used.

    Returns
    -------
    Function
        Imported function entity.
    """
    return executable_processor.import_executable_entity(file, key, reset_id, context)


def load_function(file: str) -> Function:
    """
    Load a function entity from a YAML file.

    Parameters
    ----------
    file : str
        Path to a YAML file containing the entity descriptor.

    Returns
    -------
    Function
        Loaded function entity. An existing entity is updated when it can be
        identified; otherwise, a new entity is created.
    """
    return executable_processor.load_executable_entity(file)


def update_function(entity: Function) -> Function:
    """
    Update a function entity in the backend.

    Parameters
    ----------
    entity : Function
        Entity to update. The entity specification is immutable.

    Returns
    -------
    Function
        Updated function entity.
    """
    return crud_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_function(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
) -> dict:
    """
    Delete one or more versions of a function entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity name or entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``). Use an entity name
        when ``delete_all_versions`` is True.
    project : str, optional
        Project name. Required when ``identifier`` is an entity name.
    entity_id : str, optional
        Identifier of the version to delete. Required when
        ``delete_all_versions`` is False and ``identifier`` does not contain
        the version identifier.
    delete_all_versions : bool, default=False
        Whether to delete all versions of the named entity. When False, only
        one version is deleted.
    cascade : bool, default=True
        Whether to request cascade deletion from the backend.

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
        delete_all_versions=delete_all_versions,
        cascade=cascade,
    )
