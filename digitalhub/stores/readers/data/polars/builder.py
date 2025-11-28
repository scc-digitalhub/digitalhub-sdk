# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.readers.data._base.builder import ReaderBuilder
from digitalhub.stores.readers.data.polars.reader import DataframeReaderPolars


class ReaderBuilderPolars(ReaderBuilder):
    """
    Polars reader builder.
    """

    ENGINE = "polars"
    DATAFRAME_CLASS = "polars.dataframe.frame.DataFrame"

    def build(self, **kwargs) -> DataframeReaderPolars:
        """
        Build reader object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        DataframeReaderPolars
            Polars reader object.
        """
        return DataframeReaderPolars(**kwargs)
