"""
Runtime class for running MLRun functions.
"""
from __future__ import annotations

import typing
from pathlib import Path

import mlrun
from digitalhub_core.entities._base.status import State
from digitalhub_core.entities.artifacts.crud import new_artifact
from digitalhub_core.entities.functions.crud import get_function
from digitalhub_core.runtimes.base import Runtime
from digitalhub_core.utils.exceptions import EntityError
from digitalhub_core.utils.generic_utils import decode_string
from digitalhub_core.utils.logger import LOGGER

if typing.TYPE_CHECKING:
    from digitalhub_core.entities.artifacts.entity import Artifact
    from digitalhub_core.entities.functions.entity import Function
    from mlrun.projects import MlrunProject
    from mlrun.runtimes import BaseRuntime


class RuntimeMLRun(Runtime):
    """
    Runtime MLRun class.
    """

    def __init__(self) -> None:
        """
        Constructor.
        """
        self.root_path = Path("/tmp")
        self.function_source = None

    def build(self, function: dict, task: dict, run: dict) -> dict:
        """
        Merge specs.
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
        # Get action
        action = self._get_action(run)

        # Handle unknown task kind
        if action not in ["mlrun"]:
            msg = f"Task {action} not allowed for MLRun runtime"
            LOGGER.error(msg)
            raise EntityError(msg)

        # Execute action
        return self.execute(action, run)

    ####################
    # Execute
    ####################

    def execute(self, action: str, run: dict) -> dict:
        """
        Execute function.

        Returns
        -------
        dict
            Status of the executed run.
        """

        # Get run specs
        LOGGER.info("Starting task.")
        spec = run.get("spec")
        project = run.get("project")

        # Setup function source and specs
        LOGGER.info("Getting function source.")
        dhcore_function = self._get_dhcore_function(project, spec)
        function_source = self._save_function_source(dhcore_function)
        function_specs = self._parse_function_specs(dhcore_function)

        # Get parameters
        LOGGER.info("Getting parameters.")
        function_args = spec.get("parameters", {})

        # Create MLRun project
        LOGGER.info("Creating MLRun project.")
        mlrun_project = self._get_mlrun_project(project)
        mlrun_function = self._get_mlrun_function(
            mlrun_project,
            dhcore_function.name,
            function_source,
            function_specs,
        )

        # Execute function
        LOGGER.info("Executing function.")
        if action == "mlrun":
            execution_results = self._run_job(mlrun_function, function_args)
        else:
            msg = f"Task {action} not allowed for MLRun runtime"
            LOGGER.error(msg)
            raise EntityError(msg)

        # Parse execution results
        LOGGER.info("Parsing execution results.")
        return self._parse_execution_results(execution_results)

    ####################
    # Dhcore function helpers
    ####################

    def _get_dhcore_function(self, project: str, spec: dict) -> Function:
        """
        Get DHCore function.

        Parameters
        ----------
        project : str
            Name of the project.
        spec : dict
            Run specs.

        Returns
        -------
        Function
            DHCore function.
        """
        function_name = spec.get("function").split("://")[1].split("/")[1].split(":")[0]
        return get_function(project, function_name)

    def _save_function_source(self, function: Function) -> str:
        """
        Save function source.

        Parameters
        ----------
        function : Function
            DHCore function.

        Returns
        -------
        path
            Path to the function source.
        """
        path = self.root_path / function.spec.build.get("origin_filename")
        path.write_text(decode_string(function.spec.build.get("functionSourceCode")))
        return str(path)

    def _parse_function_specs(self, function: Function) -> dict:
        """
        Parse function specs.

        Parameters
        ----------
        function : Function
            DHCore function.

        Returns
        -------
        dict
            Function specs.
        """
        return {
            "image": function.spec.image,
            "tag": function.spec.tag,
            "handler": function.spec.handler,
            "requirements": function.spec.requirements,
        }

    ####################
    # MLRun helpers
    ####################

    @staticmethod
    def _get_mlrun_project(project_name: str) -> MlrunProject:
        """
        Get MLRun project.

        Parameters
        ----------
        project_name : str
            Name of the project.

        Returns
        -------
        MlrunProject
            MLRun project.
        """
        return mlrun.get_or_create_project(project_name, "./")

    @staticmethod
    def _get_mlrun_function(
        project: MlrunProject,
        function_name: str,
        function_source: str,
        function_specs: dict,
    ) -> BaseRuntime:
        """
        Get MLRun function.

        Parameters
        ----------
        project : MlrunProject
            MLRun project.
        function_name : str
            Name of the function.
        function_source : str
            Path to the function source.
        function_specs : dict
            Function specs.

        Returns
        -------
        BaseRuntime
            MLRun function.
        """
        project.set_function(
            function_source,
            name=function_name,
            **function_specs,
        )
        project.save()
        return project.get_function(function_name)

    ####################
    # Execution helpers
    ####################

    @staticmethod
    def _run_job(function: BaseRuntime, function_args: dict) -> BaseRuntime:
        """
        Run MLRun job.

        Parameters
        ----------
        function : BaseRuntime
            MLRun function.
        function_args : dict
            Function arguments.

        Returns
        -------
        dict
            Execution results.
        """
        function_args["local"] = True
        return function.run(**function_args)

    ####################
    # Results helpers
    ####################

    def _parse_execution_results(self, execution_results: BaseRuntime) -> dict:
        """
        Parse execution results.

        Parameters
        ----------
        execution_results : BaseRuntime
            Execution results.

        Returns
        -------
        dict
            Parsed execution results.
        """
        try:
            return {
                "state": self._map_state(execution_results.status.state),
                "artifacts": self._get_artifacts(execution_results.status.artifacts),
                "timing": {
                    "start": execution_results.status.start_time,
                    "updated": execution_results.status.last_update,
                },
            }
        except Exception:
            msg = "Something got wrong during execution results parsing."
            LOGGER.exception(msg)
            raise RuntimeError(msg)

    @staticmethod
    def _map_state(state: str) -> str:
        """
        Map state.

        Parameters
        ----------
        state : str
            State.

        Returns
        -------
        str
            Mapped state.
        """
        _map_state = {
            "completed": State.COMPLETED.value,
            "error": State.ERROR.value,
            "running": State.RUNNING.value,
            "created": State.CREATED.value,
            "pending": State.PENDING.value,
            "unknown": State.ERROR.value,
            "aborted": State.STOP.value,
            "aborting": State.STOP.value,
        }
        return _map_state.get(state, State.ERROR.value)

    def _get_artifacts(self, artifacts: list[dict]) -> dict:
        """
        Get artifacts.

        Parameters
        ----------
        artifacts : dict
            Artifacts.

        Returns
        -------
        dict
            Parsed artifacts.
        """
        infos = []
        for art in artifacts:
            dh_art = self._create_artifact(art)
            self._enrich_metadata(dh_art, art)
            mlrun_key = self._get_mlrun_key(art)
            infos.append(self._get_artifact_info(dh_art, mlrun_key))
        return infos

    @staticmethod
    def _create_artifact(artifact: dict) -> Artifact:
        """
        New artifact.

        Parameters
        ----------
        artifact : dict
            Artifact.

        Returns
        -------
        dict
            Parsed artifact.
        """
        try:
            kwargs = {}
            kwargs["project"] = artifact.get("metadata", {}).get("project")
            kwargs["name"] = artifact.get("metadata", {}).get("key")
            kwargs["kind"] = "artifact"
            kwargs["target_path"] = artifact.get("spec", {}).get("target_path")
            return new_artifact(**kwargs)
        except Exception:
            msg = "Something got wrong during artifact creation."
            LOGGER.exception(msg)
            raise RuntimeError(msg)

    @staticmethod
    def _enrich_metadata(artifact: Artifact, artifact_info: dict) -> None:
        """
        Update artifact.

        Parameters
        ----------
        artifact : Artifact
            Artifact.
        artifact_info : dict
            Artifact info.

        Returns
        -------
        None
        """
        try:
            artifact.metadata.file_size = artifact_info.get("size")
            artifact.save(update=True)
        except Exception:
            msg = "Something got wrong during metadata update."
            LOGGER.exception(msg)
            raise RuntimeError(msg)

    @staticmethod
    def _get_mlrun_key(artifact: dict) -> str:
        """
        Get MLRun key.

        Parameters
        ----------
        artifact : dict
            Artifact.

        Returns
        -------
        str
            MLRun key.
        """
        try:
            project = artifact.get("metadata", {}).get("project")
            db_key = artifact.get("spec", {}).get("db_key")
            return f"store://datasets/{project}/{db_key}"
        except Exception:
            msg = "Something got wrong during MLRun key retrieval."
            LOGGER.exception(msg)
            raise RuntimeError(msg)

    @staticmethod
    def _get_artifact_info(artifact: Artifact, mlrun_key: str) -> dict:
        """
        Get artifact info.

        Parameters
        ----------
        artifact : Artifact
            Artifact.
        mlrun_key : str
            MLRun key.

        Returns
        -------
        dict
            Artifact info.
        """
        try:
            return {
                "key": artifact.name,
                "kind": "artifact",
                "id": f"store://{artifact.project}/artifacts/{artifact.kind}/{artifact.name}:{artifact.id}",
                "mlrun_key": mlrun_key,
            }
        except Exception:
            msg = "Something got wrong during artifact info retrieval."
            LOGGER.exception(msg)
            raise RuntimeError(msg)
