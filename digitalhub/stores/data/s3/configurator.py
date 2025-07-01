# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from botocore.config import Config

from digitalhub.stores.configurator.configurator import configurator
from digitalhub.stores.data._base.configurator import StoreConfigurator
from digitalhub.stores.data.s3.enums import S3StoreEnv


class S3StoreConfigurator(StoreConfigurator):
    """
    Configure the store by getting the credentials from user
    provided config or from environment.
    """

    keys = [
        S3StoreEnv.ENDPOINT_URL,
        S3StoreEnv.ACCESS_KEY_ID,
        S3StoreEnv.SECRET_ACCESS_KEY,
        S3StoreEnv.REGION,
        S3StoreEnv.SIGNATURE_VERSION,
        S3StoreEnv.SESSION_TOKEN,
    ]

    ##############################
    # Configuration methods
    ##############################

    @staticmethod
    def get_client_config(origin: str) -> dict:
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
        creds = configurator.get_credentials(origin)
        return {
            "endpoint_url": creds[S3StoreEnv.ENDPOINT_URL.value],
            "aws_access_key_id": creds[S3StoreEnv.ACCESS_KEY_ID.value],
            "aws_secret_access_key": creds[S3StoreEnv.SECRET_ACCESS_KEY.value],
            "aws_session_token": creds[S3StoreEnv.SESSION_TOKEN.value],
            "config": Config(
                region_name=creds[S3StoreEnv.REGION.value],
                signature_version=creds[S3StoreEnv.SIGNATURE_VERSION.value],
            ),
        }
