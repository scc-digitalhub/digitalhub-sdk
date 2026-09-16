# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.stores.client.common.enums import OpsType
from digitalhub.stores.client.http.request import BERequest


def test_method_factories_preserve_request_fields() -> None:
    requests = [
        BERequest.get(
            "/resource",
            operation=OpsType.ENTITY_READ,
            params={"page": 1},
            verify=False,
        ),
        BERequest.post(
            "/resource",
            operation=OpsType.ENTITY_CREATE,
            data={"name": "demo"},
        ),
        BERequest.put(
            "/resource",
            operation=OpsType.ENTITY_UPDATE,
            headers={"X-Request-ID": "request-id"},
        ),
        BERequest.delete(
            "/resource",
            operation=OpsType.ENTITY_DELETE,
        ),
    ]

    assert [request.method for request in requests] == ["GET", "POST", "PUT", "DELETE"]
    assert requests[0].operation == OpsType.ENTITY_READ.value
    assert requests[0].params == {"page": 1}
    assert requests[0].options == {"verify": False}
    assert requests[1].data == {"name": "demo"}
    assert requests[2].headers == {"X-Request-ID": "request-id"}
