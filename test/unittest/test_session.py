# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, wait
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.stores.session as session_module
from digitalhub.context.api import build_context, get_context
from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.common.config import ClientConfig, get_client_config
from digitalhub.stores.client.common.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.data.api import get_store
from digitalhub.stores.session import Session, get_session

# Time other callers are given to overtake a paused first use. With the lock
# they stay blocked, so this only bounds the test; it never decides it.
OVERTAKE_WINDOW = 0.5
JOIN_TIMEOUT = 5

STORE_CREDENTIALS = {
    ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example",
    CredentialsVars.S3_ACCESS_KEY_ID.value: "access",
    CredentialsVars.S3_SECRET_ACCESS_KEY.value: "secret",
}


def _identity() -> Mock:
    identity = Mock(spec=ClientConfigurator)
    identity.get_endpoint.return_value = "https://core.example"
    identity.authenticate.side_effect = lambda request: request
    identity.get_credentials_and_config.return_value = STORE_CREDENTIALS
    return identity


@pytest.fixture
def session(monkeypatch) -> Session:
    """Replace the process session with one on a fake transport and identity."""
    current = Session(transport=Mock(), identity=_identity())
    monkeypatch.setattr(session_module, "_session", current)
    return current


def _pause_first_call(factory: Callable) -> tuple[Callable, threading.Event, threading.Event, list]:
    """Wrap a factory so its first call waits until resumed; record every call."""
    paused = threading.Event()
    resume = threading.Event()
    calls: list = []

    def wrapper(*args, **kwargs):
        calls.append(args)
        if not paused.is_set():
            paused.set()
            resume.wait(JOIN_TIMEOUT)
        return factory(*args, **kwargs)

    return wrapper, paused, resume, calls


def _call_concurrently(target: Callable, paused: threading.Event, resume: threading.Event) -> list:
    with ThreadPoolExecutor(max_workers=8) as pool:
        first = pool.submit(target)
        assert paused.wait(JOIN_TIMEOUT)
        others = [pool.submit(target) for _ in range(7)]
        wait(others, timeout=OVERTAKE_WINDOW)
        resume.set()
        return [future.result(timeout=JOIN_TIMEOUT) for future in (first, *others)]


def test_get_session_builds_one_session_under_concurrent_first_use(monkeypatch) -> None:
    monkeypatch.setattr(session_module, "_session", None)
    factory, paused, resume, calls = _pause_first_call(lambda config: Session(config, transport=Mock()))
    monkeypatch.setattr(session_module, "Session", factory)

    sessions = _call_concurrently(get_session, paused, resume)

    assert len(calls) == 1
    assert all(session is sessions[0] for session in sessions)
    assert sessions[0].config is get_client_config()


def test_first_client_is_built_once_under_concurrent_use(monkeypatch) -> None:
    factory, paused, resume, calls = _pause_first_call(lambda transport, config: _identity())
    monkeypatch.setattr(session_module, "ClientConfigurator", factory)
    session = Session(transport=Mock())

    clients = _call_concurrently(session.client, paused, resume)

    assert len(calls) == 1
    assert all(client is clients[0] for client in clients)


def test_configure_rebuilds_client_and_identity_and_keeps_pool_and_contexts(monkeypatch) -> None:
    identity_factory = Mock(side_effect=lambda transport, config: _identity())
    monkeypatch.setattr(session_module, "ClientConfigurator", identity_factory)
    transport = Mock()
    session = Session(transport=transport)
    first = session.client()
    contexts = session.contexts
    config = ClientConfig(http_timeout=3)

    session.configure(config)
    second = session.client()

    assert second is not first
    assert second._config is config
    assert second._transport is transport
    assert session.contexts is contexts
    assert [call.args for call in identity_factory.call_args_list] == [
        (transport, ClientConfig()),
        (transport, config),
    ]


def test_configure_keeps_a_given_identity() -> None:
    identity = _identity()
    session = Session(transport=Mock(), identity=identity)

    session.configure(ClientConfig(http_timeout=3))

    assert session.client()._auth is identity


def test_contexts_live_in_the_session(session, tmp_path) -> None:
    project = SimpleNamespace(name="demo", spec=SimpleNamespace(config={}, source=str(tmp_path)))

    context = build_context(project)

    assert get_context("demo") is context
    assert session.contexts.get("demo") is context


def test_stores_are_built_once_per_type_with_the_session_credentials(session) -> None:
    store = get_store("s3://bucket/key", "demo")

    assert store.get_credentials(lowercase_keys=False)[CredentialsVars.S3_ACCESS_KEY_ID.value] == "access"
    assert get_store("s3://bucket/other") is store
    assert session.store("s3://bucket/key") is store


def test_store_credentials_refresh_through_the_user_identity() -> None:
    identity = _identity()
    identity.evaluate_refresh.return_value = True
    session = Session(transport=Mock(), identity=identity)

    assert session.store_credentials("demo").refresh() is True
    identity.evaluate_refresh.assert_called_once_with(check_token_validity=True)
