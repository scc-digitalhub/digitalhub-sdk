# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._processors.processors import base_crud_processor, search_processor
from digitalhub.entities.project.utils import setup_project
from digitalhub.utils.exceptions import BackendError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities.project._base.entity import Project


ENTITY_TYPE = EntityTypes.PROJECT.value


def new_project(
    name: str,
    description: str | None = None,
    labels: list[str] | None = None,
    config: dict | None = None,
    source: str | None = None,
    setup_kwargs: dict | None = None,
    extensions: list[dict] | None = None,
) -> Project:
    """
    Create a new project entity.

    Parameters
    ----------
    name : str
        Project name.
    description : str, optional
        Human-readable project description.
    labels : list[str], optional
        Project labels.
    config : dict, optional
        DHCore environment configuration.
    source : str, optional
        Local project context folder. Defaults to the current directory.
    setup_kwargs : dict, optional
        Keyword arguments passed to ``setup_project``.
    extensions : list[dict], optional
        Extensions to apply to the project.

    Returns
    -------
    Project
        Created project entity.
    """
    if source is None:
        source = "./"
    obj = base_crud_processor.create_project_entity(
        name=name,
        kind=EntityKinds.PROJECT_PROJECT.value,
        description=description,
        labels=labels,
        config=config,
        source=source,
        extensions=extensions,
    )
    return setup_project(obj, setup_kwargs)


def get_project(
    name: str,
    setup_kwargs: dict | None = None,
) -> Project:
    """
    Get a project entity from the backend.

    Parameters
    ----------
    name : str
        Project name.
    setup_kwargs : dict, optional
        Keyword arguments passed to ``setup_project``.

    Returns
    -------
    Project
        Retrieved project entity.
    """
    obj = base_crud_processor.read_project_entity(
        entity_type=ENTITY_TYPE,
        entity_name=name,
    )
    return setup_project(obj, setup_kwargs)


def import_project(
    file: str,
    setup_kwargs: dict | None = None,
    reset_id: bool = False,
) -> Project:
    """
    Import a project entity from a YAML file.

    Parameters
    ----------
    file : str
        Path to a YAML file containing the project descriptor.
    setup_kwargs : dict, optional
        Keyword arguments passed to ``setup_project``.
    reset_id : bool, default=False
        Whether to generate a new entity identifier instead of preserving the
        identifier from the imported project.

    Returns
    -------
    Project
        Imported project entity.
    """
    obj = base_crud_processor.import_project_entity(
        file=file,
        reset_id=reset_id,
    )
    return setup_project(obj, setup_kwargs)


def load_project(
    file: str,
    setup_kwargs: dict | None = None,
) -> Project:
    """
    Load a project entity from a YAML file.

    Parameters
    ----------
    file : str
        Path to a YAML file containing the project descriptor.
    setup_kwargs : dict, optional
        Keyword arguments passed to ``setup_project``.

    Returns
    -------
    Project
        Loaded project entity.
    """
    obj = base_crud_processor.load_project_entity(file=file)
    return setup_project(obj, setup_kwargs)


def list_projects() -> list[Project]:
    """
    List project entities from the backend.

    Returns
    -------
    list[Project]
        Project entities in the backend.
    """
    return base_crud_processor.list_project_entities(ENTITY_TYPE)


def get_or_create_project(
    name: str,
    description: str | None = None,
    labels: list[str] | None = None,
    config: dict | None = None,
    context: str | None = None,
    setup_kwargs: dict | None = None,
    extensions: list[dict] | None = None,
) -> Project:
    """
    Get a project entity or create it if it does not exist.

    Parameters
    ----------
    name : str
        Project name.
    description : str, optional
        Human-readable project description used when creating the project.
    labels : list[str], optional
        Project labels used when creating the project.
    config : dict, optional
        DHCore environment configuration.
    context : str, optional
        Local project context folder used when creating the project.
    setup_kwargs : dict, optional
        Keyword arguments passed to ``setup_project``.
    extensions : list[dict], optional
        Extensions to apply when creating the project.

    Returns
    -------
    Project
        Retrieved or created project entity.
    """
    try:
        return get_project(
            name,
            setup_kwargs=setup_kwargs,
        )
    except BackendError:
        return new_project(
            name,
            description=description,
            labels=labels,
            config=config,
            setup_kwargs=setup_kwargs,
            source=context,
            extensions=extensions,
        )


def update_project(entity: Project) -> Project:
    """
    Update a project entity.

    Parameters
    ----------
    entity : Project
        Entity to update. The entity specification is immutable.

    Returns
    -------
    Project
        Updated project entity.
    """
    return base_crud_processor.update_project_entity(
        entity_type=entity.ENTITY_TYPE,
        entity_name=entity.name,
        entity_dict=entity.to_dict(),
    )


def delete_project(
    name: str,
    cascade: bool = True,
    clean_context: bool = True,
) -> dict:
    """
    Delete a project entity.

    Parameters
    ----------
    name : str
        Project name.
    cascade : bool, default=True
        Whether to request cascade deletion from the backend.
    clean_context : bool, default=True
        Whether to delete the project's local context.

    Returns
    -------
    dict
        Response data from the backend.
    """
    return base_crud_processor.delete_project_entity(
        entity_type=ENTITY_TYPE,
        entity_name=name,
        cascade=cascade,
        clean_context=clean_context,
    )


def search_entity(
    project_name: str,
    query: str | None = None,
    entity_types: list[str] | None = None,
    name: str | None = None,
    kind: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
) -> tuple[list[ContextEntity], list[dict]]:
    """
    Search project entities in the backend.

    The result includes both existing and deleted entities.

    Parameters
    ----------
    project_name : str
        Project name.
    query : str, optional
        Search query.
    entity_types : list[str], optional
        Entity types used to filter results.
    name : str, optional
        Entity name used to filter results.
    kind : str, optional
        Entity kind used to filter results.
    created : str, optional
        Entity creation date filter.
    updated : str, optional
        Entity update date filter.
    description : str, optional
        Entity description filter.
    labels : list[str], optional
        Entity labels used to filter results.

    Returns
    -------
    tuple[list[ContextEntity], list[dict]]
        A tuple containing existing entities and deleted entity records.
    """
    return search_processor.search_entity(
        project_name,
        query=query,
        entity_types=entity_types,
        name=name,
        kind=kind,
        created=created,
        updated=updated,
        description=description,
        labels=labels,
    )
