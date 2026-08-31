# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from requests import request as requests_request
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException
from requests.exceptions import Timeout as RequestsTimeout

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.utils.exceptions import BackendError

if typing.TYPE_CHECKING:
    from requests import Response


def request(method: str, url: str, **kwargs) -> Response:
    """Execute an HTTP request and normalize transport errors."""
    try:
        return requests_request(method, url, timeout=get_client_config().http_timeout, **kwargs)
    except RequestsTimeout as e:
        raise TimeoutError("Request to DHCore backend timed out.") from e
    except RequestsConnectionError as e:
        raise ConnectionError("Unable to connect to DHCore backend.") from e
    except RequestException as e:
        raise BackendError(f"Some error occurred. {e}") from e
