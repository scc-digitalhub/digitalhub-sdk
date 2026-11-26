# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import Any

from digitalhub.context.api import get_context
from digitalhub.entities.dataitem.croissant.utils import (
    METADATA_DEFAULT_NAME,
    get_croissant_dataset,
    get_files_from_croissant,
    get_mappings_from_croissant,
)
from digitalhub.stores.data.api import get_store
from digitalhub.utils.uri_utils import has_remote_scheme, has_s3_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant


class DataitemCroissantProcessor:
    """Load the Croissant dataset of a dataitem."""

    def as_dataset(self, obj: DataitemCroissant, overwrite: bool = False) -> Any:
        """Load the dataset; on S3, download its files and map them to the local copies."""
        if has_remote_scheme(obj.spec.path):
            return get_croissant_dataset(obj.spec.path)

        root = get_context(obj.project).root / obj.ENTITY_TYPE
        store = get_store(obj.spec.path, obj.project)
        if not has_s3_scheme(obj.spec.path):
            return get_croissant_dataset(store.download(obj.spec.path, root, overwrite=True))

        metadata = store.download(obj.spec.path + METADATA_DEFAULT_NAME, root, overwrite=True)
        dataset = get_croissant_dataset(metadata)
        for file_path in get_files_from_croissant(dataset, metadata):
            relative_path = str(file_path).replace("\\", "/").lstrip("/")
            store.download(
                f"{obj.spec.path.rstrip('/')}/{relative_path}",
                root / Path(relative_path),
                overwrite=overwrite,
            )
        return get_croissant_dataset(metadata, mapping=get_mappings_from_croissant(dataset, metadata, root))
