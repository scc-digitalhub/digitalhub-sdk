from __future__ import annotations

import pickle
from typing import Any

from digitalhub_core.entities._base.status import State
from digitalhub_core.entities.artifacts.crud import new_artifact
from digitalhub_core.entities.artifacts.entity import Artifact
from digitalhub_core.utils.logger import LOGGER
from digitalhub_data.entities.dataitems.crud import new_dataitem
from digitalhub_data.entities.dataitems.entity.table import DataitemTable
from digitalhub_data.readers.registry import DATAFRAME_TYPES


def collect_outputs(results: Any, outputs: list[str], project_name: str) -> dict:
    """
    Collect outputs. Use the produced results directly.

    Parameters
    ----------
    results : Any
        Function outputs.
    project : Project
        Project object.

    Returns
    -------
    dict
        Function outputs.
    """
    objects = {}
    results = listify_results(results)

    for idx, item in enumerate(results):
        try:
            name = outputs[idx]
        except IndexError:
            name = f"output_{idx}"

        if isinstance(item, (str, int, float, bool, bytes)):
            objects[name] = item

        elif f"{item.__class__.__module__}.{item.__class__.__name__}" in DATAFRAME_TYPES:
            objects[name] = build_and_load_dataitem(name, project_name, item)

        else:
            objects[name] = build_and_load_artifact(name, project_name, item)

    return objects


def parse_outputs(results: Any, run_outputs: list, project_name: str) -> dict:
    """
    Parse outputs.

    Parameters
    ----------
    results : Any
        Function outputs.
    project : Project
        Project object.

    Returns
    -------
    dict
        Function outputs.
    """
    results_list = listify_results(results)
    out_list = []
    for idx, _ in enumerate(results_list):
        try:
            out_list.append(run_outputs.pop(0))
        except IndexError:
            out_list.append(f"output_{idx}")
    return collect_outputs(results, out_list, project_name)


def listify_results(results: Any) -> list:
    """
    Listify results.

    Parameters
    ----------
    results : Any
        Function outputs.

    Returns
    -------
    list
        Function outputs.
    """
    if results is None:
        return []

    if not isinstance(results, (tuple, list)):
        results = [results]

    return results


def build_and_load_dataitem(name: str, project_name: str, data: Any) -> DataitemTable:
    """
    Build and load dataitem.

    Parameters
    ----------
    name : str
        Dataitem name.
    project_name : str
        Project name.
    data : Any
        Data.

    Returns
    -------
    str
        Dataitem key.
    """
    try:
        path = f"s3://datalake/{project_name}/dataitems/table/{name}.parquet"
        di: DataitemTable = new_dataitem(project=project_name, name=name, kind="table", path=path)
        di.write_df(df=data)
        return di
    except Exception as e:
        msg = f"Some error occurred while building and loading dataitem. Exception: {e.__class__}. Error: {e.args}"
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def build_and_load_artifact(name: str, project_name: str, data: Any) -> Artifact:
    """
    Build and load artifact.

    Parameters
    ----------
    name : str
        Artifact name.
    project_name : str
        Project name.
    data : Any
        Data.

    Returns
    -------
    str
        Artifact key.
    """
    try:
        path = f"s3://datalake/{project_name}/artifacts/artifact/{name}.pickle"

        # Dump item to pickle
        with open(f"{name}.pickle", "wb") as f:
            f.write(pickle.dumps(data))

        art = new_artifact(project=project_name, name=name, kind="artifact", path=path)
        art.upload(source=f"{name}.pickle")
        return art

    except Exception as e:
        msg = f"Some error occurred while building and loading artifact. Exception: {e.__class__}. Error: {e.args}"
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def build_status(
    parsed_execution: dict,
    mapped_outputs: dict | None = None,
) -> dict:
    """
    Collect outputs.

    Parameters
    ----------
    parsed_execution : dict
        Parsed execution dict.
    mapped_outputs : dict
        Mapped outputs.

    Returns
    -------
    dict
        Status dict.
    """
    results = {}
    outputs = {}
    if mapped_outputs is None:
        mapped_outputs = {}

    try:
        for key, _ in mapped_outputs.items():
            if key in parsed_execution:
                if isinstance(parsed_execution[key], (DataitemTable, Artifact)):
                    outputs[key] = parsed_execution[key].key
                else:
                    results[key] = parsed_execution[key]
        return {
            "state": State.COMPLETED.value,
            "outputs": outputs,
            "results": results,
        }
    except Exception as e:
        msg = f"Something got wrong during run status building. Exception: {e.__class__}. Error: {e.args}"
        LOGGER.exception(msg)
        raise RuntimeError(msg) from e
