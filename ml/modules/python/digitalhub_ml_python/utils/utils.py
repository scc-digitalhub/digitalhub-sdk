from __future__ import annotations

import functools
from typing import Callable

from digitalhub_ml_python.utils.outputs import collect_outputs


def handler(outputs: list[str] | None = None) -> Callable:
    """
    Decorator that handles the outputs of the function.

    Parameters
    ----------
    outputs : list[str]
        List of named outputs to collect.

    Returns
    -------
    Callable
        Decorated function.
    """

    def decorator(func: Callable) -> Callable:
        """
        Decorator that handles the outputs of the function.

        Parameters
        ----------
        func : Callable
            Function to decorate.

        Returns
        -------
        Callable
            Decorated function.
        """

        def wrapper(*args, **kwargs) -> dict:
            """
            Wrapper that handles the outputs of the function.

            Parameters
            ----------
            args : tuple
                Function arguments.
            kwargs : dict
                Function keyword arguments.

            Returns
            -------
            Any
                Function outputs.
            """

            # Initialize outputs
            nonlocal outputs

            # We pass the first argument as the project name
            project_name = args[0]
            args = args[1:]

            # Execute the function
            results = func(*args, **kwargs)

            # Parse outputs based on the decorator signature
            return collect_outputs(results, outputs, project_name)

        wrapper = functools.wraps(func)(wrapper)

        return wrapper

    return decorator
