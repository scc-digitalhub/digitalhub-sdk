# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.utils.exceptions import BackendError


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
            pass
        return fn(self, *args, **kwargs)

    return wrapper
