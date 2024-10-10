from __future__ import annotations

from urllib.parse import urlparse

import mlflow

from digitalhub.entities.model.entity._base import Model
from digitalhub.entities.model.models import Dataset, Signature


class ModelMlflow(Model):
    """
    Mlflow model.
    """


def from_mlflow_run(run_id: str) -> dict:
    """
    Extract from mlflow run spec for Digitalhub Model.

    Parameters
    ----------
    run_id : str
        The id of the mlflow run.

    Returns
    -------
    dict
        The extracted spec.
    """

    # Get MLFlow run
    client = mlflow.MlflowClient()
    run = client.get_run(run_id)

    # Extract spec
    data = run.data
    parameters = data.params
    metrics = data.metrics
    source_path = urlparse(run.info.artifact_uri).path
    model_uri = f"runs:/{run_id}/model"
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    model_config = model.model_config
    flavor = None
    for f in model.metadata.flavors:
        if f != "python_function":
            flavor = f
            break

    # Extract signature
    mlflow_signature = model.metadata.signature
    signature = Signature(
        inputs=mlflow_signature.inputs.to_json() if mlflow_signature.inputs else None,
        outputs=mlflow_signature.outputs.to_json() if mlflow_signature.outputs else None,
        params=mlflow_signature.params.to_json() if mlflow_signature.params else None,
    ).dict()

    # Extract datasets
    datasets = []
    if run.inputs and run.inputs.dataset_inputs:
        datasets = [
            Dataset(
                name=d.dataset.name,
                digest=d.dataset.digest,
                profile=d.dataset.profile,
                schema=d.dataset.schema,
                source=d.dataset.source,
                source_type=d.dataset.source_type,
            ).dict()
            for d in run.inputs.dataset_inputs
        ]

    # Create model params
    model_params = {}

    # source path
    model_params["source"] = source_path

    # common properties
    model_params["framework"] = flavor
    model_params["parameters"] = parameters
    model_params["metrics"] = metrics

    # specific to MLFlow
    model_params["flavor"] = flavor
    model_params["model_config"] = model_config
    model_params["input_datasets"] = datasets
    model_params["signature"] = signature

    return model_params
