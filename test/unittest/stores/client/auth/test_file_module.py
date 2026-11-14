# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import os
import stat
from pathlib import Path

import pytest
from dotenv import dotenv_values

from digitalhub.stores.client.auth import file_module
from digitalhub.stores.client.common.config import ClientConfig, get_client_config, set_client_config
from digitalhub.utils.exceptions import ClientError


def test_write_dotenv_preserves_unrelated_values(tmp_path) -> None:
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("UNRELATED=keep\nDHCORE_ACCESS_TOKEN=old\n")
    original_config = get_client_config()

    try:
        set_client_config(ClientConfig(config_ini_path=tmp_path / "config.ini"))
        file_module.write_dotenv({"dhcore_access_token": "new"})
    finally:
        set_client_config(original_config)

    assert dotenv_values(dotenv_file) == {
        "UNRELATED": "keep",
        "DHCORE_ACCESS_TOKEN": "new",
    }
    if os.name != "nt":
        assert stat.S_IMODE(dotenv_file.stat().st_mode) == 0o600


def test_write_file_preserves_percent_in_credential(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    credential = "olD&NXyS3%5f@%gKK5qHx^Wy5"
    monkeypatch.setattr(file_module, "_get_ini_file", lambda: ini_file)

    file_module.write_file({"refresh_token": credential}, "default")

    assert file_module.load_file()["default"]["refresh_token"] == credential
    if os.name != "nt":
        assert stat.S_IMODE(ini_file.stat().st_mode) == 0o600


def test_write_file_removes_none_values_from_profile(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    monkeypatch.setattr(file_module, "_get_ini_file", lambda: ini_file)

    file_module.write_file({"access_token": "old"}, "default")
    file_module.write_file({"access_token": None, "refresh_token": None}, "default")

    assert "access_token" not in file_module.load_file()["default"]
    assert "refresh_token" not in file_module.load_file()["default"]


def test_write_file_and_set_current_profile_write_securely(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    monkeypatch.setattr(file_module, "_get_ini_file", lambda: ini_file)

    file_module.write_file({"refresh_token": "token"}, "default")
    file_module.set_current_profile("other")

    config = file_module.load_file()
    assert config["DEFAULT"]["current_environment"] == "other"
    assert config["default"]["refresh_token"] == "token"
    if os.name != "nt":
        assert stat.S_IMODE(ini_file.stat().st_mode) == 0o600


def test_load_file_wraps_invalid_config_as_client_error(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    ini_file.write_text("invalid config line\n")
    monkeypatch.setattr(file_module, "_get_ini_file", lambda: ini_file)

    with pytest.raises(ClientError, match="Failed to parse .dhcore.ini file"):
        file_module.load_file()


def test_write_file_preserves_existing_file_when_replace_fails(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    ini_file.write_text("[default]\nrefresh_token = old\n")
    monkeypatch.setattr(file_module, "_get_ini_file", lambda: ini_file)

    def fail_replace(source: Path, target: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(file_module.os, "replace", fail_replace)

    with pytest.raises(ClientError, match="Failed to write env file: replace failed"):
        file_module.write_file({"refresh_token": "new"}, "default")

    assert ini_file.read_text() == "[default]\nrefresh_token = old\n"
    assert list(tmp_path.iterdir()) == [ini_file]
