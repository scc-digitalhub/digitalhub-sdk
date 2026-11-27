# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.runtimes._base import Runtime


def test_execute_returns_the_function_result() -> None:
    assert Runtime._execute(lambda a, b=0: a + b, 1, b=2) == 3


def test_execute_names_the_error_of_the_function() -> None:
    # The message is stored in the run status: it used to be only
    # "Something got wrong during function execution."
    def handler() -> None:
        raise ValueError("column 'age' is missing")

    with pytest.raises(RuntimeError, match="ValueError: column 'age' is missing") as error:
        Runtime._execute(handler)

    assert isinstance(error.value.__cause__, ValueError)
