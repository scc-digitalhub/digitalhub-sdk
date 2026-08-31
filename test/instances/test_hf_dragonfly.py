import importlib
import os

import pytest

import digitalhub.stores.data.hf.dragonfly as dragonfly_module


@pytest.mark.parametrize(("node_ip", "enabled"), [(None, False), ("192.0.2.1", True)])
def test_dragonfly_requires_node_ip(monkeypatch, node_ip, enabled) -> None:
    original_node_ip = os.environ.get("NODE_IP")
    if node_ip is None:
        monkeypatch.delenv("NODE_IP", raising=False)
    else:
        monkeypatch.setenv("NODE_IP", node_ip)

    try:
        module = importlib.reload(dragonfly_module)
        assert module.dragonfly is enabled
    finally:
        if original_node_ip is None:
            monkeypatch.delenv("NODE_IP", raising=False)
        else:
            monkeypatch.setenv("NODE_IP", original_node_ip)
        importlib.reload(dragonfly_module)
