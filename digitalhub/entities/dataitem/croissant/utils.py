# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

from digitalhub.entities._commons.utils import build_log_path_as_partition
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.utils.uri_utils import has_local_scheme, has_s3_scheme

METADATA_DEFAULT_NAME = "metadata.json"


def _load_croissant() -> ModuleType:
    """
    Load the mlcroissant module.

    Returns
    -------
    ModuleType
        The mlcroissant module.
    """
    try:
        return importlib.import_module("mlcroissant")
    except ImportError as e:
        raise ModuleNotFoundError("Please install 'mlcroissant' to use this feature.") from e


def get_croissant_dataset(metadata_json_path: str, mapping: dict | None = None) -> Any:
    """
    Get the Croissant Dataset object from the metadata JSON file.

    Parameters
    ----------
    metadata_json_path : str
        Path to the metadata JSON file.
    mapping : dict | None, optional
        Optional mapping to apply to the metadata, by default None.

    Returns
    -------
    mlcroissant.Dataset
        Croissant Dataset object.
    """
    mlcroissant = _load_croissant()
    return mlcroissant.Dataset(metadata_json_path, mapping=mapping)


def get_files_from_croissant(dataset: Any, metadata_path: str) -> list[str]:
    """
    Parse Croissant metadata to extract the local files described
    with FileObject structure, save the paths in a list of strings.

    Parameters
    ----------
    dataset : mlcroissant.Dataset
        The Croissant Dataset object.
    metadata_path : str
        Path to the metadata JSON file.

    Returns
    -------
    list[str]
        List of local file paths extracted from FileObject structures.
    """
    files: list[str] = []
    for file_object in dataset.metadata.file_objects:
        content_url = file_object.content_url
        if content_url is None or not has_local_scheme(content_url):
            continue
        abs_metadata_path = Path(metadata_path).resolve()
        abs_content_url = (abs_metadata_path.parent / Path(content_url)).resolve()
        pth = str(abs_content_url.relative_to(abs_metadata_path.parent))
        files.append(pth)
    return files


def get_file_and_ids_from_croissant(dataset: Any, metadata_path: str) -> dict[str, str]:
    """
    Parse Croissant metadata to extract the local files described
    with FileObject structure, save the paths in a dict of strings with file ids as keys.

    Parameters
    ----------
    dataset : mlcroissant.Dataset
        The Croissant Dataset object.
    metadata_path : str
        Path to the metadata JSON file.

    Returns
    -------
    dict[str, str]
        Dict of local file paths extracted from FileObject structures with file ids as keys.
    """
    files: dict[str, str] = {}
    for file_object in dataset.metadata.file_objects:
        content_url = file_object.content_url
        if (id_ := file_object.id) is None:
            raise ValueError("FileObject is missing an id.")

        if content_url is None or not has_local_scheme(content_url):
            continue
        abs_metadata_path = Path(metadata_path).resolve()
        abs_content_url = (abs_metadata_path.parent / Path(content_url)).resolve()
        pth = str(abs_content_url.relative_to(abs_metadata_path.parent))
        files[id_] = pth
    return files


def get_metadata_fields_from_croissant(dataset: Any) -> tuple[str | None, str | None, list[str] | None]:
    """
    Extract name, description, and keywords from Croissant metadata.

    Parameters
    ----------
    dataset : mlcroissant.Dataset
        The Croissant Dataset object.

    Returns
    -------
    tuple[str | None, str | None, list[str] | None]
        Name, description, and keywords (labels) from metadata.
    """
    metadata = dataset.metadata
    name = getattr(metadata, "name", None)
    description = getattr(metadata, "description", None)
    keywords = getattr(metadata, "keywords", None)
    if keywords is not None and not isinstance(keywords, list):
        keywords = [str(keywords)]
    return name, description, keywords


def validate_croissant_source(src: str) -> str:
    """
    Validate the provided source for the Croissant dataitem, ensuring
    it points to a valid metadata JSON file.

    Parameters
    ----------
    src : str
        Path to the file or directory to validate. If a directory is provided, it must contain a file named 'metadata.json'.

    Returns
    -------
    str
        The path to the valid Croissant metadata JSON file.
    """

    path_src = Path(src)

    # If the provided path does not exist, raise an error
    if not path_src.exists():
        raise ValueError(
            f"The provided path '{src}' does not exist. "
            "Please provide a valid path to a Croissant metadata JSON file or a directory containing it."
        )

    # If source is dir, verify that it contains a file named metadata.json, otherwise raise an error
    if path_src.is_dir():
        filepath = path_src / METADATA_DEFAULT_NAME
        if not filepath.is_file():
            raise ValueError(
                f"The provided directory does not contain a file named '{METADATA_DEFAULT_NAME}'. "
                "Please provide a valid Croissant metadata JSON file or a directory containing it."
            )

    # If it is a file, verify that it is named metadata.json, otherwise raise an error
    if path_src.is_file():
        if path_src.name != METADATA_DEFAULT_NAME:
            raise ValueError(
                f"The provided file is not a valid Croissant metadata JSON file. "
                f"The file must be named '{METADATA_DEFAULT_NAME}'."
            )
        filepath = path_src

    filepath = str(filepath.resolve())

    try:
        _ = get_croissant_dataset(filepath)
    except Exception as e:
        raise ValueError("The provided file is not a valid Croissant metadata JSON file.") from e

    return filepath


def validate_output_path(path: str | None) -> None:
    """
    Validate the output path for the Croissant dataitem.

    Parameters
    ----------
    path : str | None
        Output path to validate.
    """
    if path is None:
        return
    if not has_s3_scheme(path):
        raise ValueError("The output path for Croissant dataitem must be an S3 path.")
    if not path.endswith("/"):
        raise ValueError("The output path for Croissant dataitem must be a partition path ending with '/'.")


def build_croissant_kwargs(
    project: str,
    entity_type: str,
    name: str,
    path: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Build kwargs for logging a Croissant dataitem.

    Parameters
    ----------
    project : str
        Project name.
    entity_type : str
        Entity type.
    name : str
        Object name.
    path : str
        Output path for the dataitem. If None, it will be generated.

    Returns
    -------
    dict[str, Any]
        Kwargs for logging a Croissant dataitem.
    """
    validate_output_path(path)
    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        kwargs["path"] = build_log_path_as_partition(project, entity_type, name, uuid)
    else:
        kwargs["path"] = path

    # For Croissant dataitems, we need to keep the directory structure of the
    # files as defined in the metadata.json, so we set keep_dir_structure to True.
    kwargs["keep_dir_structure"] = True
    return kwargs


def get_mappings_from_croissant(dataset: Any, metadata_path: str, root: Path) -> dict:
    """
    Extract mappings from the Croissant Dataset metadata.

    Parameters
    ----------
    dataset : mlcroissant.Dataset
        The Croissant Dataset object.
    metadata_path : str
        Path to the metadata JSON file, used for resolving relative paths in mappings.
    root : Path
        Root path to resolve relative paths in mappings.

    Returns
    -------
    dict
        Mappings extracted from the dataset metadata.
    """
    mapping_id_filename = get_file_and_ids_from_croissant(dataset, metadata_path)
    return {id_: str((root / Path(file_path)).resolve()) for id_, file_path in mapping_id_filename.items()}
