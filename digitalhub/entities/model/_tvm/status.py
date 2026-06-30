# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.model._base.status import ModelStatus


class ModelStatusTvm(ModelStatus):
    """
    Shared status for TVM models (tvm-ir / tvm-so).
    """
