# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.runtimes._base import Runtime


class RuntimeBuilder:
    """
    Builder class for instantiating runtime objects.

    This class implements the Builder pattern to create Runtime instances.
    Subclasses must set the RUNTIME_CLASS class variable to specify which
    Runtime implementation to build.
    """

    RUNTIME_CLASS: Runtime = None

    def __init__(self) -> None:
        """
        Initialize a RuntimeBuilder instance.
        """
        if self.RUNTIME_CLASS is None:
            raise BuilderError("RUNTIME_CLASS must be set")

    def build(self, project: str, *args, **kwargs) -> Runtime:
        """
        Build a runtime object.

        Parameters
        ----------
        project : str
            The project identifier for the runtime instance.
        *args
            Additional positional arguments to pass to the Runtime constructor.
        **kwargs
            Additional keyword arguments to pass to the Runtime constructor.

        Returns
        -------
        Runtime
            A new instance of the configured Runtime class.
        """
        return self.RUNTIME_CLASS(project, *args, **kwargs)

    def run(self, run: dict) -> dict:
        """
        Run function. By default, this method raises a NotImplementedError,
        as local execution is not implemented. Subclasses can override this
        method to provide specific execution logic for different task kinds.

        Returns
        -------
        dict
            Status of the executed run.
        """
        task_kind = run["spec"]["task"].split(":")[0]
        raise NotImplementedError(f"Local execution not implemented for task kind: {task_kind}")
