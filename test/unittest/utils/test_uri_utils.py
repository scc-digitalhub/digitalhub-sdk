import pytest

from digitalhub.utils.uri_utils import (
    SchemeCategory,
    get_filename_from_uri,
    map_uri_scheme,
    parse_entity_reference,
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


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("python-function://project/model:version", ("model", "version")),
        ("task://project/task-id", (None, "task-id")),
        ("store://project/task/python-task/task-id", (None, "task-id")),
        ("task-id", (None, "task-id")),
    ],
)
def test_parse_entity_reference(reference: str, expected: tuple[str | None, str]) -> None:
    assert parse_entity_reference(reference) == expected


@pytest.mark.parametrize("reference", ["", "task://project/", "function://project/:id", "function://project/name:"])
def test_parse_entity_reference_rejects_empty_components(reference: str) -> None:
    with pytest.raises(ValueError, match="Invalid entity reference"):
        parse_entity_reference(reference)
