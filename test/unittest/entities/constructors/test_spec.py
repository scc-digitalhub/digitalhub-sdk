from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._constructors.spec import build_spec
from digitalhub.entities._mixin.generic.spec import GenericSpec


class ExampleSpecValidator(SpecValidator):
    command: str
    optional: str | None = None


def test_build_spec_validates_and_excludes_none_values() -> None:
    spec = build_spec(
        GenericSpec,
        ExampleSpecValidator,
        command="run",
        optional=None,
    )

    assert isinstance(spec, GenericSpec)
    assert spec.to_dict() == {"command": "run"}
