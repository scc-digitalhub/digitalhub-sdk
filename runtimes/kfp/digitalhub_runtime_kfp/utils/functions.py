from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Callable

import kfp
from digitalhub_core.entities._base.state import State
from digitalhub_core.utils.io_utils import read_text
from digitalhub_runtime_kfp.dsl import set_current_project, unset_current_project
from digitalhub_runtime_kfp.utils.outputs import build_status
from kfp.compiler import compiler

import digitalhub as dh


def build_kfp_pipeline(run: dict, pipeline: Callable) -> str | None:
    """
    Build KFP pipeline.

    Parameters
    ----------
    run: dict
        Run definition.
    pipeline : Callable
        KFP pipeline function.

    Returns
    -------
    str
        Pipeline spec.
    """
    pipeline_spec = None
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_package_path = os.path.join(tmpdir, "pipeline.yaml")
        # workaround to pass the project implicitly
        set_current_project(run.get("project"))
        compiler.Compiler(kfp.dsl.PipelineExecutionMode.V1_LEGACY).compile(
            pipeline_func=pipeline,
            package_path=pipeline_package_path,
        )
        unset_current_project()
        pipeline_spec = read_text(pipeline_package_path)
    return pipeline_spec


def run_kfp_pipeline(run: dict) -> dict:
    """
    Run KFP pipeline.

    Parameters
    ----------
    run: dict
        Run dictionary.

    Returns
    -------
    dict
        Execution results.
    """

    def _kfp_execution(pipeline: Callable, function_args) -> dict:
        """
        Run KFP pipeline.

        Parameters
        ----------
        pipeline : Callable
            KFP pipeline function.
        function_args: dict
            Function arguments.

        Returns
        -------
        dict
            Execution results.
        """

        kfp_client = kfp.Client(host=os.environ.get("KFP_ENDPOINT"))

        # workaround to pass the project implicitly
        workflow = run.get("spec", {}).get("workflow", None)

        # workflow was not built locally
        if workflow is None:
            run_status = {"state": State.ERROR.value}
            _update_status(run.get("key"), run_status)
            return run_status

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_package_path = Path(tmpdir, "pipeline.yaml")
            pipeline_package_path.write_text(workflow, encoding="utf-8")
            result = kfp_client.create_run_from_pipeline_package(str(pipeline_package_path), arguments=function_args)

        status = None
        response = None
        run_status = None
        while status is None or status.lower() not in ["succeeded", "failed", "skipped", "error"]:
            time.sleep(5)

            try:
                # Get kfp run status
                response = kfp_client.get_run(run_id=result.run_id)
                status = response.run.status

                # Update dhcore status
                run_status = build_status(response, kfp_client)
                _update_status(run.get("key"), run_status)

            except Exception:
                pass
        return run_status

    return _kfp_execution


def run_kfp_build(run: dict) -> dict:
    """
    Run KFP pipeline build.

    Parameters
    ----------
    run: dict
        Run dictionary.

    Returns
    -------
    dict
        Execution results.
    """

    def _kfp_build_execution(pipeline: Callable, function_args) -> dict:
        """
        Run KFP build.

        Parameters
        ----------
        pipeline : Callable
            KFP pipeline function.
        function_args: dict
            Function arguments.

        Returns
        -------
        dict
            Execution results.
        """

        # workaround to pass the project implicitly
        workflow = run.get("spec", {}).get("workflow", None)

        # need to replicate the build
        workflow = build_kfp_pipeline(run, pipeline)

        run_status = { "state": State.COMPLETED.value, "results": {"workflow":  workflow} }
        _update_status(run.get("key"), run_status)

        return run_status

    return _kfp_build_execution


def _update_status(key: dict, status: dict) -> None:
    """
    Update run status.

    Parameters
    ----------
    key: dict
        Run key.
    status: dict
        Status dictionary.

    Returns
    -------
    None
    """
    dhcore_run = dh.get_run(key)
    new_status = {**status, **dhcore_run.status.to_dict()}
    dhcore_run._set_status(new_status)
    dhcore_run.save(update=True)
