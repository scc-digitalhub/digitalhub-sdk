# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import shutil
from configparser import ConfigParser
from pathlib import Path
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv, set_key

from digitalhub.stores.client.auth.enums import SetCreds
from digitalhub.stores.client.common.config import get_client_config
from digitalhub.utils.exceptions import ClientError


def _get_ini_file() -> Path:
    return get_client_config().config_ini_path


def _get_dotenv_file() -> Path:
    return Path(get_client_config().config_env_path)


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
    temporary_path: str | None = None
    try:
        current_values = {str(key).upper(): str(value) for key, value in variables.items() if value is not None}
        with NamedTemporaryFile(mode="w", dir=dotenv_file.parent, delete=False) as temporary_file:
            temporary_path = temporary_file.name
            if dotenv_file.exists():
                with open(dotenv_file) as envfile:
                    shutil.copyfileobj(envfile, temporary_file)

        for key, value in current_values.items():
            set_key(temporary_path, key, value, quote_mode="auto")

        os.replace(temporary_path, dotenv_file)
    except OSError as e:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
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
        file = ConfigParser()
        file.read(_get_ini_file())
        return file
    except OSError as e:
        raise ClientError(f"Failed to read env file: {e}")


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


def write_config(creds: dict, environment: str) -> None:
    """
    Write credentials to the .dhcore.ini file for the specified environment.
    Overwrites any existing values for that environment.

    Parameters
    ----------
    creds : dict
        Dictionary of credentials to write.
    environment : str
        Name of the credentials profile/environment.
    """
    try:
        ini_file = _get_ini_file()
        cfg = load_file()

        sections = cfg.sections()
        if environment not in sections:
            cfg.add_section(environment)

        cfg["DEFAULT"]["current_environment"] = environment
        for k, v in creds.items():
            cfg[environment][k] = str(v)

        ini_file.touch(exist_ok=True)
        with open(ini_file, "w") as inifile:
            cfg.write(inifile)

    except OSError as e:
        raise ClientError(f"Failed to write env file: {e}")


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
            cfg[profile][k] = str(v)

        ini_file.touch(exist_ok=True)
        with open(ini_file, "w") as inifile:
            cfg.write(inifile)

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
        with open(_get_ini_file(), "w") as inifile:
            cfg.write(inifile)

    except OSError as e:
        raise ClientError(f"Failed to write env file: {e}")
