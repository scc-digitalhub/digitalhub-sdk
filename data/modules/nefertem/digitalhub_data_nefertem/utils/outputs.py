from __future__ import annotations

import typing
from pathlib import Path

from digitalhub_core.entities._base.status import State
from digitalhub_core.entities.artifacts.crud import new_artifact
from digitalhub_core.utils.exceptions import EntityError
from digitalhub_core.utils.generic_utils import (
    calculate_blob_hash,
    get_file_extension,
    get_file_mime_type,
    get_file_size,
)
from digitalhub_core.utils.logger import LOGGER
from digitalhub_data_nefertem.utils.env import S3_BUCKET

if typing.TYPE_CHECKING:
    from digitalhub_core.entities.artifacts.entity import Artifact


def create_artifact(src_path: str, project: str, run_id: str) -> Artifact:
    """
    Create new artifact in backend.

    Parameters
    ----------
    src_path : str
        The artifact source local path.
    project : str
        The project name.
    run_id : str
        Neferetem run id.

    Returns
    -------
    Artifact
        DHCore artifact.
    """

    try:
        name = Path(src_path).stem.replace("_", "-")
        LOGGER.info(f"Creating new artifact '{name}'.")
        kwargs = {}
        kwargs["project"] = project
        kwargs["name"] = name
        kwargs["kind"] = "artifact"
        kwargs["path"] = f"s3://{S3_BUCKET}/{project}/artifacts/ntruns/{run_id}/{Path(src_path).name}"
        kwargs["hash"] = calculate_blob_hash(src_path)
        kwargs["size"] = get_file_size(src_path)
        kwargs["file_type"] = get_file_mime_type(src_path)
        kwargs["file_extension"] = get_file_extension(src_path)
        artifact = new_artifact(**kwargs)
        artifact.spec.src_path = src_path
        return artifact
    except Exception:
        msg = f"Error creating artifact '{name}'."
        LOGGER.exception(msg)
        raise EntityError(msg)


def upload_artifact(artifact: Artifact) -> None:
    """
    Upload artifact to minio.

    Parameters
    ----------
    artifact : Artifact
        The artifact to upload.

    Returns
    -------
    None
    """
    try:
        LOGGER.info(f"Uploading artifact '{artifact.name}' to minio.")
        artifact.upload()
    except Exception:
        msg = f"Error uploading artifact '{artifact.name}'."
        LOGGER.exception(msg)
        raise EntityError(msg)


def build_status(results: dict, outputs: list[Artifact]) -> dict:
    """
    Build run status.

    Parameters
    ----------
    results : dict
        Neferetem run results.
    outputs : list
        The list of DHCore artifacts.

    Returns
    -------
    dict
        Run status.
    """
    return {
        "state": State.COMPLETED.value,
        "outputs": [{i.name: i.key} for i in outputs],
        "results": {"nefertem_result": results},
    }
