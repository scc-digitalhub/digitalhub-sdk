# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.utils.exceptions import BackendError


class ClientApiBuilder:
    """
    This class is used to build the API for the DHCore client.
    """

    def build_api(self, category: ApiType, operation: BEOps, **kwargs) -> str:
        """
        Build the API for the client.

        Parameters
        ----------
        category : ApiType
            API category.
        operation : BackendOperations
            API operation.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            API formatted.
        """
        match category:
            case ApiType.BASE:
                return self.build_api_base(operation, **kwargs)
            case _:
                return self.build_api_context(operation, **kwargs)

    def build_api_base(self, operation: BEOps, **kwargs) -> str:
        """
        Build the base API for the client.

        Parameters
        ----------
        operation : BackendOperations
            API operation.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            API formatted.
        """
        api_base = get_client_config().api_base
        entity_type = kwargs["entity_type"] + "s"
        match operation:
            case BEOps.CREATE | BEOps.LIST:
                return f"{api_base}/{entity_type}"
            case BEOps.READ | BEOps.UPDATE | BEOps.DELETE:
                return f"{api_base}/{entity_type}/{kwargs['entity_name']}"
            case BEOps.SHARE:
                return f"{api_base}/{entity_type}/{kwargs['entity_name']}/share"
            case _:
                raise BackendError(f"Invalid operation '{operation}' for entity type '{entity_type}' in DHCore.")

    def build_api_context(self, operation: BEOps, **kwargs) -> str:
        """
        Build the context API for the client.

        Parameters
        ----------
        operation : BackendOperations
            The API operation.
        **kwargs : dict
            Additional parameters including project, entity_type, entity_id, etc.

        Returns
        -------
        str
            The formatted context API endpoint.
        """
        api_context = get_client_config().api_context
        project = kwargs["project"]
        entity_type = kwargs["entity_type"] + "s"
        match operation:
            case BEOps.SEARCH:
                return f"{api_context}/{project}/solr/search/item"
            case BEOps.CREATE | BEOps.LIST | BEOps.DELETE_ALL_VERSIONS:
                return f"{api_context}/{project}/{entity_type}"
            case BEOps.READ | BEOps.UPDATE | BEOps.DELETE:
                return f"{api_context}/{project}/{entity_type}/{kwargs['entity_id']}"
            case BEOps.LOGS:
                return f"{api_context}/{project}/{entity_type}/{kwargs['entity_id']}/logs"
            case BEOps.STOP:
                return f"{api_context}/{project}/{entity_type}/{kwargs['entity_id']}/stop"
            case BEOps.RESUME:
                return f"{api_context}/{project}/{entity_type}/{kwargs['entity_id']}/resume"
            case BEOps.DATA:
                return f"{api_context}/{project}/{entity_type}/data"
            case BEOps.FILES:
                return f"{api_context}/{project}/{entity_type}/{kwargs['entity_id']}/files/info"
            case BEOps.METRICS:
                metric_name = kwargs["metric_name"]
                if metric_name is None:
                    return f"{api_context}/{project}/{entity_type}/{kwargs['entity_id']}/metrics"
                return f"{api_context}/{project}/{entity_type}/{kwargs['entity_id']}/metrics/{metric_name}"
            case _:
                raise BackendError(f"Invalid operation '{operation}' in DHCore.")
