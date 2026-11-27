# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Protocol, cast

from digitalhub.entities._mixin.executable.enums import ExecutableActions

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class _RunnableExecutable(Protocol):
    def run(
        self,
        action: str,
        wait: bool = False,
        log_info: bool = True,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run: ...


class ExecutableBuildMixin:
    """Add ``build()`` to executables whose runtime implements the build action."""

    def build(
        self,
        wait: bool = True,
        log_info: bool = True,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """
        Execute the build action.

        Parameters
        ----------
        wait : bool
            Flag to wait for the build to finish.
        log_info : bool
            Flag to log information while waiting.
        extensions : list[dict] | None
            List of extensions to apply.
        **kwargs : dict
            Keyword arguments passed to Run construction.

        Returns
        -------
        Run
            Build run.
        """
        return cast(_RunnableExecutable, self).run(
            ExecutableActions.BUILD.value,
            wait=wait,
            log_info=log_info,
            extensions=extensions,
            **kwargs,
        )
