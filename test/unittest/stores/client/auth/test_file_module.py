# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import os
import stat
from pathlib import Path

import pytest
from dotenv import dotenv_values

from digitalhub.stores.client.auth import file_module
from digitalhub.utils.exceptions import ClientError


def test_write_dotenv_preserves_unrelated_values(tmp_path) -> None:
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("UNRELATED=keep\nDHCORE_ACCESS_TOKEN=old\n")
    file_module.write_dotenv({"dhcore_access_token": "new"}, dotenv_file)

    assert dotenv_values(dotenv_file) == {
        "UNRELATED": "keep",
        "DHCORE_ACCESS_TOKEN": "new",
    }
    if os.name != "nt":
        assert stat.S_IMODE(dotenv_file.stat().st_mode) == 0o600


def test_write_file_preserves_percent_in_credential(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    credential = "olD&NXyS3%5f@%gKK5qHx^Wy5"

    file_module.write_file({"refresh_token": credential}, "default", ini_file)

    assert file_module.load_file(ini_file)["default"]["refresh_token"] == credential
    if os.name != "nt":
        assert stat.S_IMODE(ini_file.stat().st_mode) == 0o600


def test_write_file_removes_none_values_from_profile(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"

    file_module.write_file({"access_token": "old"}, "default", ini_file)
    file_module.write_file({"access_token": None, "refresh_token": None}, "default", ini_file)

    assert "access_token" not in file_module.load_file(ini_file)["default"]
    assert "refresh_token" not in file_module.load_file(ini_file)["default"]


def test_write_file_and_set_current_profile_write_securely(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"

    file_module.write_file({"refresh_token": "token"}, "default", ini_file)
    file_module.set_current_profile("other", ini_file)

    config = file_module.load_file(ini_file)
    assert config["DEFAULT"]["current_environment"] == "other"
    assert config["default"]["refresh_token"] == "token"
    if os.name != "nt":
        assert stat.S_IMODE(ini_file.stat().st_mode) == 0o600


def test_load_file_wraps_invalid_config_as_client_error(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    ini_file.write_text("invalid config line\n")

    with pytest.raises(ClientError, match="Failed to parse .dhcore.ini file"):
        file_module.load_file(ini_file)


def test_write_file_preserves_existing_file_when_replace_fails(tmp_path, monkeypatch) -> None:
    ini_file = tmp_path / ".dhcore.ini"
    ini_file.write_text("[default]\nrefresh_token = old\n")

    def fail_replace(source: Path, target: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(file_module.os, "replace", fail_replace)

    with pytest.raises(ClientError, match="Failed to write env file: replace failed"):
        file_module.write_file({"refresh_token": "new"}, "default", ini_file)

    assert ini_file.read_text() == "[default]\nrefresh_token = old\n"
    assert list(tmp_path.iterdir()) == [ini_file]
