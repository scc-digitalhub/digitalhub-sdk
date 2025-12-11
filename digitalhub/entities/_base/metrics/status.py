# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class MetricsStatus:
    """
    MetricsStatus mixin for entities with metrics.
    """

    def __init__(self, metrics: dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.metrics = metrics if metrics is not None else {}
