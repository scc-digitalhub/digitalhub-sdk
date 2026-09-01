from digitalhub.entities._mixin.generic.entity import GenericMixin
from digitalhub.entities._mixin.unversioned.mixin import UnversionedMixin
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin


def test_versioned_mixin_initializes_context_key() -> None:
    entity = VersionedMixin()
    entity.ENTITY_TYPE = "function"

    entity._init_versioned_identity("project", "pipeline", "function-id", "python")

    assert entity.name == "pipeline"
    assert entity.id == "function-id"
    assert entity.key == "store://project/function/python/pipeline:function-id"


def test_unversioned_mixin_uses_uuid_as_name_and_context_key() -> None:
    entity = UnversionedMixin()
    entity.ENTITY_TYPE = "task"

    entity._init_unversioned_identity("project", "task-id", "python+job")

    assert entity.name == "task-id"
    assert entity.id == "task-id"
    assert entity.key == "store://project/task/python+job/task-id"


def test_generic_mixin_preserves_existing_attributes() -> None:
    entity = GenericMixin()
    entity.existing = "original"

    entity._set_generic_attributes(existing="replacement", added="value")

    assert entity.existing == "original"
    assert entity.added == "value"
