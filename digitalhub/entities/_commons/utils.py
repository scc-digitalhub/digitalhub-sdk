# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Concatenate, ParamSpec, Protocol, TypeVar
from urllib.parse import unquote, urlparse

from digitalhub.utils.exceptions import EntityNotExistsError
from digitalhub.utils.file_utils import eval_zip_sources
from digitalhub.utils.generic_utils import slugify_string
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.uri_utils import SchemeCategory, map_uri_scheme, parse_sql_path

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.versioned.protocol import VersionedEntityProtocol

logger = get_logger(__name__)


class _Refreshable(Protocol):
    def refresh(self) -> object: ...


_RefreshableT = TypeVar("_RefreshableT", bound=_Refreshable)
_P = ParamSpec("_P")
_R = TypeVar("_R")


def build_log_path_from_source(
    project: str,
    entity_type: str,
    name: str,
    uuid: str,
    source: str | list[str],
    *,
    default_store: str,
) -> str:
    """
    Build log path.

    Parameters
    ----------
    project : str
        Project name.
    entity_type : str
        Entity type.
    name : str
        Object name.
    uuid : str
        Object UUID.
    source : str | list[str]
        Source(s).

    Returns
    -------
    str
        Log path.
    """
    path = _get_base_path(default_store, project, entity_type, name, uuid)

    prefix = "zip+" if eval_zip_sources(source) else ""
    path = f"{prefix}{path}"

    if isinstance(source, list) and len(source) >= 1:
        if len(source) > 1:
            path += "/"
        else:
            path += f"/{Path(source[0]).name}"
    elif Path(source).is_dir():
        path += "/"
    elif Path(source).is_file():
        path += f"/{Path(source).name}"

    return path


def build_log_name_from_source(source: str | list[str]) -> str:
    """
    Build a log entity name from a source path.

    Parameters
    ----------
    source : str or list[str]
        Source path(s).

    Returns
    -------
    str
        Slugified source name.
    """
    if isinstance(source, list):
        if len(source) != 1:
            raise ValueError("A name is required when logging multiple sources.")
        source = source[0]

    source_category = map_uri_scheme(source)
    if source_category == SchemeCategory.SQL.value:
        source_name = parse_sql_path(source)["table"]
    elif source_category == SchemeCategory.LOCAL.value:
        source_path = Path(source)
        source_name = source_path.stem if source_path.is_file() else source_path.name
    else:
        parsed_source = urlparse(source)
        source_path = Path(unquote(parsed_source.path.rstrip("/")))
        source_name = source_path.stem or parsed_source.netloc
    return slugify_string(source_name)


def build_log_path_as_partition(
    project: str,
    entity_type: str,
    name: str,
    uuid: str,
    *,
    default_store: str,
) -> str:
    """
    Build log path as partition.

    Parameters
    ----------
    project : str
        Project name.
    entity_type : str
        Entity type.
    name : str
        Object name.
    uuid : str
        Object UUID.

    Returns
    -------
    str
        Log path as partition.
    """
    return _get_base_path(default_store, project, entity_type, name, uuid) + "/"


def build_log_path_from_filename(
    project: str,
    entity_type: str,
    name: str,
    uuid: str,
    filename: str,
    *,
    default_store: str,
) -> str:
    """
    Build log path.

    Parameters
    ----------
    project : str
        Project name.
    entity_type : str
        Entity type.
    name : str
        Object name.
    uuid : str
        Object UUID.
    filename : str
        Filename.

    Returns
    -------
    str
        Log path.
    """
    return _get_base_path(default_store, project, entity_type, name, uuid) + f"/{filename}"


def _get_base_path(
    default_store: str,
    project: str,
    entity_type: str,
    name: str,
    uuid: str,
) -> str:
    """
    Utils to get base path.

    Parameters
    ----------
    project : str
        Project name.
    entity_type : str
        Entity type.
    name : str
        Object name.
    uuid : str
        Object UUID.

    Returns
    -------
    str
        Base path.
    """
    return f"{default_store}/{project}/{entity_type}/{name}/{uuid}"


def build_zip_path(entity: VersionedEntityProtocol, filename: str, *, default_store: str) -> str:
    """
    Get destination path.

    Parameters
    ----------
    entity : VersionedEntityProtocol
        Entity.
    filename : str
        Filename.

    Returns
    -------
    str
        Destination path.
    """
    return f"zip+{default_store}/{entity.project}/{entity.ENTITY_TYPE}/{entity.name}/{entity.id}/{filename}"


def refresh_decorator(
    fn: Callable[Concatenate[_RefreshableT, _P], _R],
) -> Callable[Concatenate[_RefreshableT, _P], _R]:
    """
    Refresh decorator.

    Parameters
    ----------
    fn : Callable
        Function to decorate.

    Returns
    -------
    Callable
        Decorated function.
    """

    @wraps(fn)
    def wrapper(self: _RefreshableT, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        # Prevent rising error if entity is not yet created in backend
        try:
            self.refresh()
        except EntityNotExistsError:
            logger.debug(
                f"Refresh skipped for {getattr(self, 'id', 'unknown')} (entity may not exist in backend yet).",
                exc_info=True,
            )
        return fn(self, *args, **kwargs)

    return wrapper
