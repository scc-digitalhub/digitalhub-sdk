from __future__ import annotations

from digitalhub.client._base.api_builder import ClientApiBuilder
from digitalhub.client.local.enums import LocalClientVar
from digitalhub.entities._commons.enums import ApiCategories, BackendOperations
from digitalhub.utils.exceptions import BackendError

API_BASE = "/api/v1"
API_CONTEXT = f"{API_BASE}/-"


class ClientLocalApiBuilder(ClientApiBuilder):
    """
    This class is used to build the API for the Local client.
    """

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
        if category == ApiCategories.BASE.value:
            return self.build_api_base(operation, **kwargs)
        return self.build_api_context(operation, **kwargs)

    def build_api_base(self, operation: str, **kwargs) -> str:
        """
        Build the base API for the client.

        Parameters
        ----------
        operation : str
            API operation.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            API formatted.
        """
        entity_type = kwargs["entity_type"] + "s"
        if operation in (
            BackendOperations.CREATE.value,
            BackendOperations.LIST.value,
        ):
            return f"{API_BASE}/{entity_type}"
        elif operation in (
            BackendOperations.READ.value,
            BackendOperations.UPDATE.value,
            BackendOperations.DELETE.value,
        ):
            return f"{API_BASE}/{entity_type}/{kwargs['entity_name']}"
        raise BackendError(f"API for operation '{operation}' for entity type '{entity_type}' not implemented in Local.")

    def build_api_context(self, operation: str, **kwargs) -> str:
        """
        Build the context API for the client.
        """
        entity_type = kwargs["entity_type"] + "s"
        project = kwargs["project"]
        if operation in (
            BackendOperations.CREATE.value,
            BackendOperations.LIST.value,
        ):
            return f"{API_CONTEXT}/{project}/{entity_type}"
        elif operation in (
            BackendOperations.READ.value,
            BackendOperations.UPDATE.value,
            BackendOperations.DELETE.value,
        ):
            return f"{API_CONTEXT}/{project}/{entity_type}/{kwargs['entity_id']}"
        elif operation in (
            BackendOperations.LOGS.value,
            BackendOperations.FILES.value,
            BackendOperations.METRICS.value,
        ):
            return LocalClientVar.EMPTY.value
        raise BackendError(f"API for operation '{operation}' for entity type '{entity_type}' not implemented in Local.")
