# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import importlib.util as imputil
import json
import stat
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import date, datetime, time
from enum import Enum, EnumMeta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType
from typing import Any
from warnings import warn
from zipfile import ZipFile

from slugify import slugify

from digitalhub.utils.io_utils import read_text


def get_timestamp() -> str:
    """
    Get the current timestamp in ISO format with timezone.

    Returns
    -------
    str
        The current timestamp in ISO format with timezone.
    """
    return datetime.now().astimezone().isoformat()


def decode_base64_string(string: str) -> str:
    """
    Decode a string from base64 encoding.

    Parameters
    ----------
    string : str
        The base64-encoded string to decode.

    Returns
    -------
    str
        The decoded string.
    """
    return base64.b64decode(string).decode()


def encode_string(string: str) -> str:
    """
    Encode a string in base64.

    Parameters
    ----------
    string : str
        The string to encode.

    Returns
    -------
    str
        The base64-encoded string.
    """
    return base64.b64encode(string.encode()).decode()


def encode_source(path: str) -> str:
    """
    Read a file and encode its content in base64.

    Parameters
    ----------
    path : str
        The file path to read.

    Returns
    -------
    str
        The file content encoded in base64.
    """
    return encode_string(read_text(path))


def requests_chunk_download(
    source: str,
    filename: Path,
    timeout: float | tuple[float, float] = (10, 60),
) -> None:
    """
    Download a file from a URL in chunks and save to disk.

    Parameters
    ----------
    source : str
        URL to download the file from.
    filename : Path
        Path where to save the downloaded file.
    timeout : float | tuple[float, float]
        Request timeout. Defaults to a 10-second connection timeout and a
        60-second read timeout.
    """
    import requests

    with requests.get(source, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with filename.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def extract_archive(path: Path, filename: Path) -> None:
    """
    Extract a zip archive to a specified directory.

    Parameters
    ----------
    path : Path
        Directory where to extract the archive.
    filename : Path
        Path to the zip archive file.
    """
    base_dir = path.resolve()
    with ZipFile(filename, "r") as zip_file:
        members = zip_file.infolist()
        for member in members:
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError(f"Unsafe symbolic link in archive: {member.filename}")

            target = (base_dir / member.filename).resolve()
            if not target.is_relative_to(base_dir):
                raise ValueError(f"Unsafe path in archive: {member.filename}")

        zip_file.extractall(base_dir, members=members)


@contextmanager
def create_archive(path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary zip archive for the duration of a context.

    Parameters
    ----------
    path : Path
        Directory to archive.

    Returns
    -------
    Generator[Path, None, None]
        Context manager yielding the created zip archive path.
    """
    with TemporaryDirectory() as temp_dir:
        filename = Path(temp_dir) / "archive.zip"
        with ZipFile(filename, "w") as zip_file:
            for file in path.rglob("*"):
                zip_file.write(file, file.relative_to(path))
        yield filename


class CustomJsonEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle serialization of special types.
    """

    def default(self, obj: Any) -> Any:
        """
        Convert an object to a JSON-serializable format.

        Parameters
        ----------
        obj : Any
            The object to convert.

        Returns
        -------
        Any
            The object converted to a JSON-serializable format.
        """
        if isinstance(obj, (int, str, float, list, dict)):
            return obj
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()

        import numpy as np

        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return str(obj)


def dump_json(struct: Any) -> str:
    """
    Convert a Python object to a JSON string using CustomJsonEncoder.

    Parameters
    ----------
    struct : Any
        The object to convert to JSON.

    Returns
    -------
    str
        The JSON string representation of the object.
    """
    return json.dumps(struct, cls=CustomJsonEncoder)


def slugify_string(filename: str, **kwargs) -> str:
    """
    Sanitize a filename using slugify.

    Parameters
    ----------
    filename : str
        The filename to sanitize.

    Returns
    -------
    str
        The sanitized filename (max length 255).
    """
    return slugify(filename, regex_pattern=r"[^-a-z0-9]+", max_length=255, **kwargs)


def import_function(path: Path, handler: str) -> Callable:
    """
    Import a function from a Python module file.

    Parameters
    ----------
    path : Path
        Path to the Python module file.
    handler : str
        Name of the function to import.

    Returns
    -------
    Callable
        The imported function.
    """
    spec = imputil.spec_from_file_location(path.stem, path)
    if spec is None:
        raise RuntimeError(f"Error loading function source from {path!s}.")

    mod = imputil.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Error getting module loader from {path!s}.")

    spec.loader.exec_module(mod)
    func = getattr(mod, handler)
    if not callable(func):
        raise TypeError(f"Handler '{handler}' is not a callable.")

    return func


def list_enum(enum: EnumMeta) -> list[Any]:
    """
    Get all values of an enum class.

    Parameters
    ----------
    enum : EnumMeta
        Enum class to get values from.

    Returns
    -------
    list
        List of enum values.
    """
    vals: MappingProxyType[str, Enum] = enum.__members__
    return [member.value for member in vals.values()]


def carriage_return_warn(string: str) -> None:
    """
    Print a warning message if the string contains
    a carriage return (\r\n).

    Parameters
    ----------
    string : str
        The string to check.
    """
    if "\r\n" in string:
        warn("String contains a carriage return. It may not be parsed correctly from remote runtimes.")


def read_source(path: str) -> str:
    """
    Read a file and encode its content in base64,
    warning if carriage returns are present.

    Parameters
    ----------
    path : str
        Path to the file.

    Returns
    -------
    str
        Base64-encoded file content.
    """
    text = read_text(path)
    carriage_return_warn(text)
    return encode_string(text)
