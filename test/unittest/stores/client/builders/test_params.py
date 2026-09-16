# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.stores.client.common.enums import ApiType
from digitalhub.stores.client.compiler.options import OpaqueOptions
from digitalhub.stores.client.compiler.params.builder import ClientParametersBuilder
from digitalhub.stores.client.compiler.params.profile import ParamsProfile


def test_build_parameters_does_not_mutate_input_params() -> None:
    options = OpaqueOptions({"params": {"existing": "value"}, "name": "demo"})

    result = ClientParametersBuilder().build_parameters(
        ApiType.CONTEXT,
        ParamsProfile.READ,
        options,
    )

    assert options.values == {"params": {"existing": "value"}, "name": "demo"}
    assert result == {"params": {"existing": "value", "name": "demo"}}


def test_build_list_parameters_preserves_filtered_output() -> None:
    result = ClientParametersBuilder().build_parameters(
        ApiType.CONTEXT,
        ParamsProfile.LIST,
        OpaqueOptions({"params": {"page": 2}, "q": "demo", "state": "READY"}),
    )

    assert result == {"params": {"page": 2, "q": "demo", "state": "READY"}}


def test_build_search_parameters_preserves_filter_output() -> None:
    result = ClientParametersBuilder().build_parameters(
        ApiType.CONTEXT,
        ParamsProfile.SEARCH,
        OpaqueOptions(
            {
                "params": {"page": 1},
                "query": "demo",
                "entity_types": ["artifact", "model"],
                "labels": ["team:a", "env:test"],
            }
        ),
    )

    assert result == {
        "params": {
            "page": 1,
            "q": "demo",
            "fq": [
                "type:(artifact OR model)",
                "metadata.updated:[* TO *]",
                "metadata.labels:(team:a AND env:test)",
            ],
        }
    }


def test_build_parameters_rejects_transport_options() -> None:
    with pytest.raises(ValueError, match="Unsupported backend parameters: timeout"):
        ClientParametersBuilder().build_parameters(
            ApiType.CONTEXT,
            ParamsProfile.LIST,
            OpaqueOptions({"timeout": 4}),
        )
