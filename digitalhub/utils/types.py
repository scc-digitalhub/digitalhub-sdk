# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Union

from digitalhub.stores.readers.data.types import _dataframe_types

SourcesOrListOfSources = str | list[str]

Dataframe = Union[_dataframe_types]
