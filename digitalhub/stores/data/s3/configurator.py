# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from botocore.config import Config

from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.client.base.factory import get_client


class S3StoreConfigurator:
    """
    Configurator class for S3 store configuration and credentials management.
    """

    def __init__(self):
        self._validate()

    ##############################
    # Configuration methods
    ##############################

    def get_client_config(self) -> dict:
        """
        Gets S3 credentials (access key, secret key, session token, and other config).

        Parameters
        ----------
        creds : dict
            The credentials dictionary.

        Returns
        -------
        dict
            A dictionary containing the S3 credentials.
        """
        creds = self.get_credentials(lowercase_keys=False)
        return {
            "endpoint_url": creds[ConfigurationVars.S3_ENDPOINT_URL.value],
            "aws_access_key_id": creds[CredentialsVars.S3_ACCESS_KEY_ID.value],
            "aws_secret_access_key": creds[CredentialsVars.S3_SECRET_ACCESS_KEY.value],
            "aws_session_token": creds[CredentialsVars.S3_SESSION_TOKEN.value],
            "config": Config(
                region_name=creds[ConfigurationVars.S3_REGION.value],
                signature_version=creds[ConfigurationVars.S3_SIGNATURE_VERSION.value],
            ),
        }

    def get_credentials(self, lowercase_keys: bool = True) -> dict:
        """
        Get all configured S3 credentials as a dictionary.

        Parameters
        ----------
        lowercase_keys : bool
            Whether to return credential keys in lowercase format.

        Returns
        -------
        dict
            Dictionary containing all credential key-value pairs from self.keys.
            Keys correspond to S3 connection parameters such as endpoint URL,
            access key ID, secret access key, session token, region, and signature version.
        """
        keys = [
            ConfigurationVars.S3_ENDPOINT_URL.value,
            CredentialsVars.S3_ACCESS_KEY_ID.value,
            CredentialsVars.S3_SECRET_ACCESS_KEY.value,
            CredentialsVars.S3_SESSION_TOKEN.value,
            ConfigurationVars.S3_REGION.value,
            ConfigurationVars.S3_SIGNATURE_VERSION.value,
        ]
        creds = get_client().get_credentials_and_config()
        if lowercase_keys:
            return {key.lower(): creds.get(key) for key in keys}
        return {key: creds.get(key) for key in keys}

    def _validate(self) -> None:
        """
        Validate if all required keys are present in the configuration.
        """
        required_keys = [
            ConfigurationVars.S3_ENDPOINT_URL.value,
            CredentialsVars.S3_ACCESS_KEY_ID.value,
            CredentialsVars.S3_SECRET_ACCESS_KEY.value,
        ]
        current_keys = get_client().get_credentials_and_config()
        missing_keys = []
        for key in required_keys:
            if key not in current_keys or current_keys[key] is None:
                missing_keys.append(key)
        if missing_keys:
            raise ValueError(f"Missing required variables for S3 store: {', '.join(missing_keys)}")

    def eval_retry(self) -> bool:
        """
        Evaluate the status of retry lifecycle.

        Returns
        -------
        bool
            True if a retry action was performed, otherwise False.
        """
        return get_client().eval_retry()
