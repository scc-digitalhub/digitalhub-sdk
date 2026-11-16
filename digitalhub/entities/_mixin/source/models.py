# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.generic_utils import encode_string


class SourceCode(BaseModel):
    """Base source code model for executables."""

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    DEFAULT_LANG: ClassVar[str | None] = None
    REQUIRE_SOURCE: ClassVar[bool] = True

    source: str | None = None
    code: str | None = Field(default=None, exclude=True)
    base64: str | None = None
    lang: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_source_inputs(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        if "code_src" in normalized and normalized.get("source") is None:
            normalized["source"] = normalized.pop("code_src")
        else:
            normalized.pop("code_src", None)

        if normalized.get("lang") is None and cls.DEFAULT_LANG is not None:
            normalized["lang"] = cls.DEFAULT_LANG

        code = normalized.get("code")
        if isinstance(code, str):
            normalized["base64"] = encode_string(normalized.pop("code"))

        return normalized

    @model_validator(mode="after")
    def _validate_source_presence(self) -> Self:
        if self.REQUIRE_SOURCE and self.source is None and self.base64 is None:
            raise EntityError("Source must be provided.")
        return self


class HandlerSourceCode(SourceCode):
    """Source code model with an entrypoint handler."""

    REQUIRE_HANDLER: ClassVar[bool] = False

    handler: str | None = None

    @model_validator(mode="after")
    def _validate_handler_presence(self) -> Self:
        if self.REQUIRE_HANDLER and not self.handler:
            raise EntityError("Handler must be provided.")
        return self
