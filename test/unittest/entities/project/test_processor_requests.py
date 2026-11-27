# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.entities.project._base.processor as processor_module
from digitalhub.entities.project._base.processor import ProjectProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import DeleteOptions, NoOptions
from digitalhub.stores.client.compiler.targets import BaseCollectionTarget, BaseEntityTarget


def _project(payload: dict) -> Mock:
    project = Mock(ENTITY_TYPE="project")
    project.name = "demo"
    project.to_dict.return_value = payload
    return project


def _processor() -> ProjectProcessor:
    processor = ProjectProcessor(Mock())
    processor._registered = Mock(return_value="registered")
    return processor


def test_create_project_entity_uses_backend_operation_request(monkeypatch) -> None:
    client = Mock()
    client.execute.return_value = {"id": "project-id"}
    monkeypatch.setattr(processor_module, "resolve_client", Mock(return_value=client))
    project = _project({"name": "demo"})
    processor = _processor()

    assert processor.create_project_entity(project) is project

    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BackendOp.CREATE,
            target=BaseCollectionTarget("project"),
            options=NoOptions(),
            payload={"name": "demo"},
        )
    )
    processor._registered.assert_called_once_with({"id": "project-id"})
    project._update_attributes.assert_called_once_with("registered")


def test_read_project_entity_uses_only_ra(monkeypatch) -> None:
    client = Mock()
    client.execute.return_value = {"name": "demo"}
    monkeypatch.setattr(processor_module, "resolve_client", Mock(return_value=client))
    processor = _processor()

    assert processor.read_project_entity("project", "demo") == "registered"

    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BackendOp.READ,
            target=BaseEntityTarget("project", "demo"),
            options=NoOptions(),
        )
    )
    processor._registered.assert_called_once_with({"name": "demo"})


def test_list_project_entities_uses_paginated_execution(monkeypatch) -> None:
    client = Mock()
    client.execute_list.return_value = [{"name": "demo"}]
    monkeypatch.setattr(processor_module, "resolve_client", Mock(return_value=client))
    build_entity = Mock(return_value="project")
    monkeypatch.setattr(processor_module.entity_factory, "build_entity_from_dict", build_entity)

    assert ProjectProcessor(Mock()).list_project_entities("project") == ["project"]

    client.execute_list.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BackendOp.LIST,
            target=BaseCollectionTarget("project"),
            options=NoOptions(),
        )
    )
    build_entity.assert_called_once_with({"name": "demo"})


def test_update_project_entity_uses_backend_operation_request(monkeypatch) -> None:
    client = Mock()
    client.execute.return_value = {"name": "updated"}
    monkeypatch.setattr(processor_module, "resolve_client", Mock(return_value=client))
    project = _project({"name": "updated"})
    processor = _processor()

    assert processor.update_project_entity(project) is project

    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BackendOp.UPDATE,
            target=BaseEntityTarget("project", "demo"),
            options=NoOptions(),
            payload={"name": "updated"},
        )
    )
    processor._registered.assert_called_once_with({"name": "updated"})
    project._update_attributes.assert_called_once_with("registered")


def test_delete_project_entity_uses_semantic_parameters(monkeypatch) -> None:
    client = Mock()
    client.execute.return_value = {"deleted": True}
    monkeypatch.setattr(processor_module, "resolve_client", Mock(return_value=client))
    monkeypatch.setattr(processor_module, "delete_context", Mock())

    result = ProjectProcessor(Mock()).delete_project_entity("project", "demo", cascade=True)

    assert result == {"deleted": True}
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BackendOp.DELETE,
            target=BaseEntityTarget("project", "demo"),
            options=DeleteOptions(cascade=True),
        )
    )
    processor_module.delete_context.assert_called_once_with("demo")
