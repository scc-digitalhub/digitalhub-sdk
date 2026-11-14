# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os

from digitalhub.utils.logger.enum import LoggerVars

_ROOT_LOGGER_NAME = LoggerVars.LOG_NAME.value
_DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_root_logger = logging.getLogger(_ROOT_LOGGER_NAME)
if not any(isinstance(handler, logging.NullHandler) for handler in _root_logger.handlers):
    _root_logger.addHandler(logging.NullHandler())


class _ConfiguredStreamHandler(logging.StreamHandler):
    pass


def _resolve_level(level: int | str) -> int:
    if isinstance(level, int):
        return level
    if not isinstance(level, str):
        raise TypeError("Logging level must be an integer or string.")
    resolved_level = getattr(logging, level.upper(), None)
    if isinstance(resolved_level, int):
        return resolved_level
    raise ValueError(f"Unknown logging level: {level!r}")


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure formatted console logging for the dhcore logger."""
    resolved_level = _resolve_level(level)
    handler = next(
        (handler for handler in _root_logger.handlers if isinstance(handler, _ConfiguredStreamHandler)),
        None,
    )
    if handler is None:
        handler = _ConfiguredStreamHandler()
        _root_logger.addHandler(handler)

    log_format = os.environ.get(LoggerVars.ENV_LOG_FORMAT.value, _DEFAULT_FORMAT)
    handler.setFormatter(logging.Formatter(log_format))
    handler.setLevel(resolved_level)
    _root_logger.setLevel(resolved_level)
    _root_logger.propagate = False


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a child logger under the digitalhub hierarchy.

    Parameters
    ----------
    name : str
        Typically __name__ of the calling module.  If *name* already
        starts with "digitalhub" it is used as-is; otherwise it is
        appended (digitalhub.<name>).  When *None*, the root
        "digitalhub" logger is returned.

    Returns
    -------
    logging.Logger
    """
    if name is None:
        return _root_logger
    if name == _ROOT_LOGGER_NAME or name.startswith(_ROOT_LOGGER_NAME + "."):
        return logging.getLogger(name)
    return _root_logger.getChild(name)


def set_level(level: int | str) -> None:
    """Change the log level for the entire digitalhub hierarchy.

    Parameters
    ----------
    level : int | str
        A standard logging level (e.g. logging.DEBUG or "DEBUG").
    """
    _root_logger.setLevel(_resolve_level(level))


_environment_level = os.environ.get(LoggerVars.ENV_LOG_LEVEL.value)
if _environment_level is not None:
    configure_logging(_environment_level)
