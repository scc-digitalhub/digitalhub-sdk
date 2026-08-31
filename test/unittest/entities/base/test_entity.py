from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._base.entity.entity import Entity
from digitalhub.entities.artifact._base.entity import Artifact
from digitalhub.entities.artifact.generic.entity import ArtifactGeneric
from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.entities.model._base.entity import Model
from digitalhub.entities.model.generic.entity import ModelGeneric
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.run._base.entity import Run
from digitalhub.entities.run.generic.entity import RunGeneric


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
