# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import cast

from digitalhub.stores.data.api import get_store
from digitalhub.utils.generic_utils import extract_archive, requests_chunk_download
from digitalhub.utils.git_utils import clone_repository
from digitalhub.utils.uri_utils import (
    get_filename_from_uri,
    has_git_scheme,
    has_remote_scheme,
    has_s3_scheme,
    has_zip_scheme,
)

if typing.TYPE_CHECKING:
    from pathlib import Path

    from digitalhub.stores.data.s3.store import S3Store


def fetch_source(path: Path, source: str) -> None:
    """
    Fetch the source of an executable into a directory.

    A git repository is cloned and an http(s) file is downloaded; a ``zip+``
    archive, over http(s) or S3, is downloaded and extracted.

    Parameters
    ----------
    path : Path
        Directory of the source, created if missing.
    source : str
        URI of the source.
    """
    path.mkdir(parents=True, exist_ok=True)
    if has_git_scheme(source):
        clone_repository(path, source)
    elif has_remote_scheme(source):
        if has_zip_scheme(source):
            _fetch_archive(path, source)
        else:
            requests_chunk_download(source, path / get_filename_from_uri(source))
    elif has_s3_scheme(source):
        if not has_zip_scheme(source):
            raise RuntimeError("S3 source must be a zip file with scheme zip+s3://.")
        _fetch_archive(path, source)
    else:
        raise RuntimeError(f"Unable to collect source from: {source}")


def _fetch_archive(path: Path, source: str) -> None:
    """Download a ``zip+`` archive into the directory and extract it there."""
    url = source.removeprefix("zip+")
    archive = path / get_filename_from_uri(source)
    if has_s3_scheme(url):
        cast("S3Store", get_store(url)).get_s3_source(source, archive)
    else:
        requests_chunk_download(url, archive)
    extract_archive(path, archive)
    archive.unlink()
