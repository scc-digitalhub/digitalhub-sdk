# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from requests import Response

import digitalhub.context.context as context_module
import digitalhub.stores.session as session_module
from digitalhub.context.api import build_context
from digitalhub.context.context import Context
from digitalhub.entities._processors.context.control import ContextEntityControlProcessor
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.project._base.processor import ProjectProcessor
from digitalhub.stores.client.common.config import ClientConfig
from digitalhub.stores.session import Session


def _response() -> Response:
    response = Response()
    response.status_code = 200
    response.url = "https://core.example/api"
    response.headers = {}
    response._content = b"{}"
    return response


@pytest.fixture
def session(monkeypatch):
    """Replace the process session with one on a recording transport and a pass-through identity."""
    transport = Mock()
    transport.execute.side_effect = lambda request, **_: _response()
    identity = Mock()
    identity.get_endpoint.return_value = "https://core.example"
    identity.authenticate.side_effect = lambda request: request
    current = Session(transport=transport, identity=identity)
    monkeypatch.setattr(session_module, "_session", current)
    return current


def _sent_timeouts(session: Session) -> list:
    return [call.args[0].timeout for call in session._transport.execute.call_args_list]


def _project(tmp_path) -> Project:
    return Project(
        name="demo",
        kind="project",
        metadata=SimpleNamespace(),
        spec=SimpleNamespace(source=str(tmp_path), config={}),
        status=SimpleNamespace(),
    )


def _registered_project(tmp_path) -> Project:
    """A project whose context is registered, as after reading it from the backend."""
    project = _project(tmp_path)
    build_context(project)
    return project


def _context(tmp_path) -> Context:
    return Context(SimpleNamespace(name="demo", spec=SimpleNamespace(config={}, source=str(tmp_path))))


def test_project_construction_does_not_build_a_client(session, monkeypatch, tmp_path) -> None:
    client = Mock(wraps=session.client)
    monkeypatch.setattr(session, "client", client)

    _project(tmp_path)

    client.assert_not_called()


def test_operations_use_the_client_built_after_a_config_change(session, tmp_path) -> None:
    # Before the fix contexts kept the client copied in Project.__init__, so
    # after a configuration change project operations used the new client
    # while context entity operations kept using the old one.
    _registered_project(tmp_path)

    ProjectProcessor().delete_project_entity("project", "demo", clean_context=False)
    ContextEntityControlProcessor().stop_entity("demo", "run", "run-id")

    session.configure(ClientConfig(http_timeout=1))

    ProjectProcessor().delete_project_entity("project", "demo", clean_context=False)
    ContextEntityControlProcessor().stop_entity("demo", "run", "run-id")

    assert _sent_timeouts(session) == [60, 60, 1, 1]


def test_context_resolves_the_client_for_its_project(monkeypatch, tmp_path) -> None:
    client = Mock()
    resolve_client = Mock(return_value=client)
    monkeypatch.setattr(context_module, "resolve_client", resolve_client)

    assert _context(tmp_path).client is client
    resolve_client.assert_called_once_with("demo")
