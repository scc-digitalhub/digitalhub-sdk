# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.builders.strategies import ListParameterStrategy, SearchParameterStrategy
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
from digitalhub.stores.client.common.utils import add_param, ensure_params


class ClientParametersBuilder:
    """
    Parameter builder for DHCore client API calls.

    Constructs HTTP request parameters for DHCore API operations, handling
    parameter formats and query structures for both base-level operations
    (project management) and context-level operations (entity operations
    within projects). Uses strategy pattern for complex parameter building.
    """

    def __init__(self) -> None:
        self._search_strategy = SearchParameterStrategy()
        self._list_strategy = ListParameterStrategy()

    def build_parameters(self, category: str, operation: str, **kwargs) -> dict:
        """
        Build HTTP request parameters for DHCore API calls.

        Parameters
        ----------
        category : str
            API category: 'base' for project-level operations or 'context'
            for entity operations within projects.
        operation : str
            Specific API operation (create, read, update, delete, list, search, etc.).
        **kwargs : dict
            Raw parameters to transform including entity identifiers, filter
            criteria, pagination options, etc.

        Returns
        -------
        dict
            Formatted parameters dictionary with 'params' key for query parameters
            and other request-specific parameters.
        """
        if category == ApiCategories.BASE.value:
            return self.build_parameters_base(operation, **kwargs)
        return self.build_parameters_context(operation, **kwargs)

    def build_parameters_base(self, operation: str, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for project operations.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Operation-specific parameters.
        Returns
        -------
        dict
            Formatted parameters with 'params' containing query parameters.
        """
        kwargs = ensure_params(**kwargs)

        # Handle delete
        if operation == BackendOperations.DELETE.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = add_param("cascade", str(cascade).lower(), **kwargs)

        # Handle share
        elif operation == BackendOperations.SHARE.value:
            kwargs = add_param("user", kwargs.pop("user"), **kwargs)
            if kwargs.pop("unshare", False):
                kwargs = add_param("id", kwargs.pop("id"), **kwargs)

        return kwargs

    def build_parameters_context(self, operation: str, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for entity management and search within
        projects.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Operation-specific parameters.

        Returns
        -------
        dict
            Formatted parameters with 'params'.
        """
        kwargs = ensure_params(**kwargs)

        # Handle read
        if operation == BackendOperations.READ.value:
            if (name := kwargs.pop("name", None)) is not None:
                kwargs = add_param("name", name, **kwargs)

        # Handle read all versions
        elif operation == BackendOperations.READ_ALL_VERSIONS.value:
            kwargs = add_param("versions", "all", **kwargs)
            kwargs = add_param("name", kwargs.pop("name"), **kwargs)

        # Handle list
        elif operation == BackendOperations.LIST.value:
            result = self._list_strategy.build(**kwargs)
            list_params = result.pop("list_params", {})
            for k, v in list_params.items():
                kwargs = add_param(k, v, **result)
            kwargs = result

        # Handle delete
        elif operation == BackendOperations.DELETE.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = add_param("cascade", str(cascade).lower(), **kwargs)

        elif operation == BackendOperations.DELETE_ALL_VERSIONS.value:
            if (cascade := kwargs.pop("cascade", None)) is not None:
                kwargs = add_param("cascade", str(cascade).lower(), **kwargs)
            kwargs = add_param("name", kwargs.pop("name"), **kwargs)

        # Handle search
        elif operation == BackendOperations.SEARCH.value:
            # Handle pre-existing fq
            if (fq := kwargs.pop("fq", None)) is not None:
                kwargs = add_param("fq", fq, **kwargs)

            # Add search query
            if (query := kwargs.pop("query", None)) is not None:
                kwargs = add_param("q", query, **kwargs)

            # Build search filters using strategy
            result = self._search_strategy.build(**kwargs)
            fq = result.pop("fq", [])
            kwargs = result

            # Add filters to params
            kwargs = add_param("fq", fq, **kwargs)

        return kwargs
