from __future__ import annotations

import typing
from typing import Any

from requests import request
from requests.exceptions import JSONDecodeError

from digitalhub.client._base.client import Client
from digitalhub.client.dhcore.api_builder import ClientDHCoreApiBuilder
from digitalhub.client.dhcore.configurator import ClientDHCoreConfigurator
from digitalhub.client.dhcore.error_parser import ErrorParser
from digitalhub.client.dhcore.key_builder import ClientDHCoreKeyBuilder
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.generic_utils import dump_json

if typing.TYPE_CHECKING:
    from requests import Response


class ClientDHCore(Client):
    """
    DHCore client.

    The DHCore client is used to communicate with the Digitalhub Core
    backendAPI via REST. The client supports basic authentication and
    OAuth2 token authentication with token refresh.
    At creation, the client tries to get the endpoint and authentication
    parameters from the .dhcore file and the environment variables. In
    case the user incours into an authentication/endpoint error during
    the client creation, the user has the possibility to update the
    correct parameters using the `set_dhcore_env` function. If the DHCore
    client is already initialized, this function will override the
    configuration, otherwise it simply set the environment variables.
    """

    def __init__(self, config: dict | None = None) -> None:
        super().__init__()

        # API builder
        self._api_builder = ClientDHCoreApiBuilder()

        # Key builder
        self._key_builder = ClientDHCoreKeyBuilder()

        # Error parser
        self._error_parser = ErrorParser()

        # Client Configurator
        self._configurator = ClientDHCoreConfigurator()
        self._configurator.configure(config)

    ##############################
    # CRUD methods
    ##############################

    def create_object(self, api: str, obj: Any, **kwargs) -> dict:
        """
        Create an object in DHCore.

        Parameters
        ----------
        api : str
            Create API.
        obj : Any
            Object to create.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        dict
            Response object.
        """
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Content-Type"] = "application/json"
        kwargs["data"] = dump_json(obj)
        return self._prepare_call("POST", api, **kwargs)

    def read_object(self, api: str, **kwargs) -> dict:
        """
        Get an object from DHCore.

        Parameters
        ----------
        api : str
            Read API.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        dict
            Response object.
        """
        return self._prepare_call("GET", api, **kwargs)

    def update_object(self, api: str, obj: Any, **kwargs) -> dict:
        """
        Update an object in DHCore.

        Parameters
        ----------
        api : str
            Update API.
        obj : dict
            Object to update.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        dict
            Response object.
        """
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Content-Type"] = "application/json"
        kwargs["data"] = dump_json(obj)
        return self._prepare_call("PUT", api, **kwargs)

    def delete_object(self, api: str, **kwargs) -> dict:
        """
        Delete an object from DHCore.

        Parameters
        ----------
        api : str
            Delete API.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        dict
            Response object.
        """
        resp = self._prepare_call("DELETE", api, **kwargs)
        if isinstance(resp, bool):
            resp = {"deleted": resp}
        return resp

    def list_objects(self, api: str, **kwargs) -> list[dict]:
        """
        List objects from DHCore.

        Parameters
        ----------
        api : str
            List API.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        list[dict]
            Response objects.
        """
        if kwargs is None:
            kwargs = {}

        if "params" not in kwargs:
            kwargs["params"] = {}

        start_page = 0
        if "page" not in kwargs["params"]:
            kwargs["params"]["page"] = start_page

        objects = []
        while True:
            resp = self._prepare_call("GET", api, **kwargs)
            contents = resp["content"]
            total_pages = resp["totalPages"]
            if not contents or kwargs["params"]["page"] >= total_pages:
                break
            objects.extend(contents)
            kwargs["params"]["page"] += 1

        return objects

    def list_first_object(self, api: str, **kwargs) -> dict:
        """
        List first objects.

        Parameters
        ----------
        api : str
            The api to list the objects with.
        **kwargs : dict
            Keyword arguments passed to the request.

        Returns
        -------
        dict
            The list of objects.
        """
        try:
            return self.list_objects(api, **kwargs)[0]
        except IndexError:
            raise BackendError("No object found.")

    def search_objects(self, api: str, **kwargs) -> list[dict]:
        """
        Search objects from DHCore.

        Parameters
        ----------
        api : str
            Search API.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        list[dict]
            Response objects.
        """
        if kwargs is None:
            kwargs = {}

        if "params" not in kwargs:
            kwargs["params"] = {}

        start_page = 0
        if "page" not in kwargs["params"]:
            kwargs["params"]["page"] = start_page

        if "size" not in kwargs["params"]:
            kwargs["params"]["size"] = 10

        # Add sorting
        if "sort" not in kwargs["params"]:
            kwargs["params"]["sort"] = "metadata.updated,DESC"

        objects_with_highlights: list[dict] = []
        while True:
            resp = self._prepare_call("GET", api, **kwargs)
            contents = resp["content"]
            total_pages = resp["totalPages"]
            if not contents or kwargs["params"]["page"] >= total_pages:
                break
            objects_with_highlights.extend(contents)
            kwargs["params"]["page"] += 1

        objects = []
        for obj in objects_with_highlights:
            obj.pop("highlights", None)
            objects.append(obj)

        return objects

    ##############################
    # Call methods
    ##############################

    def _prepare_call(self, call_type: str, api: str, **kwargs) -> dict:
        """
        Prepare a call to the DHCore API.

        Parameters
        ----------
        call_type : str
            The type of call to prepare.
        api : str
            The api to call.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        dict
            Response object.
        """
        if kwargs is None:
            kwargs = {}
        url = self._configurator.build_url(api)
        kwargs = self._configurator.set_request_auth(kwargs)
        return self._make_call(call_type, url, **kwargs)

    def _make_call(self, call_type: str, url: str, refresh_token: bool = True, **kwargs) -> dict:
        """
        Make a call to the DHCore API.

        Parameters
        ----------
        call_type : str
            The type of call to make.
        url : str
            The URL to call.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        dict
            Response object.
        """
        # Call the API
        response = request(call_type, url, timeout=60, **kwargs)

        # Evaluate DHCore API version
        self._configurator.check_core_version(response)

        # Handle token refresh
        if response.status_code in [401] and refresh_token and self._configurator.oauth2_auth():
            self._configurator.get_new_access_token()
            kwargs = self._configurator.set_request_auth(kwargs)
            return self._make_call(call_type, url, refresh_token=False, **kwargs)

        self._error_parser.parse(response)
        return self._dictify_response(response)

    def _dictify_response(self, response: Response) -> dict:
        """
        Return dict from response.

        Parameters
        ----------
        response : Response
            The response object.

        Returns
        -------
        dict
            The parsed response object.
        """
        try:
            return response.json()
        except JSONDecodeError:
            if response.text == "":
                return {}
            raise BackendError("Backend response could not be parsed.")

    ##############################
    # Interface methods
    ##############################

    @staticmethod
    def is_local() -> bool:
        """
        Declare if Client is local.

        Returns
        -------
        bool
            False
        """
        return False
