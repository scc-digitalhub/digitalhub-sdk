# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
import typing
from collections.abc import Callable

from digitalhub.entities._commons.enums import State
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
    from digitalhub.entities.run._base.entity import Run

logger = get_logger(__name__)

TERMINAL_STATES = frozenset({State.STOPPED.value, State.ERROR.value, State.COMPLETED.value})


def finished(run: Run) -> str | None:
    """Outcome of a run in a terminal state; None while it is not."""
    return "finished" if run.status.state in TERMINAL_STATES else None


def wait_until(
    crud_processor: ContextEntityCRUDProcessor,
    run: Run,
    outcome: Callable[[Run], str | None],
    goal: str,
    log_info: bool = True,
    timeout: float | None = None,
    poll_interval: float = 5.0,
) -> Run:
    """
    Refresh a run until ``outcome`` tells what happened to it.

    Parameters
    ----------
    crud_processor : ContextEntityCRUDProcessor
        Processor that refreshes the run.
    run : Run
        Run to wait for.
    outcome : Callable[[Run], str | None]
        Returns what happened to the refreshed run, for the log, or None to
        keep waiting.
    goal : str
        What the run is waited for, for the log and the timeout error.
    log_info : bool
        If True, log information.
    timeout : float | None
        Maximum time to wait in seconds. If None, wait indefinitely.
    poll_interval : float
        Time to wait between status checks in seconds.

    Returns
    -------
    Run
        The refreshed run.

    Raises
    ------
    TimeoutError
        If ``outcome`` returns None until the timeout.
    """
    if timeout is not None and timeout < 0:
        raise ValueError("timeout must be non-negative.")
    if poll_interval <= 0:
        raise ValueError("poll_interval must be positive.")

    start = time.monotonic()
    while True:
        if log_info:
            logger.info(f"Waiting for run {run.id} to {goal}...")
        crud_processor.refresh_context_entity(run)
        elapsed = time.monotonic() - start
        result = outcome(run)
        if result is not None:
            if log_info:
                logger.info(f"Run {run.id} {result} in {elapsed:.2f} seconds.")
            return run
        if timeout is not None:
            remaining = timeout - elapsed
            if remaining <= 0:
                raise TimeoutError(f"Run {run.id} did not {goal} within {timeout}s")
            time.sleep(min(poll_interval, remaining))
        else:
            time.sleep(poll_interval)
