"""
Runtime class for running Container functions.
"""
from __future__ import annotations

from typing import Callable

from digitalhub_core.runtimes.base import Runtime
from digitalhub_core.runtimes.registry import KindRegistry

data = {
    "executable": {"kind": "container"},
    "task": [
        {"kind": "container+job", "action": "job"},
        {"kind": "container+serve", "action": "serve"},
        {"kind": "container+build", "action": "build"},
        {"kind": "container+deploy", "action": "deploy"},
    ],
    "run": {"kind": "container+run"},
}


class RuntimeContainer(Runtime):
    """
    Runtime Container class.
    """

    kind_registry = KindRegistry(data)

    def build(self, function: dict, task: dict, run: dict) -> dict:
        """
        Build run spec.

        Parameters
        ----------
        function : dict
            The function.
        task : dict
            The task.
        run : dict
            The run.

        Returns
        -------
        dict
            The run spec.
        """
        return {
            **function.get("spec", {}),
            **task.get("spec", {}),
            **run.get("spec", {}),
        }

    def run(self, run: dict) -> dict:
        """
        Run function.

        Returns
        -------
        dict
            Status of the executed run.
        """
        raise RuntimeError("Cannot excute locally.")

    @staticmethod
    def _get_executable(action: str) -> Callable:
        """
        Select function according to action.

        Parameters
        ----------
        action : str
            Action to execute.

        Returns
        -------
        Callable
            Function to execute.
        """
        raise NotImplementedError
