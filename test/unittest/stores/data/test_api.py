# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.stores.data.api as data_api
from digitalhub.stores.client.common.enums import ConfigurationVars


def test_default_store_uri_prefers_project_config(monkeypatch) -> None:
    var = ConfigurationVars.DEFAULT_FILES_STORE.value
    key = var.lower().replace("dhcore_", "")
    client = Mock()
    monkeypatch.setattr(data_api, "get_client", Mock(return_value=client))

    assert data_api.get_default_store_uri({key: "s3://project-store"}) == "s3://project-store"
    client.get_credentials_and_config.assert_not_called()


def test_default_store_uri_falls_back_to_client_config(monkeypatch) -> None:
    var = ConfigurationVars.DEFAULT_FILES_STORE.value
    client = Mock()
    client.get_credentials_and_config.return_value = {var: "s3://client-store"}
    monkeypatch.setattr(data_api, "get_client", Mock(return_value=client))

    assert data_api.get_default_store_uri({}) == "s3://client-store"
    client.get_credentials_and_config.assert_called_once_with()
