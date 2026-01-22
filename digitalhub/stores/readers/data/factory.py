# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.stores.readers.data._base.builder import ReaderBuilder
    from digitalhub.stores.readers.data._base.reader import DataframeReader
    from digitalhub.utils.types import Dataframe


class ReaderFactory:
    """
    Reader factory class.
    """

    def __init__(self) -> None:
        self._builders: dict[str, ReaderBuilder] = None
        self._default: str = None

    def add_builder(
        self,
        engine: str,
        builder: ReaderBuilder,
    ) -> None:
        """
        Add a builder to the factory.

        Parameters
        ----------
        engine : str
            Engine name.
        builder : ReaderBuilder
            Builder instance.
        """
        if self._builders is None:
            self._builders = {}
        if engine in self._builders:
            raise BuilderError(f"Builder for engine '{engine}' already exists.")
        self._builders[engine] = builder

    def build(
        self,
        engine: str | None = None,
        dataframe: Dataframe | None = None,  # type: ignore
        **kwargs,
    ) -> DataframeReader:
        """
        Build reader object.

        Parameters
        ----------
        engine : str
            Engine name.
        dataframe : Dataframe
            Dataframe type.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        DataframeReader
            Reader object.
        """
        if (engine is None) == (dataframe is None):
            raise BuilderError("Either engine or dataframe must be provided.")
        if engine is not None:
            return self._builders[engine].build(**kwargs)
        for builder in self._builders.values():
            if isinstance(dataframe, builder.DATAFRAME_CLASS):
                return builder.build(**kwargs)
        raise KeyError(f"No builder found for dataframe type '{dataframe}'.")

    def list_supported_engines(self) -> list[str]:
        """
        List supported engines.

        Returns
        -------
        list[str]
            List of supported engines.
        """
        return list(self._builders.keys())

    def list_supported_dataframes(self) -> list[Dataframe]:  # type: ignore
        """
        List supported dataframes.

        Returns
        -------
        list[Dataframe]
            List of supported dataframes.
        """
        return [i.DATAFRAME_CLASS for i in self._builders.values()]

    def set_default(self, engine: str) -> None:
        """
        Set default engine.

        Parameters
        ----------
        engine : str
            Engine name.
        """
        if engine not in self._builders:
            raise BuilderError(f"Engine {engine} not found.")
        self._default = engine

    def get_default(self) -> str:
        """
        Get default engine.

        Returns
        -------
        str
            Default engine.
        """
        if self._default is None:
            raise BuilderError("No default engine set.")
        return self._default


factory = ReaderFactory()

try:
    from digitalhub.stores.readers.data.pandas.builder import ReaderBuilderPandas

    factory.add_builder(
        ReaderBuilderPandas.ENGINE,
        ReaderBuilderPandas(),
    )
    factory.set_default(ReaderBuilderPandas.ENGINE)

except ImportError:
    pass

try:
    from digitalhub.stores.readers.data.polars.builder import ReaderBuilderPolars

    factory.add_builder(
        ReaderBuilderPolars.ENGINE,
        ReaderBuilderPolars(),
    )

except ImportError:
    pass
