# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from requests import request

from digitalhub.stores.client.dhcore.enums import AuthType
from digitalhub.stores.credentials.configurator import Configurator
from digitalhub.stores.credentials.enums import CredsEnvVar, CredsOrigin
from digitalhub.stores.credentials.handler import creds_handler
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.generic_utils import list_enum
from digitalhub.utils.uri_utils import has_remote_scheme

if typing.TYPE_CHECKING:
    from requests import Response


# API levels that are supported
MAX_API_LEVEL = 20
MIN_API_LEVEL = 11
LIB_VERSION = 13


class ClientDHCoreConfigurator(Configurator):
    """
    Configurator object used to configure the client.
    """

    keys = [*list_enum(CredsEnvVar)]
    required_keys = [CredsEnvVar.DHCORE_ENDPOINT.value]
    keys_to_unprefix = [
        CredsEnvVar.DHCORE_REFRESH_TOKEN.value,
        CredsEnvVar.DHCORE_ACCESS_TOKEN.value,
        CredsEnvVar.DHCORE_ISSUER.value,
        CredsEnvVar.DHCORE_CLIENT_ID.value,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._current_env = creds_handler.get_current_env()
        self._origin = CredsOrigin.ENV.value
        self.load_configs()

    ##############################
    # Configuration methods
    ##############################

    def load_configs(self) -> None:
        self.load_env_vars()
        self.load_file_vars()

        env_creds = self._creds_handler.get_credentials(self._env)
        missing_env = self._check_credentials(env_creds)

        file_creds = self._creds_handler.get_credentials(self._file)
        missing_file = self._check_credentials(file_creds)

        msg = ""
        if missing_env:
            msg = f"Missing credentials in env: {', '.join(missing_env)}"
            self.change_origin()
        elif missing_file:
            msg += f"Missing credentials in file: {', '.join(missing_file)}"

        if missing_env and missing_file:
            raise ClientError(msg)

    def load_env_vars(self) -> None:
        env_creds = {var: self._creds_handler.load_from_env(var) for var in self.keys}
        env_creds = self._sanitize_env_vars(env_creds)
        self._creds_handler.set_credentials(self._env, env_creds)

    def load_file_vars(self) -> None:
        keys = [*self._remove_prefix_dhcore()]
        file_creds = {var: self._creds_handler.load_from_file(var) for var in keys}
        file_creds = self._sanitize_file_vars(file_creds)
        self._creds_handler.set_credentials(self._file, file_creds)

    def change_origin(self) -> None:
        if self._origin == CredsOrigin.ENV.value:
            self._origin = CredsOrigin.FILE.value
        else:
            self._origin = CredsOrigin.ENV.value

    def check_config(self) -> None:
        """
        Check if the config is valid.

        Parameters
        ----------
        config : dict
            Configuration dictionary.

        Returns
        -------
        None
        """
        if creds_handler.get_current_env() != self._current_env:
            self.load_file_vars()

    def check_core_version(self, response: Response) -> None:
        """
        Raise an exception if DHCore API version is not supported.

        Parameters
        ----------
        response : Response
            The response object.

        Returns
        -------
        None
        """
        if "X-Api-Level" in response.headers:
            core_api_level = int(response.headers["X-Api-Level"])
            if not (MIN_API_LEVEL <= core_api_level <= MAX_API_LEVEL):
                raise ClientError("Backend API level not supported.")
            if LIB_VERSION < core_api_level:
                warn("Backend API level is higher than library version. You should consider updating the library.")

    def build_url(self, api: str) -> str:
        """
        Build the url.

        Parameters
        ----------
        api : str
            The api to call.

        Returns
        -------
        str
            The url.
        """
        creds = self._creds_handler.get_credentials(self._origin)
        endpoint = creds[CredsEnvVar.DHCORE_ENDPOINT.value]
        return f"{endpoint}/{api.removeprefix('/')}"

    def _sanitize_env_vars(self, creds: dict) -> dict:
        """
        Sanitize the env vars. We expect issuer to have the
        form "DHCORE_ISSUER" in env.

        Parameters
        ----------
        creds : dict
            Credentials dictionary.

        Returns
        -------
        dict
        """
        creds[CredsEnvVar.DHCORE_ENDPOINT.value] = self._sanitize_endpoint(creds[CredsEnvVar.DHCORE_ENDPOINT.value])
        creds[CredsEnvVar.DHCORE_ISSUER.value] = self._sanitize_endpoint(creds[CredsEnvVar.DHCORE_ISSUER.value])
        return creds

    def _sanitize_file_vars(self, creds: dict) -> dict:
        """
        Sanitize the file vars. We expect issuer, client_id and access_token and
        refresh_token to not have the form "DHCORE_" in the file.

        Parameters
        ----------
        creds : dict
            Credentials dictionary.

        Returns
        -------
        dict
        """
        creds[CredsEnvVar.DHCORE_ENDPOINT.value] = self._sanitize_endpoint(creds[CredsEnvVar.DHCORE_ENDPOINT.value])
        creds[CredsEnvVar.DHCORE_ISSUER.value] = self._sanitize_endpoint(
            creds[CredsEnvVar.DHCORE_ISSUER.value.removeprefix("DHCORE_")]
        )
        creds[CredsEnvVar.DHCORE_REFRESH_TOKEN.value] = creds[
            CredsEnvVar.DHCORE_REFRESH_TOKEN.value.removeprefix("DHCORE_")
        ]
        creds[CredsEnvVar.DHCORE_ACCESS_TOKEN.value] = creds[
            CredsEnvVar.DHCORE_ACCESS_TOKEN.value.removeprefix("DHCORE_")
        ]
        creds[CredsEnvVar.DHCORE_CLIENT_ID.value] = creds[CredsEnvVar.DHCORE_CLIENT_ID.value.removeprefix("DHCORE_")]
        return {k: v for k, v in creds.items() if k in self.keys}

    @staticmethod
    def _sanitize_endpoint(endpoint: str | None = None) -> str | None:
        """
        Sanitize the endpoint.

        Returns
        -------
        str | None
            The sanitized endpoint.
        """
        if endpoint is None:
            return
        if not has_remote_scheme(endpoint):
            raise ClientError("Invalid endpoint scheme. Must start with http:// or https://.")

        endpoint = endpoint.strip()
        return endpoint.removesuffix("/")

    ##############################
    # Auth methods
    ##############################

    def get_auth_type(self) -> str:
        """
        Evaluate the auth type from the credentials.

        Returns
        -------
        str
            The auth type.
        """
        creds = creds_handler.get_credentials(self._origin)
        return self._eval_auth_type(creds)

    def set_request_auth(self, kwargs: dict) -> dict:
        """
        Get the authentication header.

        Parameters
        ----------
        kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        dict
            Authentication header.
        """
        creds = creds_handler.get_credentials(self._origin)
        auth_type = self.get_auth_type()

        if auth_type is None:
            return kwargs
        if auth_type == AuthType.EXCHANGE.value:
            return kwargs
        if auth_type == AuthType.BASIC.value:
            user = creds[CredsEnvVar.DHCORE_USER.value]
            password = creds[CredsEnvVar.DHCORE_PASSWORD.value]
            kwargs["auth"] = (user, password)
        elif auth_type == AuthType.OAUTH2.value:
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            access_token = creds[CredsEnvVar.DHCORE_ACCESS_TOKEN.value]
            kwargs["headers"]["Authorization"] = f"Bearer {access_token}"
        return kwargs

    def get_new_access_token(self, change_origin: bool = False) -> None:
        """
        Get a new access token.

        Parameters
        ----------
        change_origin : bool, optional
            Whether to change the origin, by default False

        Returns
        -------
        None
        """
        # Call issuer and get endpoint for
        # refreshing access token
        url = self._get_refresh_endpoint()

        creds = self._creds_handler.get_credentials(self._origin)
        auth_type = self._eval_auth_type(creds)

        # Here should go the handling of token exchange or refresh
        if auth_type == AuthType.OAUTH2.value:
            refresh_token = creds.get(CredsEnvVar.DHCORE_REFRESH_TOKEN.value)
        else:
            raise NotImplementedError("Token exchange not implemented yet.")

        # Call refresh token endpoint
        response = self._call_refresh_token_endpoint(url, refresh_token)

        # Change origin of creds if needed
        if response.status_code in (400, 401, 403):
            if not change_origin:
                raise ClientError("Unable to refresh token. Please check your credentials.")

            self.change_origin()
            self.get_new_access_token(change_origin=False)

        response.raise_for_status()

        # Read new credentials and propagate to config file
        self._export_new_creds(response.json())

    def _export_new_creds(self, response: dict) -> None:
        """
        Set new credentials.

        Parameters
        ----------
        response : dict
            Response from refresh token endpoint.

        Returns
        -------
        None
        """
        creds_handler.write_env(response)
        self.load_file_vars()

    def _remove_prefix_dhcore(self) -> list[str]:
        """
        Remove prefix from selected keys. (Compatibility with CLI)

        Parameters
        ----------
        keys : list[str]
            List of keys.

        Returns
        -------
        list[str]
            List of keys without prefix.
        """
        new_list = []
        for key in self.keys:
            if key in self.keys_to_unprefix:
                new_list.append(key.removeprefix("DHCORE_"))
            else:
                new_list.append(key)
        return new_list

    def _get_refresh_endpoint(self) -> str:
        """
        Get the refresh endpoint.

        Returns
        -------
        str
            Refresh endpoint.
        """
        # Get issuer endpoint
        creds = self._creds_handler.get_credentials(self._origin)
        endpoint_issuer = creds.get(CredsEnvVar.DHCORE_ISSUER.value)
        if endpoint_issuer is None:
            raise ClientError("Issuer endpoint not set.")

        # Standard issuer endpoint path
        url = endpoint_issuer + "/.well-known/openid-configuration"

        # Call issuer to get refresh endpoint
        r = request("GET", url, timeout=60)
        r.raise_for_status()
        return r.json().get("token_endpoint")

    def _call_refresh_token_endpoint(self, url: str, refresh_token: str) -> Response:
        """
        Call the refresh token endpoint.

        Parameters
        ----------
        url : str
            Refresh token endpoint.
        refresh_token : str
            Refresh token.

        Returns
        -------
        Response
            Response object.
        """
        # Get client id
        creds = self._creds_handler.get_credentials(self._origin)
        client_id = creds.get(CredsEnvVar.DHCORE_CLIENT_ID.value)
        if client_id is None:
            raise ClientError("Client id not set.")

        # Send request to get new access token
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
            "scope": "openid credentials offline_access",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return request("POST", url, data=payload, headers=headers, timeout=60)

    def _eval_auth_type(self, creds: dict) -> str | None:
        if creds[CredsEnvVar.DHCORE_PERSONAL_ACCESS_TOKEN.value] is not None:
            return AuthType.EXCHANGE.value
        if (
            creds[CredsEnvVar.DHCORE_ACCESS_TOKEN.value] is not None
            and creds[CredsEnvVar.DHCORE_REFRESH_TOKEN.value] is not None
        ):
            return AuthType.OAUTH2.value
        if creds[CredsEnvVar.DHCORE_USER.value] is not None and creds[CredsEnvVar.DHCORE_PASSWORD.value] is not None:
            return AuthType.BASIC.value
        return None
