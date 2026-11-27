# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import json
import threading

from requests import Response

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.client import Client
from digitalhub.stores.client.common.config import ClientConfig
from digitalhub.stores.client.common.enums import (
    ApiType,
    BackendOp,
    ConfigurationVars,
    CredentialSource,
    CredentialsVars,
)
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.targets import BaseEntityTarget
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.generic_utils import list_enum

READ_PROJECT = ClientOp(
    category=ApiType.BASE,
    operation=BackendOp.READ,
    target=BaseEntityTarget("project", "demo"),
)

# Long enough for a second refresh to arrive when refreshes are not serialized.
OVERLAP_WINDOW = 0.5
JOIN_TIMEOUT = 10


class SingleUseRefreshCore:
    """
    Backend whose access token A0 has expired and whose refresh tokens work
    once, like Core's ``RefreshTokenGranter``.

    The first requests wait for each other, so both threads are rejected with
    the old token. The first refresh stays in flight for a while, so a second
    refresh, if any, overlaps it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._first_requests = threading.Barrier(2, timeout=JOIN_TIMEOUT)
        self._second_refresh = threading.Event()
        self.valid_access: set[str] = set()
        self.valid_refresh = {"R0"}
        self.refreshes: list[str] = []

    def execute(self, request, attempt: int = 1, retry_reason: str | None = None) -> Response:
        if request.api.endswith("/auth/token"):
            return self._refresh(request.data["refresh_token"])
        if attempt == 1:
            self._first_requests.wait()
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        with self._lock:
            valid = token in self.valid_access
        return _response(200, {"name": "demo"}) if valid else _response(401, {"status": 401})

    def _refresh(self, token: str) -> Response:
        with self._lock:
            self.refreshes.append(token)
            first = len(self.refreshes) == 1
        if first:
            self._second_refresh.wait(OVERLAP_WINDOW)
        else:
            self._second_refresh.set()
        with self._lock:
            if token not in self.valid_refresh:
                return _response(400, {"error": "invalid_grant"})
            self.valid_refresh.discard(token)
            number = len(self.valid_access) + 1
            self.valid_access.add(f"A{number}")
            self.valid_refresh.add(f"R{number}")
            return _response(200, {"access_token": f"A{number}", "refresh_token": f"R{number}"})


def _response(status: int, body: dict) -> Response:
    response = Response()
    response.status_code = status
    response.url = "http://core.test"
    response.headers["Content-Type"] = "application/json"
    response._content = json.dumps(body).encode()
    return response


def test_threads_rejected_together_refresh_the_credentials_once(monkeypatch, tmp_path) -> None:
    # Each thread refreshed with the same refresh token, which Core accepts
    # once: the others failed with invalid_grant or Unauthorized, and their
    # fallback switched the shared credentials to the (empty) environment.
    for variable in [*list_enum(ConfigurationVars), *list_enum(CredentialsVars)]:
        monkeypatch.delenv(variable, raising=False)
    ini = tmp_path / ".dhcore.ini"
    ini.write_text(
        "[DEFAULT]\ncurrent_environment = test\n\n[test]\n"
        "dhcore_endpoint = http://core.test\ndhcore_client_id = cli\n"
        "oauth2_token_endpoint = http://core.test/auth/token\n"
        "dhcore_access_token = A0\ndhcore_refresh_token = R0\n"
    )
    core = SingleUseRefreshCore()
    config = ClientConfig(config_ini_path=ini)
    identity = ClientConfigurator(core, config)
    client = Client(core, identity, config)
    results: list = []

    def read() -> None:
        try:
            results.append(client.execute(READ_PROJECT))
        except BackendError as error:
            results.append(error)

    threads = [threading.Thread(target=read) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(JOIN_TIMEOUT)

    assert results == [{"name": "demo"}, {"name": "demo"}]
    assert core.refreshes == ["R0"]
    assert identity._config_manager.credential_source is CredentialSource.FILE
