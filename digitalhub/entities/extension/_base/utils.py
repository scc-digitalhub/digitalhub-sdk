# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import typing

if typing.TYPE_CHECKING:
    from pydantic import BaseModel


def create_extension_schema(extension_name: str, kind: str, model: type[BaseModel]) -> str:
    """
    Create and dump an exension schema for a given extension name, kind, and Pydantic model.

    Parameters
    ----------
    extension_name : str
        The name of the extension.
    kind : str
        The kind of the extension.
    model : type[BaseModel]
        The Pydantic model class to convert.

    Returns
    -------
    str
        The extension schema as a JSON string.
    """
    extension_schema = {
        "name": extension_name,
        "kind": kind,
        "schema": model.model_json_schema(),
    }
    return json.dumps(extension_schema)
