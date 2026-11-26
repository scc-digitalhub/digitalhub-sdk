# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass

from digitalhub.entities._commons.enums import EntityTypes

# Same patterns as Core (Keys.java): KEY_PATTERN and KEY_PATTERN_NO_ID,
# FUNCTION_PATTERN and TASK_PATTERN.
_KEY_PATTERN = re.compile(r"store://([^/]+)/([^/]+)/([^/]+)/([^:]+)(?::(.+))?")
_REF_PATTERN = re.compile(r"([^:/]+)://([^/]+)/([^:]+)(?::(.+))?")

# Entity types whose key ends with the id instead of the name.
_UNVERSIONED_TYPES = (EntityTypes.TASK.value, EntityTypes.RUN.value, EntityTypes.LOG.value)


def build_project_key(project: str) -> str:
    """Build the canonical key for a project."""
    return f"store://{project}"


def is_valid_key(key: str) -> bool:
    """Tell whether a string is an entity key rather than a name."""
    return _KEY_PATTERN.fullmatch(key) is not None


@dataclass(frozen=True)
class EntityKey:
    """
    Key of a context entity: ``store://<project>/<entity_type>/<kind>/<name>:<id>``.

    The id is optional. Tasks, runs and logs have no name: their key
    ends with the id (``store://<project>/run/<kind>/<id>``).
    """

    project: str
    entity_type: str
    kind: str
    name: str | None = None
    id: str | None = None

    @classmethod
    def parse(cls, key: str) -> EntityKey:
        """
        Parse an entity key.

        Parameters
        ----------
        key : str
            Entity key.

        Returns
        -------
        EntityKey
            The parsed key. For tasks, runs and logs the form ``<id>:<id>``,
            used in relationships, gives the id.

        Raises
        ------
        ValueError
            If the string is not an entity key.
        """
        match = _KEY_PATTERN.fullmatch(key)
        if match is None:
            raise ValueError(
                f"Invalid entity key '{key}': expected store://<project>/<entity_type>/<kind>/<name>:<id>."
            )
        project, entity_type, kind, name, entity_id = match.groups()
        if entity_type in _UNVERSIONED_TYPES:
            return cls(project, entity_type, kind, id=entity_id or name)
        return cls(project, entity_type, kind, name, entity_id)

    def __str__(self) -> str:
        if self.name is None:
            last = self.id
        elif self.id is None:
            last = self.name
        else:
            last = f"{self.name}:{self.id}"
        return f"store://{self.project}/{self.entity_type}/{self.kind}/{last}"


@dataclass(frozen=True)
class EntityRef:
    """
    Reference from a run or a task to the entity it uses.

    Executables are referenced as ``<kind>://<project>/<name>:<id>``,
    tasks as ``<kind>://<project>/<id>``.
    """

    kind: str
    project: str
    id: str
    name: str | None = None

    @classmethod
    def parse(cls, ref: str) -> EntityRef:
        """
        Parse an entity reference.

        Parameters
        ----------
        ref : str
            Entity reference.

        Returns
        -------
        EntityRef
            The parsed reference. Without ``:<id>`` the last part is the id
            and the name is ``None``.

        Raises
        ------
        ValueError
            If the string is not an entity reference.
        """
        match = _REF_PATTERN.fullmatch(ref)
        if match is None:
            raise ValueError(f"Invalid entity reference '{ref}': expected <kind>://<project>/<name>:<id>.")
        kind, project, name, entity_id = match.groups()
        if entity_id is None:
            return cls(kind, project, id=name)
        return cls(kind, project, id=entity_id, name=name)

    def __str__(self) -> str:
        last = self.id if self.name is None else f"{self.name}:{self.id}"
        return f"{self.kind}://{self.project}/{last}"
