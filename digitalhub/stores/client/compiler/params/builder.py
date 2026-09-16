# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.params.state import ParameterState
from digitalhub.stores.client.compiler.params.strategies import ListParameterStrategy, SearchParameterStrategy


class ClientParametersBuilder:
    """
    Parameter builder for DHCore client API calls.
    """

    def __init__(self) -> None:
        self._search_strategy = SearchParameterStrategy()
        self._list_strategy = ListParameterStrategy()

    def build_parameters(self, category: ApiType, operation: BEOps, **kwargs) -> dict:
        """
        Build HTTP request parameters for DHCore API calls.
        """
        match category:
            case ApiType.BASE:
                return self.build_parameters_base(operation, **kwargs)
            case _:
                return self.build_parameters_context(operation, **kwargs)

    def build_parameters_base(self, operation: BEOps, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for project operations.
        """
        state = ParameterState.from_kwargs(kwargs)

        match operation:
            case BEOps.DELETE:
                cascade, state = state.pop("cascade", None)
                if cascade is not None:
                    state = state.with_param("cascade", str(cascade).lower())
            case BEOps.SHARE:
                user, state = state.pop("user")
                state = state.with_param("user", user)
                unshare, state = state.pop("unshare", False)
                if unshare:
                    entity_id, state = state.pop("id")
                    state = state.with_param("id", entity_id)
                else:
                    role, state = state.pop("role", None)
                    if role is not None:
                        state = state.with_param("role", role)

        return state.to_kwargs()

    def build_parameters_context(self, operation: BEOps, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for entity management and search within
        projects.
        """
        state = ParameterState.from_kwargs(kwargs)

        match operation:
            case BEOps.READ:
                name, state = state.pop("name", None)
                if name is not None:
                    state = state.with_param("name", name)
            case BEOps.READ_ALL_VERSIONS:
                state = state.with_param("versions", "all")
                name, state = state.pop("name")
                state = state.with_param("name", name)
            case BEOps.LIST:
                state = self._list_strategy.build(state)
                list_params, state = state.pop("list_params", {})
                for key, value in list_params.items():
                    state = state.with_param(key, value)
            case BEOps.DELETE:
                cascade, state = state.pop("cascade", None)
                if cascade is not None:
                    state = state.with_param("cascade", str(cascade).lower())
            case BEOps.DELETE_ALL_VERSIONS:
                cascade, state = state.pop("cascade", None)
                if cascade is not None:
                    state = state.with_param("cascade", str(cascade).lower())
                name, state = state.pop("name")
                state = state.with_param("name", name)
            case BEOps.SEARCH:
                fq, state = state.pop("fq", None)
                if fq is not None:
                    state = state.with_param("fq", fq)

                query, state = state.pop("query", None)
                if query is not None:
                    state = state.with_param("q", query)

                state = self._search_strategy.build(state)
                fq, state = state.pop("fq", [])
                state = state.with_param("fq", fq)
            case BEOps.LOGS:
                state_value, state = state.pop("state", None)
                if state_value is not None:
                    state = state.with_param("state", state_value)
            case BEOps.METRICS:
                user, state = state.pop("user", None)
                if user is not None:
                    state = state.with_param("user", user)
            case BEOps.STOP | BEOps.RESUME:
                reason, state = state.pop("reason", None)
                if reason is not None:
                    state = state.with_param("reason", reason)

        return state.to_kwargs()
