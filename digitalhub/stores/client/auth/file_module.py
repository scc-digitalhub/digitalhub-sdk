# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from configparser import ConfigParser

from dotenv import load_dotenv

from digitalhub.stores.client.auth.enums import SetCreds
from digitalhub.stores.client.common.config import get_client_config
from digitalhub.utils.exceptions import ClientError

# File where to write credementials
INI_FILE = get_client_config().config_ini_path
DOTENV_FILE = get_client_config().config_env_path


def write_dotenv(variables: dict) -> None:
    """
    Write variables to the .env file for the current profile.
    Overwrites any existing values for that profile.

    Parameters
    ----------
    variables : dict
        Dictionary of variables to write.
    """
    try:
        current_values = {str(key).upper(): str(value) for key, value in variables.items() if value is not None}

        with open(DOTENV_FILE, "w") as envfile:
            for key, value in current_values.items():
                envfile.write(f"{key}={value}\n")
    except Exception as e:
        raise ClientError(f"Failed to write .env file: {e}")


def load_dotenv_file() -> None:
    """
    Load the .env file into the environment variables.
    """
    try:
        load_dotenv(DOTENV_FILE, verbose=True, override=True)
    except Exception as e:
        raise ClientError(f"Failed to load .env file: {e}")


def ini_file_exists() -> bool:
    """
    Check if the .dhcore.ini file exists.

    Returns
    -------
    bool
        True if the file exists, False otherwise.
    """
    return INI_FILE.exists()


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
        file.read(INI_FILE)
        return file
    except Exception as e:
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
        cfg = load_file()

        sections = cfg.sections()
        if environment not in sections:
            cfg.add_section(environment)

        cfg["DEFAULT"]["current_environment"] = environment
        for k, v in creds.items():
            cfg[environment][k] = str(v)

        INI_FILE.touch(exist_ok=True)
        with open(INI_FILE, "w") as inifile:
            cfg.write(inifile)

    except Exception as e:
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
        cfg = load_file()

        sections = cfg.sections()
        if profile not in sections:
            cfg.add_section(profile)

        cfg["DEFAULT"]["current_environment"] = profile
        for k, v in variables.items():
            cfg[profile][k] = str(v)

        INI_FILE.touch(exist_ok=True)
        with open(INI_FILE, "w") as inifile:
            cfg.write(inifile)

    except Exception as e:
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
        with open(INI_FILE, "w") as inifile:
            cfg.write(inifile)

    except Exception as e:
        raise ClientError(f"Failed to write env file: {e}")
