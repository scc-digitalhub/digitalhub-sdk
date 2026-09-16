# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.targets import (
    BaseCollectionTarget,
    BaseEntityTarget,
    ContextCollectionTarget,
    ContextEntityTarget,
    ContextMetricTarget,
    ContextProjectTarget,
    RouteTarget,
)
from digitalhub.utils.exceptions import BackendError


class ClientApiBuilder:
    """
    This class is used to build the API for the DHCore client.
    """

    def build_api(self, category: ApiType, operation: BackendOp, target: RouteTarget) -> str:
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
                return self.build_api_base(operation, target)
            case _:
                return self.build_api_context(operation, target)

    def build_api_base(self, operation: BackendOp, target: RouteTarget) -> str:
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
        match operation, target:
            case BackendOp.CREATE | BackendOp.LIST, BaseCollectionTarget(entity_type):
                return f"{api_base}/{entity_type}s"
            case BackendOp.READ | BackendOp.UPDATE | BackendOp.DELETE | BackendOp.SHARE, BaseEntityTarget(
                entity_type, entity_name
            ):
                suffix = "/share" if operation == BackendOp.SHARE else ""
                return f"{api_base}/{entity_type}s/{entity_name}{suffix}"
            case _:
                raise BackendError(f"Invalid operation '{operation}' for target '{target}' in DHCore.")

    def build_api_context(self, operation: BackendOp, target: RouteTarget) -> str:
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
        match operation, target:
            case BackendOp.SEARCH, ContextProjectTarget(project):
                return f"{api_context}/{project}/solr/search/item"
            case (
                BackendOp.CREATE | BackendOp.LIST | BackendOp.DELETE_ALL_VERSIONS | BackendOp.DATA,
                ContextCollectionTarget(project, entity_type),
            ):
                suffix = "/data" if operation == BackendOp.DATA else ""
                return f"{api_context}/{project}/{entity_type}s{suffix}"
            case BackendOp.READ | BackendOp.UPDATE | BackendOp.DELETE, ContextEntityTarget(
                project, entity_type, entity_id
            ):
                return f"{api_context}/{project}/{entity_type}s/{entity_id}"
            case BackendOp.LOGS, ContextEntityTarget(project, entity_type, entity_id):
                return f"{api_context}/{project}/{entity_type}s/{entity_id}/logs"
            case BackendOp.STOP, ContextEntityTarget(project, entity_type, entity_id):
                return f"{api_context}/{project}/{entity_type}s/{entity_id}/stop"
            case BackendOp.RESUME, ContextEntityTarget(project, entity_type, entity_id):
                return f"{api_context}/{project}/{entity_type}s/{entity_id}/resume"
            case BackendOp.FILES, ContextEntityTarget(project, entity_type, entity_id):
                return f"{api_context}/{project}/{entity_type}s/{entity_id}/files/info"
            case BackendOp.METRICS, ContextMetricTarget(project, entity_type, entity_id, metric_name):
                if metric_name is None:
                    return f"{api_context}/{project}/{entity_type}s/{entity_id}/metrics"
                return f"{api_context}/{project}/{entity_type}s/{entity_id}/metrics/{metric_name}"
            case _:
                raise BackendError(f"Invalid operation '{operation}' for target '{target}' in DHCore.")
