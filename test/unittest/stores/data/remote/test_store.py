from unittest.mock import MagicMock, Mock

import digitalhub.stores.data.remote.store as remote_store_module
from digitalhub.stores.data.remote.store import RemoteStore


def test_download_file_skips_head_and_streams_response(monkeypatch, tmp_path) -> None:
    store = object.__new__(RemoteStore)
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [b"first", b"", b"last"]
    get = Mock(return_value=response)
    head = Mock()
    monkeypatch.setattr(remote_store_module.requests, "get", get)
    monkeypatch.setattr(remote_store_module.requests, "head", head)
    destination = tmp_path / "download.bin"

    assert store._download_file("https://example.com/download.bin", destination, overwrite=False) == str(destination)

    assert destination.read_bytes() == b"firstlast"
    get.assert_called_once_with(
        "https://example.com/download.bin",
        stream=True,
        timeout=60,
        allow_redirects=True,
    )
    head.assert_not_called()
