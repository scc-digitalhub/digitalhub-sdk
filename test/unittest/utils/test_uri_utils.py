import pytest

from digitalhub.utils.uri_utils import (
    SchemeCategory,
    get_filename_from_uri,
    map_uri_scheme,
    parse_sql_path,
)


@pytest.mark.parametrize(
    "uri",
    [
        "C:/users/data.csv",
        r"C:\users\data.csv",
        r"\\server\share\data.csv",
    ],
)
def test_map_uri_scheme_recognizes_windows_paths(uri: str) -> None:
    assert map_uri_scheme(uri) == SchemeCategory.LOCAL.value


@pytest.mark.parametrize(
    ("uri", "filename"),
    [
        ("C:/users/data.csv", "data.csv"),
        (r"C:\users\data.csv", "data.csv"),
        (r"\\server\share\data.csv", "data.csv"),
        ("https://example.com/data%20file.csv", "data file.csv"),
    ],
)
def test_get_filename_from_uri_normalizes_path_separators(uri: str, filename: str) -> None:
    assert get_filename_from_uri(uri) == filename


@pytest.mark.parametrize("scheme", ["sql", "postgresql"])
def test_parse_sql_path_accepts_registered_sql_schemes(scheme: str) -> None:
    assert parse_sql_path(f"{scheme}://database/schema/items") == {
        "database": "database",
        "schema": "schema",
        "table": "items",
    }


def test_parse_sql_path_defaults_to_the_public_schema() -> None:
    assert parse_sql_path("sql://database/items")["schema"] == "public"
