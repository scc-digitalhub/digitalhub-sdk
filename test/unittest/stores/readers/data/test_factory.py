from unittest.mock import Mock

import pytest

import digitalhub.stores.readers.data.api as reader_api
from digitalhub.stores.readers.data.factory import ReaderFactory
from digitalhub.utils.exceptions import ReaderError


def test_first_available_reader_becomes_default() -> None:
    factory = ReaderFactory()
    factory.add_builder("polars", Mock())

    assert factory.get_default() == "polars"

    factory.add_builder("pandas", Mock())
    assert factory.get_default() == "polars"

    factory.set_default("pandas")
    assert factory.get_default() == "pandas"


def test_missing_optional_readers_raise_reader_error(monkeypatch) -> None:
    factory = ReaderFactory()
    monkeypatch.setattr(reader_api, "factory", factory)

    with pytest.raises(ReaderError, match="No dataframe readers are installed"):
        reader_api.get_reader_by_engine()

    with pytest.raises(ReaderError, match="No dataframe readers are installed"):
        factory.build(engine="pandas")
