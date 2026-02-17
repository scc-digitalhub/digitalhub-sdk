# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import typing
from pathlib import Path

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.dataitem._base.crud import log_base_dataitem
from digitalhub.entities.dataitem.croissant.utils import (
    METADATA_DEFAULT_NAME,
    build_croissant_kwargs,
    get_croissant_dataset,
    get_files_from_croissant,
    get_metadata_fields_from_croissant,
    validate_croissant_source,
)
from digitalhub.utils.exceptions import EntityErrorFileNotFound

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant


def log_croissant(
    project: str,
    name: str,
    source: str,
    drop_existing: bool = False,
    path: str | None = None,
    **kwargs,
) -> DataitemCroissant:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    source : str
        Metadata JSON file path.
    drop_existing : bool
        Whether to drop existing entity with the same name.
    path : str
        Destination path of the dataitem. If not provided, it's generated.
    **kwargs : dict
        New dataitem spec parameters.

    Returns
    -------
    DataitemCroissant
        Object instance.

    Examples
    --------
    >>> obj = log_croissant(project="my-project",
    >>>                     name="my-croissant",
    >>>                     source="./metadata.json")
    """
    # Validate the source and transform it to point to the
    # metadata.json file if it's a directory
    metadata_file = validate_croissant_source(source)
    metadata_folder = Path(metadata_file).parent.resolve()

    kwargs = build_croissant_kwargs(project, name, EntityTypes.DATAITEM.value, path, **kwargs)

    # Get the dataset and files from the Croissant metadata
    dataset = get_croissant_dataset(metadata_file)
    files = get_files_from_croissant(dataset, metadata_file)

    # Change working dir to the metadata.json parent to
    # correctly resolve relative paths in content_url
    current_dir = os.getcwd()
    os.chdir(metadata_folder)
    sources = files + [METADATA_DEFAULT_NAME]

    # Log dataitem in the context of the metadata.json dir
    try:
        dataitem = log_base_dataitem(
            project=project,
            name=name,
            kind=EntityKinds.DATAITEM_CROISSANT.value,
            source=sources,
            drop_existing=drop_existing,
            **kwargs,
        )
    except EntityErrorFileNotFound as e:
        raise EntityErrorFileNotFound(
            f"One or more files specified in the Croissant {METADATA_DEFAULT_NAME} were not found. "
            f"Please verify that all content URLs in the {METADATA_DEFAULT_NAME} are correct and that the corresponding files are present."
        ) from e

    # Change back to the original working dir
    os.chdir(current_dir)

    # Update metadata fields from Croissant
    metadata = get_metadata_fields_from_croissant(dataset)
    dataitem.metadata.name = metadata[0]
    dataitem.metadata.description = metadata[1]
    if metadata[2] is not None:
        dataitem.metadata.labels = metadata[2]
    dataitem.save(update=True)

    return dataitem
