# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import shutil
import warnings
from base64 import b64encode
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

if TYPE_CHECKING:
    from git import Repo


class GitCredentialsType(Enum):
    """
    Supported git credentials types.

    Attributes
    ----------
    USERNAME : str
        Environment variable name for git username.
    PASSWORD : str
        Environment variable name for git password.
    TOKEN : str
        Environment variable name for git token.
    """

    USERNAME = "GIT_USERNAME"
    PASSWORD = "GIT_PASSWORD"
    TOKEN = "GIT_TOKEN"


def clone_repository(path: Path, url: str) -> None:
    """
    Clone a git repository to a local path.

    Parameters
    ----------
    path : Path
        Path where to save the repository.
    url : str
        URL of the repository.
    """
    clean_path(path)
    checkout_object = get_checkout_object(url)
    repo = clone_from_url(url, path)
    if checkout_object != "":
        repo.git.checkout(checkout_object)


def get_checkout_object(url: str) -> str:
    """
    Get checkout object (branch, tag, commit) from URL fragment.

    Parameters
    ----------
    url : str
        URL of the repository.

    Returns
    -------
    str
        Checkout object (branch, tag, commit) or empty string if not present.
    """
    return urlparse(url).fragment


def clean_path(path: Path) -> None:
    """
    Remove all files and directories at the given path.

    Parameters
    ----------
    path : Path
        Path to clean.
    """

    shutil.rmtree(path, ignore_errors=True)


def get_git_username_password_from_token(token: str) -> tuple[str, str]:
    """
    Parse a token to get username and password for git authentication.

    The token can be one of the following:
        - GitHub/GitLab personal access token (github_pat_.../glpat...)
        - GitHub/GitLab access token
        - Other generic token

    Parameters
    ----------
    token : str
        Token to parse.

    Returns
    -------
    tuple[str, str]
        Username and password for git authentication.
    """
    if token.startswith(("github_pat_", "glpat_", "glpat-", "ghp_", "gloas-")):
        return "oauth2", token
    return token, "x-oauth-basic"


def _clean_git_remote_url(url: str) -> str:
    url_obj = urlparse(url)
    netloc = url_obj.netloc.rsplit("@", maxsplit=1)[-1]
    return urlunparse((url_obj.scheme, netloc, url_obj.path, "", "", ""))


def _git_auth_environment() -> dict[str, str] | None:
    username = os.getenv(GitCredentialsType.USERNAME.value)
    password = os.getenv(GitCredentialsType.PASSWORD.value)
    token = os.getenv(GitCredentialsType.TOKEN.value)

    if token is not None:
        username, password = get_git_username_password_from_token(token)

    if username is None or password is None:
        return None

    try:
        config_count = int(os.getenv("GIT_CONFIG_COUNT", "0"))
    except ValueError as e:
        raise ValueError("GIT_CONFIG_COUNT must be an integer.") from e
    if config_count < 0:
        raise ValueError("GIT_CONFIG_COUNT cannot be negative.")

    credentials = b64encode(f"{username}:{password}".encode()).decode("ascii")
    return {
        "GIT_CONFIG_COUNT": str(config_count + 1),
        f"GIT_CONFIG_KEY_{config_count}": "http.extraHeader",
        f"GIT_CONFIG_VALUE_{config_count}": f"Authorization: Basic {credentials}",
    }


def clone_from_url(url: str, path: Path) -> Repo:
    """
    Clone a git repository from a URL to a local path.

    Parameters
    ----------
    url : str
        HTTP(S) URL of the repository.
    path : Path
        Path where to save the repository.

    Returns
    -------
    Repo
        The cloned git repository object.
    """
    try:
        from git import Repo
    except ImportError as e:
        if "Bad git executable." in str(e):
            warnings.warn("git is not installed. Please install git and try again.", RuntimeWarning)
        raise

    return Repo.clone_from(
        url=_clean_git_remote_url(url),
        to_path=path,
        env=_git_auth_environment(),
    )
