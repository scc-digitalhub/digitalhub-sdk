# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os

from digitalhub.utils.logger.enum import LoggerVars


_ROOT_LOGGER_NAME = LoggerVars.LOG_NAME.value

_DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DEFAULT_LEVEL = logging.getLevelName(logging.INFO)

# Resolve configuration from environment
_level_name = os.environ.get(LoggerVars.ENV_LOG_LEVEL.value, _DEFAULT_LEVEL).upper()
_log_format = os.environ.get(LoggerVars.ENV_LOG_FORMAT.value, _DEFAULT_FORMAT)

_level = getattr(logging, _level_name, None)
if not isinstance(_level, int):
    _level = logging.INFO

# Set up the root "digitalhub" logger exactly once.
_root_logger = logging.getLogger(_ROOT_LOGGER_NAME)
_root_logger.setLevel(_level)

if not _root_logger.handlers:
    _formatter = logging.Formatter(_log_format)
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(_formatter)
    _root_logger.addHandler(_console_handler)

# Prevent log messages from propagating to the root Python logger when
# a handler is already attached (avoids duplicate messages).
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
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    _root_logger.setLevel(level)
