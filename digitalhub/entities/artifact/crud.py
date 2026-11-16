# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.crud_factory import ContextEntityCRUD
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import crud_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact._base.entity import Artifact


_crud: ContextEntityCRUD[Artifact] = ContextEntityCRUD(EntityTypes.ARTIFACT.value, crud_processor=crud_processor)


def get_artifact(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> Artifact:
    """
    Get an artifact entity from the backend.

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
    Artifact
        Retrieved artifact entity.

    Examples
    --------
    Retrieve the latest version by name and project, or by entity key:

    ```python
    import digitalhub as dh

    artifact = dh.get_artifact("my-artifact", "my-project")
    artifact = dh.get_artifact("store://my-project/artifact/artifact/my-artifact:123e4567-e89b-42d3-a456-426614174000")
    ```
    """
    return _crud.get(identifier, project, entity_id)


def get_artifact_versions(
    identifier: str,
    project: str | None = None,
) -> list[Artifact]:
    """
    Get all versions of an artifact entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity name or entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``).
    project : str, optional
        Project name. Required when ``identifier`` is an entity name.

    Returns
    -------
    list[Artifact]
        All versions of the artifact entity.

    Examples
    --------
    Retrieve all versions by name and project, or by entity key:

    ```python
    import digitalhub as dh

    artifacts = dh.get_artifact_versions("my-artifact", "my-project")
    artifacts = dh.get_artifact_versions(
        "store://my-project/artifact/artifact/my-artifact:123e4567-e89b-42d3-a456-426614174000"
    )
    ```
    """
    return _crud.get_versions(identifier, project)


def list_artifacts(
    project: str,
    q: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    labels: list[str] | None = None,
    user: str | None = None,
    state: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    versions: str | None = None,
) -> list[Artifact]:
    """
    List artifact entities in a project.

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
    labels : list[str], optional
        Labels used to filter results.
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
    list[Artifact]
        Artifact entities matching the filters.

    Examples
    --------
    List artifacts in a project:

    ```python
    import digitalhub as dh

    artifacts = dh.list_artifacts(project="my-project")
    ```
    """
    return _crud.list(
        project,
        q=q,
        name=name,
        kind=kind,
        labels=labels,
        user=user,
        state=state,
        created=created,
        updated=updated,
        versions=versions,
    )


def import_artifact(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Artifact:
    """
    Import an artifact entity from a YAML file or entity key.

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
    Artifact
        Imported artifact entity.

    Examples
    --------
    Import an artifact from a YAML file or entity key:

    ```python
    import digitalhub as dh

    artifact = dh.import_artifact(file="my-artifact.yaml")
    artifact = dh.import_artifact(
        key="store://my-project/artifact/artifact/my-artifact:123e4567-e89b-42d3-a456-426614174000"
    )
    ```
    """
    return _crud.import_entity(file, key, reset_id, context)


def load_artifact(file: str) -> Artifact:
    """
    Load an artifact entity from a YAML file.

    Parameters
    ----------
    file : str
        Path to a YAML file containing the entity descriptor.

    Returns
    -------
    Artifact
        Loaded artifact entity. An existing entity is updated when it can be
        identified; otherwise, a new entity is created.

    Examples
    --------
    Load an artifact descriptor from a YAML file:

    ```python
    import digitalhub as dh

    artifact = dh.load_artifact("my-artifact.yaml")
    ```
    """
    return _crud.load(file)


def update_artifact(entity: Artifact) -> Artifact:
    """
    Update an artifact entity in the backend.

    Parameters
    ----------
    entity : Artifact
        Entity to update. The entity specification is immutable.

    Returns
    -------
    Artifact
        Updated artifact entity.

    Examples
    --------
    Update an artifact after changing its mutable metadata:

    ```python
    import digitalhub as dh

    artifact = dh.get_artifact("my-artifact", "my-project")
    artifact.set_description("Updated artifact")
    artifact = dh.update_artifact(artifact)
    ```
    """
    return _crud.update(entity)


def delete_artifact(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
) -> dict:
    """
    Delete one or more versions of an artifact entity from the backend.

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

    Examples
    --------
    Delete a version by key, or delete all versions by name and project:

    ```python
    import digitalhub as dh

    dh.delete_artifact("store://my-project/artifact/artifact/my-artifact:123e4567-e89b-42d3-a456-426614174000")
    dh.delete_artifact("my-artifact", "my-project", delete_all_versions=True)
    ```
    """
    return _crud.delete(
        identifier,
        project,
        entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
    )
