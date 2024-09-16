from __future__ import annotations

from urllib.parse import urlparse


def map_uri_scheme(uri: str) -> str:
    """
    Map an URI scheme to a common scheme.

    Parameters
    ----------
    uri : str
        URI.

    Returns
    -------
    str
        Mapped scheme type.

    Raises
    ------
    ValueError
        If the scheme is unknown.
    """
    scheme = urlparse(uri).scheme
    if scheme in [""]:
        return "local"
    if scheme in ["file", "local"]:
        raise ValueError("For local path, do not use any scheme")
    if scheme in ["http", "https"]:
        return "remote"
    if scheme in ["s3", "s3a", "s3n", "zip+s3"]:
        return "s3"
    if scheme in ["sql", "postgresql"]:
        return "sql"
    if scheme in ["git", "git+http", "git+https"]:
        return "git"
    raise ValueError(f"Unknown scheme '{scheme}'!")


def check_local_path(path: str) -> bool:
    """
    Check if path is local.

    Parameters
    ----------
    path : str
        Path of some source.

    Returns
    -------
    bool
        True if path is local.
    """
    scheme = map_uri_scheme(path)
    return scheme == "local"
