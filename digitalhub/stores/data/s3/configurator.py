# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
from botocore.config import Config

from digitalhub.stores.client.common.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.client.factory import get_client


class S3StoreConfigurator:
    """
    Configurator class for S3 store configuration and credentials management.
    """

    def __init__(self):
        self._web_identity_credentials: dict | None = None
        self._web_identity_expiration: datetime | None = None
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
        creds = dict(get_client().get_credentials_and_config())
        access_key = creds.get(CredentialsVars.S3_ACCESS_KEY_ID.value)
        secret_key = creds.get(CredentialsVars.S3_SECRET_ACCESS_KEY.value)
        if not (access_key and secret_key):
            creds.update(self._get_web_identity_credentials(creds))
        if lowercase_keys:
            return {key.lower(): creds.get(key) for key in keys}
        return {key: creds.get(key) for key in keys}

    def _get_web_identity_credentials(self, config: dict) -> dict:
        """Exchange the configured web identity token for temporary S3 credentials."""
        now = datetime.now(timezone.utc)
        if (
            self._web_identity_credentials is not None
            and self._web_identity_expiration is not None
            and self._web_identity_expiration > now + timedelta(minutes=5)
        ):
            return self._web_identity_credentials

        token_file = config.get(CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value)
        token = Path(token_file).read_text(encoding="utf-8").strip() if token_file else None
        if not token:
            raise ValueError("A web identity token file is required for S3 role authentication.")

        sts_client = boto3.client(
            "sts",
            endpoint_url=config.get(ConfigurationVars.S3_ENDPOINT_URL_STS.value),
            region_name=config.get(ConfigurationVars.S3_REGION.value),
        )
        response = sts_client.assume_role_with_web_identity(
            RoleArn=config[CredentialsVars.S3_ROLE_ARN.value],
            RoleSessionName="digitalhub-s3-store",
            WebIdentityToken=token,
        )
        temporary_credentials = response["Credentials"]
        expiration = temporary_credentials["Expiration"]
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)

        self._web_identity_credentials = {
            CredentialsVars.S3_ACCESS_KEY_ID.value: temporary_credentials["AccessKeyId"],
            CredentialsVars.S3_SECRET_ACCESS_KEY.value: temporary_credentials["SecretAccessKey"],
            CredentialsVars.S3_SESSION_TOKEN.value: temporary_credentials["SessionToken"],
        }
        self._web_identity_expiration = expiration
        return self._web_identity_credentials

    def _validate(self) -> None:
        """
        Validate if all required keys are present in the configuration.
        """
        current_keys = get_client().get_credentials_and_config()
        missing_keys = []
        endpoint = ConfigurationVars.S3_ENDPOINT_URL.value
        access_key = CredentialsVars.S3_ACCESS_KEY_ID.value
        secret_key = CredentialsVars.S3_SECRET_ACCESS_KEY.value
        role_arn = CredentialsVars.S3_ROLE_ARN.value
        token_file = CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value
        sts_endpoint = ConfigurationVars.S3_ENDPOINT_URL_STS.value

        if not current_keys.get(endpoint):
            missing_keys.append(endpoint)

        has_static_credentials = bool(current_keys.get(access_key) and current_keys.get(secret_key))
        has_web_identity_credentials = bool(
            current_keys.get(role_arn) and current_keys.get(token_file) and current_keys.get(sts_endpoint)
        )
        if not (has_static_credentials or has_web_identity_credentials):
            missing_keys.append(
                f"either ({access_key} and {secret_key}) or ({role_arn}, {token_file}, and {sts_endpoint})"
            )
        if missing_keys:
            raise ValueError(f"Missing required variables for S3 store: {', '.join(missing_keys)}")

    def eval_retry(self) -> bool:
        """
        Evaluate the status of retry lifecycle.
        """
        return get_client().eval_retry(check_token_validity=True)
