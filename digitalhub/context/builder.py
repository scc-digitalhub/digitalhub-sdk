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
        self._initializing: set[str] = set()

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
            # Mark context as being initialized to prevent recursion
            self._initializing.add(project.name)
            try:
                # Create context without registering it yet to avoid recursion
                ctx = Context.__new__(Context)
                # Register context before initialization to prevent recursion
                # when _search_run_ctx() creates a Run that calls _context()
                self._instances[project.name] = ctx
                # Now initialize the context
                ctx.__init__(project)
            finally:
                # Remove from initializing set once done
                self._initializing.discard(project.name)
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

        Raises
        ------
        ContextError
            If no context exists for the specified project name.
        """
        try:
            return self._instances[project]
        except KeyError:
            raise ContextError(f"Context '{project}' not found. Get or create a project named '{project}'.")

    def is_initializing(self, project: str) -> bool:
        """
        Check if a context is currently being initialized.

        Parameters
        ----------
        project : str
            The name of the project to check.

        Returns
        -------
        bool
            True if the context is being initialized, False otherwise.
        """
        return project in self._initializing

    def remove(self, project: str) -> None:
        """
        Remove a project's context from the registry.

        Parameters
        ----------
        project : str
            The name of the project whose context should be removed.
            This method does not return anything.

        Notes
        -----
        If the project does not exist in the registry, this method silently does nothing.
        """
        self._instances.pop(project, None)


context_builder = ContextBuilder()
