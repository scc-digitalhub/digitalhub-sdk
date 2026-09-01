import pytest

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._base.entity.entity import Entity
from digitalhub.entities._base.metadata.entity import Metadata
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.entities.artifact._base.entity import Artifact
from digitalhub.entities.artifact.generic.entity import ArtifactGeneric
from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.entities.model._base.entity import Model
from digitalhub.entities.model.generic.entity import ModelGeneric
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.run._base.entity import Run
from digitalhub.entities.run.generic.entity import RunGeneric


class StubEntity(Entity):
    ENTITY_TYPE = "stub"

    def save(self, update: bool = False) -> Entity:
        return self

    def refresh(self) -> Entity:
        return self

    def export(self) -> str:
        return "stub.yaml"


def _build_entity(name: str = "entity") -> StubEntity:
    entity = StubEntity(
        kind="stub-kind",
        metadata=Metadata(name=name, version="1"),
        spec=GenericSpec(value="spec"),
        status=GenericStatus(state="READY"),
        user="user",
    )
    entity.key = "store://project/stub/stub-kind/entity:entity-id"
    return entity


def test_serialization_attributes_are_immutable_class_contracts() -> None:
    entity_attributes = ("kind", "metadata", "spec", "status", "user", "key")
    context_attributes = (*entity_attributes, "project", "id", "name")
    material_attributes = (*context_attributes, "extensions")

    assert Entity._obj_attr == entity_attributes
    assert ContextEntity._obj_attr == context_attributes
    assert Project._obj_attr == (*entity_attributes, "id", "name")

    for entity_class in (Artifact, ArtifactGeneric, Dataitem, Model, ModelGeneric):
        assert entity_class._obj_attr == material_attributes

    for entity_class in (Run, RunGeneric):
        assert entity_class._obj_attr == material_attributes


def test_entity_mutators_update_metadata_without_duplicates() -> None:
    entity = _build_entity()

    entity.set_name("renamed")
    entity.set_version("2")
    entity.set_description("description")
    entity.add_relationship("part_of", "project-key")
    entity.add_relationship("consumes", "source-key", source="entity-key")
    entity.add_labels(["production", "stable"])
    entity.add_label("production")

    assert entity.metadata.to_dict() == {
        "name": "renamed",
        "version": "2",
        "description": "description",
        "relationships": [
            {"type": "part_of", "dest": "project-key"},
            {"type": "consumes", "dest": "source-key", "source": "entity-key"},
        ],
        "labels": ["production", "stable"],
    }


@pytest.mark.parametrize(
    ("method_name", "value", "message"),
    [
        ("set_name", 123, "Name must be a string"),
        ("set_version", 123, "Version must be a string"),
        ("set_description", 123, "Description must be a string"),
        ("add_label", 123, "Label must be a string"),
    ],
)
def test_entity_mutators_reject_non_string_values(method_name: str, value, message: str) -> None:
    with pytest.raises(TypeError, match=message):
        getattr(_build_entity(), method_name)(value)


def test_entity_updates_attributes_and_filters_extra_serialized_fields() -> None:
    entity = _build_entity()
    updated = _build_entity("updated")
    entity.extra = "not serialized"

    entity._update_attributes(updated)

    assert entity.metadata is updated.metadata
    assert entity.spec is updated.spec
    assert entity.status is updated.status
    assert entity.user == updated.user
    assert "extra" not in entity.to_dict()
