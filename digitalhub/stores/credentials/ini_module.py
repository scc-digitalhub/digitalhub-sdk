# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

from digitalhub.utils.exceptions import ClientError

# File where to write DHCORE_ACCESS_TOKEN and DHCORE_REFRESH_TOKEN
# It's used because we inject the variables in jupyter env,
# but refresh token is only available once. Is it's used, we cannot
# overwrite it with coder, so we need to store the new one in a file,
# preserved for jupyter restart
ENV_FILE = Path.home() / ".dhcore.ini"


def load_file() -> ConfigParser:
    """
    Load current credentials set from the .dhcore.ini file.

    Returns
    -------
    ConfigParser
        Credentials set name.
    """
    try:
        file = ConfigParser()
        file.read(ENV_FILE)
        return file
    except Exception as e:
        raise ClientError(f"Failed to read env file: {e}")


def load_profile(file: ConfigParser) -> str | None:
    """
    Load current credentials set from the .dhcore.ini file.

    Returns
    -------
    str
        Credentials set name.
    """
    try:
        return file["DEFAULT"]["current_environment"]
    except KeyError:
        return


def load_key(file: ConfigParser, profile: str, key: str) -> str | None:
    """
    Load key from current credentials set from the .dhcore.ini file.

    Parameters
    ----------
    file : ConfigParser
        Opened .dhcore.ini file.
    profile : str
        Credentials set name.
    key : str
        Key name.

    Returns
    -------
    str
        Key value.
    """
    try:
        return file[profile][key]
    except KeyError:
        return


def load_from_file(var: str) -> str | None:
    """
    Load variable from config file.

    Parameters
    ----------
    profile : str
        Credentials set name.
    var : str
        Environment variable name.

    Returns
    -------
    str | None
        Environment variable value.
    """
    try:
        cfg = load_file()
        profile = cfg["DEFAULT"]["current_environment"]
        return cfg[profile].get(var)
    except KeyError:
        return


def write_config(creds: dict, environment: str) -> None:
    """
    Write the env variables to the .dhcore.ini file.
    It will overwrite any existing env variables.

    Parameters
    ----------
    creds : dict
        Credentials.
    environment : str
        Credentials set name.

    Returns
    -------
    None
    """
    try:
        cfg = load_file()

        sections = cfg.sections()
        if environment not in sections:
            cfg.add_section(environment)

        cfg["DEFAULT"]["current_environment"] = environment
        for k, v in creds.items():
            cfg[environment][k] = str(v)

        ENV_FILE.touch(exist_ok=True)
        with open(ENV_FILE, "w") as inifile:
            cfg.write(inifile)

    except Exception as e:
        raise ClientError(f"Failed to write env file: {e}")


def set_current_profile(environment: str) -> None:
    """
    Set the current credentials set.

    Parameters
    ----------
    environment : str
        Credentials set name.

    Returns
    -------
    None
    """
    try:
        cfg = load_file()
        cfg["DEFAULT"]["current_environment"] = environment
        with open(ENV_FILE, "w") as inifile:
            cfg.write(inifile)

    except Exception as e:
        raise ClientError(f"Failed to write env file: {e}")


def read_env_from_file() -> str | None:
    """
    Read the current credentials set from the .dhcore.ini file.

    Returns
    -------
    str
        Credentials set name.
    """
    try:
        cfg = load_file()
        return cfg["DEFAULT"]["current_environment"]
    except Exception:
        return None
