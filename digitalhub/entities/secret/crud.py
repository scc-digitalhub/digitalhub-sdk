# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._commons.utils import is_valid_key
from digitalhub.entities._processors.processors import crud_processor
from digitalhub.utils.exceptions import EntityNotExistsError

if typing.TYPE_CHECKING:
    from digitalhub.entities.secret._base.entity import Secret


ENTITY_TYPE = EntityTypes.SECRET.value


def new_secret(
    project: str,
    name: str,
    uuid: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    secret_value: str | None = None,
    **kwargs,
) -> Secret:
    """
    Create a new secret entity in the backend.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Entity name.
    uuid : str, optional
        Entity identifier.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    embedded : bool, default=False
        Whether to embed the entity specification in the project specification.
    secret_value : str
        Secret value. This parameter is required.
    **kwargs : dict
        Additional entity specification parameters.

    Returns
    -------
    Secret
        Created secret entity.
    """
    if secret_value is None:
        raise ValueError("secret_value must be provided.")
    obj: Secret = crud_processor.create_context_entity(
        project=project,
        name=name,
        kind=EntityKinds.SECRET_SECRET.value,
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        entity_type=ENTITY_TYPE,
        **kwargs,
    )
    obj.set_secret_value(value=secret_value)
    return obj


def get_secret(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
) -> Secret:
    """
    Get a secret entity from the backend.

    Parameters
    ----------
    identifier : str
        Entity name or entity key (``store://<project>/<entity_type>/<kind>/<(name>:)<uuid>``).
    project : str, optional
        Project name. Required when ``identifier`` is an entity name.
    entity_id : str, optional
        Entity identifier used to select a specific version when
        ``identifier`` is an entity key.

    Returns
    -------
    Secret
        Retrieved secret entity.
    """
    if not is_valid_key(identifier):
        if project is None:
            raise ValueError("Project must be provided.")
        secrets = list_secrets(project=project)
        for secret in secrets:
            if secret.name == identifier:
                return secret
        raise EntityNotExistsError(f"Secret {identifier} not found.")
    return crud_processor.read_context_entity(
        identifier=identifier,
        entity_type=ENTITY_TYPE,
        project=project,
        entity_id=entity_id,
    )


def list_secrets(project: str) -> list[Secret]:
    """
    List the latest versions of secret entities in a project.

    Parameters
    ----------
    project : str
        Project name.

    Returns
    -------
    list[Secret]
        Latest versions of secret entities in the project.
    """
    return crud_processor.list_context_entities(
        project=project,
        entity_type=ENTITY_TYPE,
    )


def import_secret(
    file: str | None = None,
    key: str | None = None,
    reset_id: bool = False,
    context: str | None = None,
) -> Secret:
    """
    Import a secret entity from a YAML file or entity key.

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
    Secret
        Imported secret entity.
    """
    return crud_processor.import_context_entity(file, key, reset_id, context)


def load_secret(file: str) -> Secret:
    """
    Load a secret entity from a YAML file.

    Parameters
    ----------
    file : str
        Path to a YAML file containing the entity descriptor.

    Returns
    -------
    Secret
        Loaded secret entity. An existing entity is updated when it can be
        identified; otherwise, a new entity is created.
    """
    return crud_processor.load_context_entity(file)


def update_secret(entity: Secret) -> Secret:
    """
    Update a secret entity in the backend.

    Parameters
    ----------
    entity : Secret
        Entity to update. The entity specification is immutable.

    Returns
    -------
    Secret
        Updated secret entity.
    """
    return crud_processor.update_context_entity(
        project=entity.project,
        entity_type=entity.ENTITY_TYPE,
        entity_id=entity.id,
        entity_dict=entity.to_dict(),
    )


def delete_secret(
    identifier: str,
    project: str | None = None,
    entity_id: str | None = None,
    delete_all_versions: bool = False,
) -> dict:
    """
    Delete one or more versions of a secret entity from the backend.

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
    )
