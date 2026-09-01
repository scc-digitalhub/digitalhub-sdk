import json

from digitalhub.entities._base._base.entity import Base


class NestedBase(Base):
    def __init__(self, value=None) -> None:
        self.value = value


def test_to_dict_excludes_private_and_none_values_and_serializes_nested_objects() -> None:
    entity = Base()
    entity.visible = "value"
    entity.empty = None
    entity._private = "hidden"
    entity.nested = NestedBase("nested-value")
    entity.empty_nested = NestedBase()

    assert entity.to_dict() == {
        "visible": "value",
        "nested": {"value": "nested-value"},
    }


def test_to_json_serializes_to_dict() -> None:
    entity = Base()
    entity.value = "text"

    assert json.loads(entity.to_json()) == {"value": "text"}


def test_any_setter_does_not_overwrite_existing_attributes() -> None:
    entity = Base()
    entity.existing = "original"

    entity._any_setter(existing="replacement", added="value")

    assert entity.existing == "original"
    assert entity.added == "value"


def test_repr_returns_dictionary_representation() -> None:
    entity = Base()
    entity.value = "text"

    assert repr(entity) == "{'value': 'text'}"
