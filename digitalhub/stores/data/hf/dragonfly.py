# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os

import requests
from requests.adapters import HTTPAdapter

dragonfly = False
NODE_IP = os.environ.get("NODE_IP")
if NODE_IP is None:
    dragonfly = True


class DragonflyAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        # Change the schema of the LFS request to download large files from https:// to http://,
        # so that Dragonfly HTTP proxy can be used.
        if url.startswith("https://cdn-lfs.huggingface.co"):
            url = url.replace("https://", "http://")
        return super().get_connection(url, proxies)

    def add_headers(self, request, **kwargs):
        super().add_headers(request, **kwargs)

        # If there are multiple different LFS repositories, you can override the
        # default repository address by adding X-Dragonfly-Registry header.
        if request.url.find("example.com") != -1:
            request.headers["X-Dragonfly-Registry"] = "https://example.com"


# Create a factory function that returns a new Session.
def backend_factory() -> requests.Session:
    session = requests.Session()
    session.mount("http://", DragonflyAdapter())
    session.mount("https://", DragonflyAdapter())
    session.proxies = {"http": "http://127.0.0.1:4001"}
    return session
