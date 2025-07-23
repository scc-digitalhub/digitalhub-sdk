# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime, timezone

from botocore.config import Config

from digitalhub.stores.client.dhcore.utils import refresh_token
from digitalhub.stores.credentials.configurator import Configurator
from digitalhub.stores.credentials.enums import CredsEnvVar


class S3StoreConfigurator(Configurator):
    """
    Configure the store by getting the credentials from user
    provided config or from environment.
    """

    keys = [
        CredsEnvVar.S3_ENDPOINT_URL,
        CredsEnvVar.S3_ACCESS_KEY_ID,
        CredsEnvVar.S3_SECRET_ACCESS_KEY,
        CredsEnvVar.S3_REGION,
        CredsEnvVar.S3_SIGNATURE_VERSION,
        CredsEnvVar.S3_SESSION_TOKEN,
        CredsEnvVar.S3_PATH_STYLE,
        CredsEnvVar.S3_CREDENTIALS_EXPIRATION,
    ]
    required_keys = [
        CredsEnvVar.S3_ENDPOINT_URL,
        CredsEnvVar.S3_ACCESS_KEY_ID,
        CredsEnvVar.S3_SECRET_ACCESS_KEY,
    ]

    def __init__(self):
        super().__init__()
        self.load_configs()

    ##############################
    # Configuration methods
    ##############################

    def load_configs(self) -> None:
        """
        Load the configuration from the environment and from the file.
        """
        self.load_env_vars()
        self.load_file_vars()

    def load_env_vars(self) -> None:
        """
        Load the credentials from the environment.
        """
        env_creds = {var.value: self._creds_handler.load_from_env(var.value) for var in self.keys}
        self._creds_handler.set_credentials(self._env, env_creds)

    def load_file_vars(self) -> None:
        """
        Load the credentials from the file.
        """
        file_creds = {var.value: self._creds_handler.load_from_file(var.value) for var in self.keys}
        self._creds_handler.set_credentials(self._file, file_creds)

    def get_client_config(self, origin: str) -> dict:
        """
        Get S3 credentials (access key, secret key, session token and other config).

        Parameters
        ----------
        origin : str
            The origin of the credentials.

        Returns
        -------
        dict
            The credentials.
        """
        creds = self.get_credentials(origin)
        if self._is_expired(creds[CredsEnvVar.S3_CREDENTIALS_EXPIRATION.value]) and origin == self._file:
            refresh_token()
            self.load_file_vars()
            creds = self.get_credentials(origin)
        return {
            "endpoint_url": creds[CredsEnvVar.S3_ENDPOINT_URL.value],
            "aws_access_key_id": creds[CredsEnvVar.S3_ACCESS_KEY_ID.value],
            "aws_secret_access_key": creds[CredsEnvVar.S3_SECRET_ACCESS_KEY.value],
            "aws_session_token": creds[CredsEnvVar.S3_SESSION_TOKEN.value],
            "config": Config(
                region_name=creds[CredsEnvVar.S3_REGION.value],
                signature_version=creds[CredsEnvVar.S3_SIGNATURE_VERSION.value],
            ),
        }

    @staticmethod
    def _is_expired(timestamp: str | None) -> bool:
        """
        Determine whether a given timestamp is after the current UTC time.

        This function compares the provided timestamp, which should be in ISO 8601
        format with a 'Z' suffix indicating UTC time, to the current time in UTC.

        Parameters
        ----------
        timestamp : str
            A timestamp string in the format 'YYYY-MM-DDTHH:MM:SSZ'.

        Returns
        -------
        bool
            Returns True if the given timestamp is later than the current UTC time,
            otherwise returns False.
        """
        if timestamp is None:
            return False
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc) + datetime.timedelta(seconds=120)
        return dt < now
