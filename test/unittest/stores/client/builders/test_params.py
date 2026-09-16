# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.params.builder import ClientParametersBuilder


def test_build_parameters_does_not_mutate_input_params() -> None:
    input_params = {"existing": "value"}

    result = ClientParametersBuilder().build_parameters(
        ApiType.CONTEXT,
        BEOps.READ,
        params=input_params,
        name="demo",
    )

    assert input_params == {"existing": "value"}
    assert result == {"params": {"existing": "value", "name": "demo"}}


def test_build_list_parameters_preserves_filtered_output() -> None:
    result = ClientParametersBuilder().build_parameters(
        ApiType.CONTEXT,
        BEOps.LIST,
        params={"page": 2},
        q="demo",
        state="READY",
    )

    assert result == {"params": {"page": 2, "q": "demo", "state": "READY"}}


def test_build_search_parameters_preserves_filter_output() -> None:
    result = ClientParametersBuilder().build_parameters(
        ApiType.CONTEXT,
        BEOps.SEARCH,
        params={"page": 1},
        query="demo",
        entity_types=["artifact", "model"],
        labels=["team:a", "env:test"],
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
            BEOps.LIST,
            timeout=4,
        )
