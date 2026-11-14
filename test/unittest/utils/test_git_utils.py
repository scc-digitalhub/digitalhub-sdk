import builtins
from pathlib import Path
from urllib.parse import urlparse

import pytest

from digitalhub.utils import git_utils
from digitalhub.utils.git_utils import (
    GitCredentialsType,
    add_credentials_git_remote_url,
    get_git_username_password_from_token,
)


@pytest.mark.parametrize(
    "token",
    ["github_pat_example", "glpat-example", "glpat_example", "ghp_example", "gloas-example"],
)
def test_get_git_username_password_from_supported_tokens(token: str) -> None:
    assert get_git_username_password_from_token(token) == ("oauth2", token)


def test_add_credentials_preserves_scheme_and_port_and_encodes_credentials(monkeypatch) -> None:
    monkeypatch.setenv(GitCredentialsType.USERNAME.value, "user@example")
    monkeypatch.setenv(GitCredentialsType.PASSWORD.value, "p@ss:/#word")
    monkeypatch.delenv(GitCredentialsType.TOKEN.value, raising=False)

    url = add_credentials_git_remote_url("http://git.example:8443/group/repo.git#main")
    parsed = urlparse(url)

    assert parsed.scheme == "http"
    assert parsed.hostname == "git.example"
    assert parsed.port == 8443
    assert parsed.username == "user%40example"
    assert parsed.password == "p%40ss%3A%2F%23word"
    assert parsed.path == "/group/repo.git"
    assert parsed.fragment == ""


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("http://git.example:8080/group/repo.git", "http://git.example:8080/group/repo.git"),
        ("https://git.example:8443/group/repo.git", "https://git.example:8443/group/repo.git"),
    ],
)
def test_add_credentials_without_credentials_preserves_scheme_and_port(monkeypatch, source: str, expected: str) -> None:
    for credential in GitCredentialsType:
        monkeypatch.delenv(credential.value, raising=False)

    assert add_credentials_git_remote_url(source) == expected


def test_gitpython_import_error_is_not_silenced(monkeypatch) -> None:
    original_import = builtins.__import__

    def import_without_git(name, *args, **kwargs):
        if name == "git":
            raise ImportError("No module named git")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_git)

    with pytest.raises(ImportError, match="No module named git"):
        git_utils.clone_from_url("https://git.example/group/repo.git", Path("repo"))
