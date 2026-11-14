from io import StringIO

import pytest

from digitalhub.utils.exceptions import ReaderError


def test_read_df_wraps_unsupported_extension() -> None:
    pytest.importorskip("pandas")
    from digitalhub.stores.readers.data.pandas.reader import DataframeReaderPandas

    with pytest.raises(ReaderError, match=r"Unsupported extension 'unknown' for reading\.") as error:
        DataframeReaderPandas().read_df("data.unknown", "unknown")

    assert isinstance(error.value.__cause__, ValueError)


def test_read_df_preserves_pandas_value_error() -> None:
    pytest.importorskip("pandas")
    from digitalhub.stores.readers.data.pandas.reader import DataframeReaderPandas

    with pytest.raises(ReaderError, match=r"Unable to read 'csv' data:.*Usecols do not match") as error:
        DataframeReaderPandas().read_df(StringIO("a,b\n1,2\n"), "csv", usecols=["missing"])

    assert isinstance(error.value.__cause__, ValueError)
    assert "Usecols do not match" in str(error.value)
