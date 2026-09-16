# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.common.enums import ApiType
from digitalhub.stores.client.compiler.options import OperationOptions
from digitalhub.stores.client.compiler.params.profile import ParamsProfile
from digitalhub.stores.client.compiler.params.state import ParameterState
from digitalhub.stores.client.compiler.params.strategies import ListParameterStrategy, SearchParameterStrategy


class ClientParametersBuilder:
    """
    Parameter builder for DHCore client API calls.
    """

    def __init__(self) -> None:
        self._search_strategy = SearchParameterStrategy()
        self._list_strategy = ListParameterStrategy()

    def build_parameters(self, category: ApiType, profile: ParamsProfile, options: OperationOptions) -> dict:
        """
        Build HTTP request parameters for DHCore API calls.
        """
        kwargs = options.to_values()
        match category:
            case ApiType.BASE:
                return self.build_parameters_base(profile, **kwargs)
            case _:
                return self.build_parameters_context(profile, **kwargs)

    def build_parameters_base(self, profile: ParamsProfile, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for project operations.
        """
        state = ParameterState.from_kwargs(kwargs)

        match profile:
            case ParamsProfile.DELETE:
                cascade, state = state.pop("cascade", None)
                if cascade is not None:
                    state = state.with_param("cascade", str(cascade).lower())
            case ParamsProfile.SHARE:
                user, state = state.pop("user")
                state = state.with_param("user", user)
                unshare, state = state.pop("unshare", False)
                if unshare:
                    entity_id, state = state.pop("share_id")
                    state = state.with_param("id", entity_id)
                else:
                    role, state = state.pop("role", None)
                    if role is not None:
                        state = state.with_param("role", role)

        return state.to_kwargs()

    def build_parameters_context(self, profile: ParamsProfile, **kwargs) -> dict:
        """
        Constructs HTTP request parameters for entity management and search within
        projects.
        """
        state = ParameterState.from_kwargs(kwargs)

        match profile:
            case ParamsProfile.READ:
                name, state = state.pop("name", None)
                if name is not None:
                    state = state.with_param("name", name)
            case ParamsProfile.READ_ALL_VERSIONS:
                state = state.with_param("versions", "all")
                name, state = state.pop("name")
                state = state.with_param("name", name)
            case ParamsProfile.LIST:
                state = self._list_strategy.build(state)
                list_params, state = state.pop("list_params", {})
                for key, value in list_params.items():
                    state = state.with_param(key, value)
            case ParamsProfile.DELETE:
                cascade, state = state.pop("cascade", None)
                if cascade is not None:
                    state = state.with_param("cascade", str(cascade).lower())
            case ParamsProfile.DELETE_ALL_VERSIONS:
                cascade, state = state.pop("cascade", None)
                if cascade is not None:
                    state = state.with_param("cascade", str(cascade).lower())
                name, state = state.pop("name")
                state = state.with_param("name", name)
            case ParamsProfile.SEARCH:
                fq, state = state.pop("fq", None)
                if fq is not None:
                    state = state.with_param("fq", fq)

                state_value, state = state.pop("state", None)
                if state_value is not None:
                    state = state.with_param("state", state_value)

                query, state = state.pop("query", None)
                if query is not None:
                    state = state.with_param("q", query)

                state = self._search_strategy.build(state)
                fq, state = state.pop("fq", [])
                state = state.with_param("fq", fq)
            case ParamsProfile.LOGS:
                state_value, state = state.pop("state", None)
                if state_value is not None:
                    state = state.with_param("state", state_value)
            case ParamsProfile.METRICS:
                user, state = state.pop("user", None)
                if user is not None:
                    state = state.with_param("user", user)
            case ParamsProfile.STOP_RESUME:
                reason, state = state.pop("reason", None)
                if reason is not None:
                    state = state.with_param("reason", reason)

        return state.to_kwargs()
