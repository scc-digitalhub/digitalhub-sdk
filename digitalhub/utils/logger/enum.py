# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class LoggerVars(Enum):
    ENV_LOG_LEVEL = "DHCORE_LOG_LEVEL"
    ENV_LOG_FORMAT = "DHCORE_LOG_FORMAT"
    LOG_NAME = "dhcore"
