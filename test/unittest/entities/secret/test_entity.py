# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities.secret._base.entity as entity_module
from digitalhub.entities.secret._base.entity import Secret


def test_set_secret_value_delegates_to_processor(monkeypatch) -> None:
    processor = Mock()
    monkeypatch.setattr(entity_module, "SecretProcessor", Mock(return_value=processor))
    entity = SimpleNamespace()

    Secret.set_secret_value(entity, "secret")

    processor.set_secret_value.assert_called_once_with(entity, "secret")


def test_read_secret_value_delegates_to_processor(monkeypatch) -> None:
    processor = Mock()
    processor.read_secret_value.return_value = "secret"
    monkeypatch.setattr(entity_module, "SecretProcessor", Mock(return_value=processor))
    entity = SimpleNamespace()

    result = Secret.read_secret_value(entity)

    assert result == "secret"
    processor.read_secret_value.assert_called_once_with(entity)
