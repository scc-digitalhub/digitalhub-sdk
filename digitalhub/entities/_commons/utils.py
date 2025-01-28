from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.models import Metric


def parse_entity_key(key: str) -> tuple[str]:
    """
    Parse the entity key. Returns project, entity type, kind, name and uuid.

    Parameters
    ----------
    key : str
        The entity key.

    Returns
    -------
    tuple[str]
        Project, entity type, kind, name and uuid.
    """
    try:
        # Remove "store://" from the key
        key = key.replace("store://", "")

        # Split the key into parts
        parts = key.split("/")

        # The project is the first part
        project = parts[0]

        # The entity type is the second part
        entity_type = parts[1]

        # The kind is the third part
        kind = parts[2]

        # Tasks and runs have no name and uuid
        if entity_type in (EntityTypes.TASK.value, EntityTypes.RUN.value):
            name = None
            uuid = parts[3]

        # The name and uuid are separated by a colon in the last part
        else:
            name, uuid = parts[3].split(":")

        return project, entity_type, kind, name, uuid
    except Exception as e:
        raise ValueError("Invalid key format.") from e


def get_entity_type_from_key(key: str) -> str:
    """
    Get entity type from key.

    Parameters
    ----------
    key : str
        The key of the entity.

    Returns
    -------
    str
        The entity type.
    """
    _, entity_type, _, _, _ = parse_entity_key(key)
    return entity_type


def get_project_from_key(key: str) -> str:
    """
    Get project from key.

    Parameters
    ----------
    key : str
        The key of the entity.

    Returns
    -------
    str
        The project.
    """
    project, _, _, _, _ = parse_entity_key(key)
    return project


def validate_metric_value(value: Any) -> float | int | list[float | int]:
    """
    Validate metric value.

    Parameters
    ----------
    value : Any
        The value to validate.

    Returns
    -------
    float | int | list[float | int]
        The validated value.
    """
    try:
        return Metric(value=value).value
    except ValidationError as e:
        raise ValueError("Invalid metric value. Must be a list of floats or ints or a float or an int.") from e
