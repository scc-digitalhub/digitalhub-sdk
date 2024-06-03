"""
Runtime class for running Python functions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from digitalhub_core.runtimes.base import Runtime
from digitalhub_core.utils.logger import LOGGER
from digitalhub_runtime_python.utils.configuration import get_function_from_source
from digitalhub_runtime_python.utils.inputs import get_inputs_parameters
from digitalhub_runtime_python.utils.outputs import build_status, parse_outputs


class RuntimePython(Runtime):
    """
    Runtime Python class.
    """

    allowed_actions = ["job", "nuclio"]

    def __init__(self) -> None:
        """
        Constructor.
        """
        super().__init__()
        self.root_path = Path("digitalhub_runtime_python")
        self.tmp_path = self.root_path / "temp"

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
        LOGGER.info("Validating task.")
        self._validate_task(run)

        LOGGER.info("Starting task.")
        spec = run.get("spec")
        project = run.get("project")

        LOGGER.info("Collecting inputs.")
        fnc_args = self._collect_inputs(spec)

        LOGGER.info("Configuring execution.")
        fnc, wrapped = self._configure_execution(spec)

        LOGGER.info("Executing run.")
        if wrapped:
            results: dict = self._execute(fnc, project, **fnc_args)
        else:
            exec_result = self._execute(fnc, **fnc_args)
            LOGGER.info("Collecting outputs.")
            results = parse_outputs(exec_result, list(spec.get("outputs", {})), project)

        status = build_status(results, spec.get("outputs"))

        # Return run status
        LOGGER.info("Task completed, returning run status.")
        return status

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

    ####################
    # Inputs
    ####################

    def _collect_inputs(self, spec: dict) -> dict:
        """
        Collect inputs.

        Parameters
        ----------
        spec : dict
            Run specs.
        project : str
            Project name.

        Returns
        -------
        dict
            Parameters.
        """
        LOGGER.info("Getting inputs.")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        return get_inputs_parameters(
            spec.get("inputs", {}),
            spec.get("parameters", {}),
            self.tmp_path,
        )

    ####################
    # Configuration
    ####################

    def _configure_execution(self, spec: dict) -> tuple[Callable, bool]:
        """
        Configure execution.

        Parameters
        ----------
        spec : dict
            Run spec.

        Returns
        -------
        Callable
            Function to execute.
        """
        fnc = get_function_from_source(
            self.root_path,
            spec.get("source", {}),
        )
        return fnc, hasattr(fnc, "__wrapped__")
