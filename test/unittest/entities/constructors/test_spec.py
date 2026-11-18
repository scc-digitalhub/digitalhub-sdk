# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities._constructors.spec import build_spec
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.material.spec import MaterialSpec
from digitalhub.entities.model._base.spec import ModelSpec


class ExampleSpec(Spec):
    command: str
    optional: str | None = None


def test_build_spec_validates_and_excludes_none_values() -> None:
    spec = build_spec(GenericSpec, command="run", optional=None)

    assert isinstance(spec, GenericSpec)
    assert spec.to_dict() == {"command": "run"}


def test_build_spec_validates_the_spec_model_and_rejects_unknown_fields() -> None:
    spec = build_spec(ExampleSpec, command="run", optional=None)

    assert spec.to_dict() == {"command": "run"}

    with pytest.raises(TypeError, match="Unexpected spec parameter.*unknown"):
        build_spec(ExampleSpec, command="run", unknown=True)


def test_from_dict_preserves_forward_compatible_fields() -> None:
    spec = ExampleSpec.from_dict({"command": "run", "future_field": "value"})

    assert spec.to_dict() == {"command": "run", "future_field": "value"}


def test_generic_spec_accepts_arbitrary_fields() -> None:
    spec = build_spec(GenericSpec, custom_field="preserved")

    assert spec.to_dict() == {"custom_field": "preserved"}


@pytest.mark.parametrize(
    "spec_cls",
    [MaterialSpec, ModelSpec],
)
def test_material_specs_validate_path(spec_cls) -> None:
    path = "s3://bucket/material"

    spec = build_spec(spec_cls, path=path)

    assert isinstance(spec, MaterialSpec)
    assert spec.to_dict() == {"path": path}
