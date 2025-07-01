# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class CredentialsStore:
    """
    Credentials store to store and retrieve credentials.
    """

    def __init__(self) -> None:
        self._credentials: dict[str, dict] = {}

    def set(self, profile: str, key: str, value: str) -> None:
        """
        Set credentials.

        Parameters
        ----------
        profile : str
            The profile of the credentials.
        key : str
            The key of the credentials.
        value : str
            The value of the credentials.

        Returns
        -------
        None
        """
        if profile not in self._credentials:
            self._credentials[profile] = {}
        self._credentials[profile][key] = value

    def get(self, profile: str, key: str) -> str | None:
        """
        Get credentials.

        Parameters
        ----------
        profile : str
            The profile of the credentials.
        key : str
            The key of the credentials.

        Returns
        -------
        str | None
            The value of the credentials.
        """
        return self._credentials.get(profile, {}).get(key)

    def get_all(self, profile: str) -> dict[str, str]:
        """
        Get all credentials.

        Parameters
        ----------
        profile : str
            The profile of the credentials.

        Returns
        -------
        dict[str, str]
            The credentials.
        """
        return self._credentials.get(profile, {})

    def set_dict(self, profile: str, origin: str, credentials: dict) -> None:
        """
        Set all credentials.

        Parameters
        ----------
        profile : str
            The profile of the credentials.
        origin : str
            The origin of the credentials.
        credentials : dict
            The credentials.

        Returns
        -------
        None
        """
        for key, value in credentials.items():
            if profile not in self._credentials:
                self._credentials[profile] = {}
            if origin not in self._credentials[profile]:
                self._credentials[profile][origin] = {}
            self._credentials[profile][origin][key] = value

    def get_dict(self, profile: str, origin: str) -> dict[str, str]:
        """
        Get all credentials.

        Parameters
        ----------
        profile : str
            The profile of the credentials.
        origin : str
            The origin of the credentials.

        Returns
        -------
        dict[str, str]
            The credentials.
        """
        return self._credentials.get(profile, {}).get(origin, {})
