# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from configparser import ConfigParser
from configparser import Error as ConfigParserError
from pathlib import Path
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv, set_key

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import SetCreds
from digitalhub.utils.exceptions import ClientError


def _get_ini_file() -> Path:
    return get_client_config().config_ini_path


def _get_dotenv_file() -> Path:
    return Path(get_client_config().config_env_path)


def _atomic_write_text_secure(target_path: Path, write_fn: Callable[[Path], None]) -> None:
    temporary_path: Path | None = None
    replaced = False
    try:
        with NamedTemporaryFile(mode="w", dir=target_path.parent, delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)

        write_fn(temporary_path)
        try:
            os.chmod(temporary_path, 0o600)
        except OSError:
            if os.name != "nt":
                raise

        with open(temporary_path, "rb+") as temporary_file:
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, target_path)
        replaced = True
    finally:
        if not replaced and temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def write_dotenv(variables: dict) -> None:
    """
    Write variables to the .env file for the current profile.
    Overwrites any existing values for that profile.

    Parameters
    ----------
    variables : dict
        Dictionary of variables to write.
    """
    dotenv_file = _get_dotenv_file()
    try:
        current_values = {str(key).upper(): str(value) for key, value in variables.items() if value is not None}

        def write_values(temporary_path: Path) -> None:
            if dotenv_file.exists():
                with open(dotenv_file) as envfile, open(temporary_path, "w") as temporary_file:
                    shutil.copyfileobj(envfile, temporary_file)

            for key, value in current_values.items():
                set_key(str(temporary_path), key, value, quote_mode="auto")

        _atomic_write_text_secure(dotenv_file, write_values)
    except OSError as e:
        raise ClientError(f"Failed to write .env file: {e}")


def load_dotenv_file() -> None:
    """
    Load the .env file into the environment variables.
    """
    try:
        load_dotenv(_get_dotenv_file(), verbose=True, override=True)
    except OSError as e:
        raise ClientError(f"Failed to load .env file: {e}")


def ini_file_exists() -> bool:
    """
    Check if the .dhcore.ini file exists.

    Returns
    -------
    bool
        True if the file exists, False otherwise.
    """
    return _get_ini_file().exists()


def load_file() -> ConfigParser:
    """
    Load the credentials configuration from the .dhcore.ini file.

    Returns
    -------
    ConfigParser
        Parsed configuration file object.
    """
    try:
        file = ConfigParser(interpolation=None)
        file.read(_get_ini_file())
        return file
    except OSError as e:
        raise ClientError(f"Failed to read .dhcore.ini file: {e}") from e
    except ConfigParserError as e:
        raise ClientError(f"Failed to parse .dhcore.ini file: {e}") from e


def load_profile(file: ConfigParser) -> str:
    """
    Load the current credentials profile name from the .dhcore.ini file.

    Parameters
    ----------
    file : ConfigParser
        Parsed configuration file object.

    Returns
    -------
    str
        Name of the credentials profile, or default if not found.
    """
    try:
        return file["DEFAULT"]["current_environment"]
    except KeyError:
        return SetCreds.DEFAULT.value


def load_key(file: ConfigParser, profile: str, key: str) -> str | None:
    """
    Load a specific key value from the credentials profile in the
    .dhcore.ini file.

    Parameters
    ----------
    file : ConfigParser
        Parsed configuration file object.
    profile : str
        Name of the credentials profile.
    key : str
        Name of the key to retrieve.

    Returns
    -------
    str or None
        Value of the key, or None if not found.
    """
    try:
        return file[profile][key]
    except KeyError:
        return


def write_file(variables: dict, profile: str) -> None:
    """
    Write variables to the .dhcore.ini file for the specified profile.
    Overwrites any existing values for that profile.

    Parameters
    ----------
    variables : dict
        Dictionary of variables to write.
    profile : str
        Name of the credentials profile to write to.
    """
    try:
        ini_file = _get_ini_file()
        cfg = load_file()

        sections = cfg.sections()
        if profile not in sections:
            cfg.add_section(profile)

        cfg["DEFAULT"]["current_environment"] = profile
        for k, v in variables.items():
            if v is None:
                cfg.remove_option(profile, k)
            else:
                cfg[profile][k] = str(v)

        def write_profile(temporary_path: Path) -> None:
            with open(temporary_path, "w") as inifile:
                cfg.write(inifile)

        _atomic_write_text_secure(ini_file, write_profile)

    except OSError as e:
        raise ClientError(f"Failed to write env file: {e}")


def set_current_profile(environment: str) -> None:
    """
    Set the current credentials profile in the .dhcore.ini file.

    Parameters
    ----------
    environment : str
        Name of the credentials profile to set as current.
    """
    try:
        cfg = load_file()
        cfg["DEFAULT"]["current_environment"] = environment

        def write_profile(temporary_path: Path) -> None:
            with open(temporary_path, "w") as inifile:
                cfg.write(inifile)

        _atomic_write_text_secure(_get_ini_file(), write_profile)

    except OSError as e:
        raise ClientError(f"Failed to write env file: {e}")
