from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import digitalhub.stores.data.remote.store as remote_store_module
import digitalhub.stores.session as session_module
from digitalhub.stores.client.common.config import ClientConfig
from digitalhub.stores.data.remote.store import RemoteStore
from digitalhub.stores.session import Session


def test_download_file_skips_head_and_streams_response(monkeypatch, tmp_path) -> None:
    store = object.__new__(RemoteStore)
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [b"first", b"", b"last"]
    get = Mock(return_value=response)
    head = Mock()
    monkeypatch.setattr(remote_store_module.requests, "get", get)
    monkeypatch.setattr(remote_store_module.requests, "head", head)
    monkeypatch.setattr(
        remote_store_module,
        "get_client_config",
        lambda: SimpleNamespace(http_timeout=35),
    )
    destination = tmp_path / "download.bin"

    assert store._download_file("https://example.com/download.bin", destination, overwrite=False) == str(destination)

    assert destination.read_bytes() == b"firstlast"
    get.assert_called_once_with(
        "https://example.com/download.bin",
        stream=True,
        timeout=35,
        allow_redirects=True,
    )
    head.assert_not_called()


def test_download_file_uses_the_timeout_of_the_session(monkeypatch, tmp_path) -> None:
    # The store read the global configuration, not the one of the session.
    session = Session(ClientConfig(http_timeout=7), transport=Mock(), identity=Mock())
    monkeypatch.setattr(session_module, "_session", session)
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [b"data"]
    get = Mock(return_value=response)
    monkeypatch.setattr(remote_store_module.requests, "get", get)

    object.__new__(RemoteStore)._download_file("https://example.com/file", tmp_path / "file", overwrite=False)

    assert get.call_args.kwargs["timeout"] == 7
