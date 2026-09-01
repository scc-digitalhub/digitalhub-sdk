import pytest
from pydantic import ValidationError

import digitalhub.entities._constructors.name as name_constructor


@pytest.mark.parametrize("name", ["pipeline", "pipeline-1", "pipeline.name_1+2"])
def test_build_name_accepts_valid_names(name: str) -> None:
    assert name_constructor.build_name(name) == name


@pytest.mark.parametrize("name", ["", "name with spaces", "a" * 257])
def test_build_name_rejects_invalid_names(name: str) -> None:
    with pytest.raises(ValidationError):
        name_constructor.build_name(name)


def test_random_name_combines_random_adjective_and_noun(monkeypatch) -> None:
    values = iter(["bright", "fox"])
    monkeypatch.setattr(name_constructor, "_random_enum_value", lambda enum_cls: next(values))

    assert name_constructor.random_name() == "bright-fox"
