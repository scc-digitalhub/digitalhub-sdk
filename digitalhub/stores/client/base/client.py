# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.builders.api import ClientApiBuilder
from digitalhub.stores.client.builders.key import ClientKeyBuilder
from digitalhub.stores.client.builders.params import ClientParametersBuilder
from digitalhub.stores.client.common.utils import (
    increment_page_number,
    read_page_number,
    set_json_content_type,
    set_pagination,
)
from digitalhub.stores.client.http.handler import HttpRequestHandler
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.generic_utils import dump_json


class Client:
    """
    DHCore client for remote DigitalHub Core backend communication.

    Provides REST API communication with DigitalHub Core backend supporting
    multiple authentication methods: Basic (username/password), OAuth2 (token
    with refresh), and Personal Access Token exchange. Automatically handles
    API version compatibility, pagination, token refresh, error parsing, and
    JSON serialization.

    Supports dependency injection for testing and customization. All dependencies
    are optional and will be created with default implementations if not provided.
    """

    def __init__(
        self,
        configurator: ClientConfigurator | None = None,
        api_builder: ClientApiBuilder | None = None,
        key_builder: ClientKeyBuilder | None = None,
        params_builder: ClientParametersBuilder | None = None,
        http_handler: HttpRequestHandler | None = None,
    ) -> None:
        """
        Initialize DHCore client with optional dependency injection.

        Parameters
        ----------
        configurator : ClientConfigurator
            Configurator for credentials and authentication. If None, creates default instance.
        api_builder : ClientApiBuilder
            Builder for API endpoints. If None, creates default instance.
        key_builder : ClientKeyBuilder
            Builder for entity keys. If None, creates default instance.
        params_builder : ClientParametersBuilder
            Builder for request parameters. If None, creates default instance.
        http_handler : HttpRequestHandler
            Handler for HTTP requests. If None, creates default instance using configurator.
        """
        # Configurator
        self._configurator = configurator if configurator is not None else ClientConfigurator()

        # API, key and parameters builders
        self._api_builder = api_builder if api_builder is not None else ClientApiBuilder()
        self._key_builder = key_builder if key_builder is not None else ClientKeyBuilder()
        self._params_builder = params_builder if params_builder is not None else ClientParametersBuilder()

        # HTTP request handling
        self._http_handler = http_handler if http_handler is not None else HttpRequestHandler(self._configurator)

    ##############################
    # CRUD methods
    ##############################

    def create_object(self, api: str, obj: Any, **kwargs) -> dict:
        """
        Create an object in DHCore via POST request.

        Automatically sets Content-Type header and serializes object to JSON.

        Parameters
        ----------
        api : str
            API endpoint path for creating the object.
        obj : Any
            Object to create. Will be serialized to JSON.
        **kwargs : dict
            Additional HTTP request arguments.

        Returns
        -------
        dict
            Created object as returned by the backend.
        """
        kwargs = set_json_content_type(**kwargs)
        kwargs["data"] = dump_json(obj)
        return self._http_handler.execute_request("POST", api, **kwargs)

    def read_object(self, api: str, **kwargs) -> dict:
        """
        Get an object from DHCore.

        Sends a GET request to the DHCore backend to retrieve an existing object.

        Parameters
        ----------
        api : str
            API endpoint path for reading the object.
        **kwargs : dict
            Additional HTTP request arguments.

        Returns
        -------
        dict
            Retrieved object as returned by the backend.

        Raises
        ------
        BackendError
            If the backend returns an error response.
        EntityNotExistsError
            If the requested object does not exist.
        """
        return self._http_handler.execute_request("GET", api, **kwargs)

    def update_object(self, api: str, obj: Any, **kwargs) -> dict:
        """
        Update an object in DHCore via PUT request.

        Automatically sets Content-Type header and serializes object to JSON.

        Parameters
        ----------
        api : str
            API endpoint path for updating the object.
        obj : Any
            Updated object data. Will be serialized to JSON.
        **kwargs : dict
            Additional HTTP request arguments.

        Returns
        -------
        dict
            Updated object as returned by the backend.
        """
        kwargs = set_json_content_type(**kwargs)
        kwargs["data"] = dump_json(obj)
        return self._http_handler.execute_request("PUT", api, **kwargs)

    def delete_object(self, api: str, **kwargs) -> dict:
        """
        Delete an object from DHCore.

        Sends DELETE request to remove an object. Wraps boolean responses
        in {"deleted": True/False} dictionary.

        Parameters
        ----------
        api : str
            API endpoint path for deleting the object.
        **kwargs : dict
            Additional HTTP request arguments.

        Returns
        -------
        dict
            Deletion result from backend or {"deleted": bool} wrapper.
        """
        resp = self._http_handler.execute_request("DELETE", api, **kwargs)
        if isinstance(resp, bool):
            resp = {"deleted": resp}
        return resp

    def list_objects(self, api: str, **kwargs) -> list[dict]:
        """
        List objects from DHCore with automatic pagination.

        Sends GET requests to retrieve paginated objects, automatically handling
        pagination (starting from page 0) until all objects are retrieved.

        Parameters
        ----------
        api : str
            API endpoint path for listing objects.
        **kwargs : dict
            Additional HTTP request arguments. Can include 'params' dict
            with pagination parameters.

        Returns
        -------
        list[dict]
            List containing all objects from all pages.
        """
        kwargs = set_pagination(partial=True, **kwargs)

        objects = []
        while True:
            resp = self._http_handler.execute_request("GET", api, **kwargs)
            contents = resp["content"]
            total_pages = resp["totalPages"]
            objects.extend(contents)
            if not contents or read_page_number(**kwargs) >= (total_pages - 1):
                break
            increment_page_number(**kwargs)

        return objects

    def list_first_object(self, api: str, **kwargs) -> dict:
        """
        Get the first object from a DHCore list.

        Retrieves the first object by calling list_objects and returning
        the first item.

        Parameters
        ----------
        api : str
            API endpoint path for listing objects.
        **kwargs : dict
            Additional HTTP request arguments.

        Returns
        -------
        dict
            First object from the list.
        """
        try:
            return self.list_objects(api, **kwargs)[0]
        except IndexError:
            raise BackendError("No object found.")

    def search_objects(self, api: str, **kwargs) -> list[dict]:
        """
        Search objects from DHCore using Solr capabilities.

        Performs search query with pagination and removes search highlights.
        Sets default pagination (page=0, size=10) and sorting (metadata.updated DESC)
        if not provided.

        Parameters
        ----------
        api : str
            API endpoint path for searching objects (usually Solr search).
        **kwargs : dict
            Additional HTTP request arguments including search parameters,
            filters, and pagination options.

        Returns
        -------
        list[dict]
            List of matching objects with search highlights removed.
        """
        kwargs = set_pagination(**kwargs)
        objects_with_highlights: list[dict] = []
        while True:
            resp = self._http_handler.execute_request("GET", api, **kwargs)
            contents = resp["content"]
            total_pages = resp["totalPages"]
            objects_with_highlights.extend(contents)
            if not contents or read_page_number(**kwargs) >= (total_pages - 1):
                break
            increment_page_number(**kwargs)

        objects = []
        for obj in objects_with_highlights:
            obj.pop("highlights", None)
            objects.append(obj)

        return objects

    ##############################
    # Build methods
    ##############################

    def build_api(self, category: str, operation: str, **kwargs) -> str:
        """
        Build the API for the client.

        Parameters
        ----------
        category : str
            API category.
        operation : str
            API operation.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            API formatted.
        """
        return self._api_builder.build_api(category, operation, **kwargs)

    def build_key(self, category: str, *args, **kwargs) -> str:
        """
        Build the key for the client.

        Parameters
        ----------
        category : str
            Key category.
        *args : tuple
            Additional arguments.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            Key formatted.
        """
        return self._key_builder.build_key(category, *args, **kwargs)

    def build_parameters(self, category: str, operation: str, **kwargs) -> dict:
        """
        Build the parameters for the client call.

        Parameters
        ----------
        category : str
            API category.
        operation : str
            API operation.
        **kwargs : dict
            Parameters to build.

        Returns
        -------
        dict
            Parameters formatted.
        """
        return self._params_builder.build_parameters(category, operation, **kwargs)

    ##############################
    # Facade methods
    ##############################

    def eval_retry(self) -> None:
        """
        Evaluate the status of retry lifecycle.
        """
        self._configurator.evaluate_refresh()

    def refresh_token(self) -> None:
        """
        Manually trigger OAuth2 token refresh.
        """
        self._configurator.evaluate_refresh()

    def get_credentials_and_config(self) -> dict:
        """
        Get current authentication credentials and configuration.
        Eventually refreshes tokens if expired.

        Returns
        -------
        dict
            Current authentication credentials and configuration.
        """
        return self._configurator.get_credentials_and_config()

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile.

        Parameters
        ----------
        profile : str
            Name of the credentials profile to set.
        """
        self._configurator.set_current_profile(profile)

    def get_current_profile(self) -> str:
        """
        Get the name of the current credentials profile.

        Returns
        -------
        str
            Name of the current credentials profile.
        """
        return self._configurator.get_current_profile()
