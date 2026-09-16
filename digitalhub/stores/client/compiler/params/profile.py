# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class ParamsProfile(Enum):
    """Semantic parameter transformations supported by the client."""

    READ = "read"
    READ_ALL_VERSIONS = "read_all_versions"
    LIST = "list"
    DELETE = "delete"
    DELETE_ALL_VERSIONS = "delete_all_versions"
    SEARCH = "search"
    SHARE = "share"
    LOGS = "logs"
    METRICS = "metrics"
    STOP_RESUME = "stop_resume"
