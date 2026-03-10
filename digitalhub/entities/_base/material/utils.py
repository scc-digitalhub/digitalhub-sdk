# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.logger.logger import get_logger

logger = get_logger(__name__)


def refresh_decorator(fn: typing.Callable) -> typing.Callable:
    """
    Refresh decorator.

    Parameters
    ----------
    fn : Callable
        Function to decorate.

    Returns
    -------
    Callable
        Decorated function.
    """

    def wrapper(self, *args, **kwargs):
        # Prevent rising error if entity is not yet created in backend
        try:
            self.refresh()
        except BackendError:
            logger.debug(
                f"Refresh skipped for {getattr(self, 'id', 'unknown')} (entity may not exist in backend yet).",
                exc_info=True,
            )
        return fn(self, *args, **kwargs)

    return wrapper
