# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class LoggerVars(Enum):
    ENV_LOG_LEVEL = "DIGITALHUB_LOG_LEVEL"
    ENV_LOG_FORMAT = "DIGITALHUB_LOG_FORMAT"
    LOG_NAME = "digitalhub"
