import builtins
from base64 import b64encode
from pathlib import Path
from unittest.mock import Mock

import pytest

from digitalhub.utils import git_utils
from digitalhub.utils.git_utils import GitCredentialsType, get_git_username_password_from_token


@pytest.mark.parametrize(
    "token",
    ["github_pat_example", "glpat-example", "glpat_example", "ghp_example", "gloas-example"],
)
def test_get_git_username_password_from_supported_tokens(token: str) -> None:
    assert get_git_username_password_from_token(token) == ("oauth2", token)


def test_clone_from_url_uses_clean_url_and_ephemeral_auth_header(monkeypatch) -> None:
    git_module = pytest.importorskip("git")
    monkeypatch.setenv(GitCredentialsType.USERNAME.value, "configured-user")
    monkeypatch.setenv(GitCredentialsType.PASSWORD.value, "configured-password")
    monkeypatch.setenv(GitCredentialsType.TOKEN.value, "github_pat_example")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.abbrev")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "10")
    clone_from = Mock()
    monkeypatch.setattr(git_module.Repo, "clone_from", clone_from)

    git_utils.clone_from_url(
        "https://url-user:url-password@git.example:8443/group/repo.git?token=url-token#main",
        Path("repo"),
    )

    assert clone_from.call_args.kwargs["url"] == "https://git.example:8443/group/repo.git"
    assert clone_from.call_args.kwargs["env"] == {
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_1": "http.extraHeader",
        "GIT_CONFIG_VALUE_1": f"Authorization: Basic {b64encode(b'oauth2:github_pat_example').decode()}",
    }
    assert "github_pat_example" not in repr(clone_from.call_args)
    assert "url-password" not in repr(clone_from.call_args)


def test_clone_from_url_strips_embedded_credentials_without_auth_env(monkeypatch) -> None:
    git_module = pytest.importorskip("git")
    for credential in GitCredentialsType:
        monkeypatch.delenv(credential.value, raising=False)
    clone_from = Mock()
    monkeypatch.setattr(git_module.Repo, "clone_from", clone_from)

    git_utils.clone_from_url("https://user:password@git.example/group/repo.git", Path("repo"))

    assert clone_from.call_args.kwargs["url"] == "https://git.example/group/repo.git"
    assert clone_from.call_args.kwargs["env"] is None


def test_gitpython_import_error_is_not_silenced(monkeypatch) -> None:
    original_import = builtins.__import__

    def import_without_git(name, *args, **kwargs):
        if name == "git":
            raise ImportError("No module named git")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_git)

    with pytest.raises(ImportError, match="No module named git"):
        git_utils.clone_from_url("https://git.example/group/repo.git", Path("repo"))
