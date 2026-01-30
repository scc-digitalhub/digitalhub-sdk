# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.context import Context
from digitalhub.utils.exceptions import ContextError

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project


class ContextBuilder:
    """
    A builder class for managing project contexts.
    """

    def __init__(self) -> None:
        self._instances: dict[str, Context] = {}

    def build(self, project: Project) -> Context:
        """
        Add a project as context and return the created Context instance.

        Parameters
        ----------
        project : Project
            The project instance to create a context for.

        Returns
        -------
        Context
            The newly created or existing Context instance.
        """
        if project.name not in self._instances:
            # Create context without registering it yet to avoid recursion
            # then register it before initialization to prevent recursion
            # finally initialize it
            ctx = Context.__new__(Context)
            self._instances[project.name] = ctx
            ctx.__init__(project)
        return self._instances[project.name]

    def get(self, project: str) -> Context:
        """
        Retrieve a context instance by project name.

        Parameters
        ----------
        project : str
            The name of the project whose context to retrieve.

        Returns
        -------
        Context
            The context instance associated with the project.
        """
        try:
            return self._instances[project]
        except KeyError:
            raise ContextError(f"Context '{project}' not found. Get or create a project named '{project}'.")

    def remove(self, project: str) -> None:
        """
        Remove a project's context from the registry.

        Parameters
        ----------
        project : str
            The name of the project whose context should be removed.
        """
        self._instances.pop(project, None)


context_builder = ContextBuilder()
