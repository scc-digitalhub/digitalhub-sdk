# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import context_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.containerimage._base.entity import Containerimage


ENTITY_TYPE = EntityTypes.CONTAINERIMAGE.value


def new_containerimage(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    image: str | None = None,
    **kwargs,
) -> Containerimage:
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
    image : str
        Image mapped to the image.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Image
        Object instance.

    Examples
    --------
    >>> obj = new_containerimage(project="my-project",
    >>>                 name="my-image",
    >>>                 kind="image",
    >>>                 image="my-image")
    """
    return context_processor.create_context_entity(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        entity_type=ENTITY_TYPE,
        image=image,
        **kwargs,
    )


def get_containerimage(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> Containerimage:
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

    Returns
    -------
    Image
        Object instance.

    Examples
    --------
    Using entity key:
    >>> obj = get_containerimage("store://my-image-key")

    Using entity name:
    >>> obj = get_containerimage("my-image-name",
    >>>                     project="my-project",
    >>>                     entity_id="my-image-id")
    """
    return context_processor.read_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
    )


def get_containerimage_versions(
    identifier: str,
    project: str | None = None,
) -> list[Containerimage]:
    """
    Get object versions from backend.

    Parameters
    ----------
    identifier : str
        Entity key (store://...) or entity name.
    project : str
        Project name.

    Returns
    -------
    list[Image]
        List of object instances.

    Examples
    --------
    Using entity key:
    >>> obj = get_containerimage_versions("store://my-image-key")

    Using entity name:
    >>> obj = get_containerimage_versions("my-image-name",
    >>>                              project="my-project")
    """
    return context_processor.read_context_entity_versions(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
    )


def list_containerimages(
    project: str,
    q: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    user: str | None = None,
    state: str | None = None,
    created: str | None = None,
    updated: str | None = None,
    versions: str | None = None,
) -> list[Containerimage]:
    """
    List all latest version objects from backend.

    Parameters
    ----------
    project : str
        Project name.
    q : str
        Query string to filter objects.
    name : str
        Object name.
    kind : str
        Kind of the object.
    user : str
        User that created the object.
    state : str
        Object state.
    created : str
        Creation date filter.
    updated : str
        Update date filter.
    versions : str
        Object version, default is latest.

    Returns
    -------
    list[Image]
        List of object instances.

    Examples
    --------
    >>> objs = list_containerimages(project="my-project")
    """
    return context_processor.list_context_entities(
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


def import_containerimage(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Containerimage:
    """
    Import an object from a YAML file or from a storage key.

    Parameters
    ----------
    file : str
        Path to the YAML file.
    key : str
        Entity key (store://...).
    reset_id : bool
        Flag to determine if the ID of executable entities should be reset.
    context : str
        Project name to use for context resolution.

    Returns
    -------
    Image
        Object instance.

    Examples
    --------
    >>> obj = import_containerimage("my-image.yaml")
    """
    return context_processor.import_context_entity(
        file,
        key,
        reset_id,
        context,
    )


def load_containerimage(file: str) -> Containerimage:
    """
    Load object from a YAML file and update an existing object into the backend.

    Parameters
    ----------
    file : str
        Path to YAML file.

    Returns
    -------
    Image
        Object instance.

    Examples
    --------
    >>> obj = load_containerimage("my-image.yaml")
    """
    return context_processor.load_context_entity(file)


def update_containerimage(entity: Containerimage) -> Containerimage:
    """
    Update object. Note that object spec are immutable.

    Parameters
    ----------
    entity : Image
        Object to update.

    Returns
    -------
    Image
        Entity updated.

    Examples
    --------
    >>> obj = update_containerimage(obj)
    """
    return context_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_containerimage(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
    cascade: bool = True,
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
        Delete all versions of the named entity.
        If True, use entity name instead of entity key as identifier.
    cascade : bool
        Cascade delete.

    Returns
    -------
    dict
        Response from backend.

    Examples
    --------
    If delete_all_versions is False:
    >>> delete_containerimage("store://my-image-key")

    Otherwise:
    >>> delete_containerimage("my-image-name",
    >>>                  project="my-project",
    >>>                  delete_all_versions=True)
    """
    return context_processor.delete_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
        delete_all_versions=delete_all_versions,
        cascade=cascade,
    )
