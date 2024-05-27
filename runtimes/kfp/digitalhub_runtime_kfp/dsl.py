from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager

import digitalhub_core as dhcore
from kfp import dsl
from kubernetes import client as k8s_client

# Variable to track the current project reference without affecting the code
current_project = None

label_prefix = "kfp-digitalhub-runtime-"


def set_current_project(val: str):
    """Set the current project for the context of the pipeline

    The current project is used implicitly in pipeline workflows without
    specifying the project explicitly.

    Args:
        val (str): The name of the project to set as current
    """
    global current_project
    current_project = threading.local()
    # store the project name in the thread local storage
    current_project.val = val


def unset_current_project() -> None:
    """Remove the current project from the pipeline context

    This is used to reset the current project to the default (None) for testing
    or other cases where the current project should not be used anymore.
    """
    global current_project
    current_project = None


@contextmanager
def pipeline_context():
    try:
        yield PipelineContext()
    finally:
        pass


class PipelineContext:
    def __init__(self) -> None:
        """Initialize the pipeline context

        This function initializes the pipeline context by retrieving the project
        from Digital Hub using the currently defined project name. If no project
        is defined, an exception is raised.

        Raises:
            Exception: If the current project is not defined
        """
        global current_project
        if current_project is not None:
            # Retrieve the project object from Digital Hub using the project name
            self._project = dhcore.get_project(current_project.val)
        else:
            # If the current project is not defined, raise an exception
            raise Exception("Current project is not defined")

    def step(
        self,
        name: str,
        function: str | None = None,
        workflow: str | None = None,
        action: str | None = None,
        node_selector: list[dict] | None = None,
        volumes: list[dict] | None = None,
        resources: list[dict] | None = None,
        env: list[dict] | None = None,
        secrets: list[str] | None = None,
        inputs: dict | None = None,
        outputs: dict | None = None,
        parameters: dict | None = None,
        values: list | None = None,
        **kwargs,
    ) -> dsl.ContainerOp:
        """Execute a function in Digital Hub Core.

        This function creates a KFP ContainerOp that executes a function or another workflow in
        Digital Hub Core. The function is executed in the context of the current
        project, which is retrieved from Digital Hub Core when the pipeline
        context is initialized.

        Args:
            name: The name of the step in KFP.
            function: The name of the function to execute. Either function or workflow must be provided.
            workflow: The name of the workflow to execute. Either function or workflow must be provided.
            action: The name of the action to execute. May be omitted in case of workflow execution (defaulting to 'pipeline').
            node_selector: A list of node selectors for the step.
            volumes: A list of volumes for the step.
            resources: A list of resource requirements for the step.
            env: A list of environment variables for the step.
            secrets: A list of secret names for the step.
            inputs: A list of complex input parameters.
            outputs: A list of complex output parameters.
            parameters: A list of simple input parameters.
            values: A list of simple output parameters.
            kwargs: Additional keyword arguments to pass to the step.

        Returns:
            A KFP ContainerOp for the step.
        """

        WORKFLOW_IMAGE = os.environ.get("DIGITALHUB_CORE_WORKFLOW_IMAGE")
        KFPMETA_DIR = os.environ.get("KFPMETA_OUT_DIR", "/tmp")
        DIGITALHUB_CORE_ENDPOINT = os.environ.get("DIGITALHUB_CORE_ENDPOINT", "http://localhost:8080/")
        # DIGITALHUB_CORE_ENDPOINT = "http://10.30.42.210:8080/"

        props = {
            "node_selector": node_selector,
            "volumes": volumes,
            "resources": resources,
            "env": env,
            "secrets": secrets,
        }

        parameters = {} if parameters is None else parameters
        inputs = {} if inputs is None else inputs
        outputs = {} if outputs is None else outputs
        values = [] if values is None else values

        if function is None and workflow is None:
            raise RuntimeError("Either function or workflow must be provided.")

        if function is not None:
            function_object = dhcore.get_function(self._project.name, entity_name=function)
            if function_object is None:
                raise RuntimeError(f"Function {function} not found")
        elif workflow is not None:
            workflow_object = dhcore.get_workflow(self._project.name, entity_name=workflow)
            if workflow_object is None:
                raise RuntimeError(f"Workflow {workflow} not found")
            if action is None:
                action = "pipeline"

        args = {}
        if kwargs is not None:
            args.update(kwargs)

        file_outputs = {
            "mlpipeline-ui-metadata": KFPMETA_DIR + "/mlpipeline-ui-metadata.json",
            "mlpipeline-metrics": KFPMETA_DIR + "/mlpipeline-metrics.json",
            "run_id": "/tmp/run_id",
        }

        cmd = [
            "python",
            "step.py",
            "--project",
            self._project.name,
            "--function" if function is not None else "--workflow",
            function if function is not None else workflow,
            "--function_id" if function is not None else "--workflow_id",
            function_object.id if function is not None else workflow_object.id,
            "--action",
            action,
            "--jsonprops",
            json.dumps(props),
        ]
        # simple input parameters and kwargs
        for param, val in args.items():
            cmd += ["-a", f"{param}={val}"]

        # complex input parameters
        for param, val in inputs.items():
            cmd += ["-ie", f"{param}={val}"]

        # simple input parameters
        for param, val in parameters.items():
            cmd += ["-iv", f"{param}={val}"]

        # complex output parameters
        for param, val in outputs.items():
            cmd += ["-oe", f"{param}={val}"]
            if isinstance(val, dsl.PipelineParam):
                raise Exception("Invalid output specification: cannot use pipeline params")
            else:
                oname = str(val)
            file_outputs[oname.replace(".", "_")] = f"/tmp/entity_{oname}"  # not using path.join to avoid windows "\"

        for param in values:
            cmd += ["-ov", f"{param}"]
            file_outputs[param.replace(".", "_")] = f"/tmp/value_{val}"  # not using path.join to avoid windows "\"

        cop = dsl.ContainerOp(
            name=name,
            image=WORKFLOW_IMAGE,
            command=cmd,
            file_outputs=file_outputs,
        )
        cop.add_pod_label(label_prefix + "project", self._project.name)
        if function is not None:
            cop.add_pod_label(label_prefix + "function", function)
            cop.add_pod_label(label_prefix + "function_id", function_object.id)
        if workflow is not None:
            cop.add_pod_label(label_prefix + "workflow", workflow)
            cop.add_pod_label(label_prefix + "workflow_id", workflow_object.id)
        cop.add_pod_label(label_prefix + "action", action)

        cop.container.add_env_variable(
            k8s_client.V1EnvVar(name="DIGITALHUB_CORE_ENDPOINT", value=DIGITALHUB_CORE_ENDPOINT)
        )

        RUN_SECRET_NAME = os.environ.get("DH_RUN_SECRET_NAME")

        if RUN_SECRET_NAME is not None:
            # user credentials from secret in steps
            names = [
                "DIGITALHUB_CORE_TOKEN",
                "DIGITALHUB_CORE_AUTH_SUB",
                "DIGITALHUB_CORE_USER",
                "DIGITALHUB_CORE_PASSWORD",
            ]
            for name in names:
                cop.container.add_env_variable(
                    k8s_client.V1EnvVar(
                        name=name,
                        value_from=k8s_client.V1EnvVarSource(
                            secret_key_ref=k8s_client.V1SecretKeySelector(name=RUN_SECRET_NAME, key=name, optional=True)
                        ),
                    )
                )
        return cop
