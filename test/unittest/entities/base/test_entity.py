# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._base.entity.entity import BaseEntity, PersistedEntity
from digitalhub.entities._base.metadata.entity import Metadata
from digitalhub.entities._mixin.extensions.mixin import ExtensionsMixin
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.entities.artifact._base.entity import Artifact
from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.entities.model._base.entity import Model
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.run._base.entity import Run
from digitalhub.factory.entity import entity_factory


class StubEntity(PersistedEntity):
    ENTITY_TYPE = "stub"

    def save(self, update: bool = False) -> PersistedEntity:
        return self

    def update(self) -> PersistedEntity:
        return self

    def refresh(self) -> PersistedEntity:
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
    material_attributes = (*context_attributes, *ExtensionsMixin._obj_attr)

    assert PersistedEntity._obj_attr == entity_attributes
    assert ContextEntity._obj_attr == context_attributes
    assert Project._obj_attr == (*entity_attributes, "id", "name", *ExtensionsMixin._obj_attr)

    for entity_class in (Artifact, Dataitem, Model, Run):
        assert entity_class._obj_attr == material_attributes


def test_base_entity_and_persisted_entity_have_separate_contracts() -> None:
    assert issubclass(ContextEntity, PersistedEntity)
    assert issubclass(Project, PersistedEntity)
    assert issubclass(Artifact, BaseEntity)


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


def _artifact_dict(**fields) -> dict:
    return {
        "project": "project",
        "kind": "artifact",
        "name": "artifact",
        "id": "artifact-id",
        "metadata": {"project": "project", "name": "artifact", "version": "artifact-id"},
        "spec": {"path": "s3://bucket/artifact"},
        "status": {"state": "READY"},
        **fields,
    }


def test_from_dict_keeps_unknown_top_level_fields() -> None:
    obj = _artifact_dict(extensions=[{"name": "extension"}], added_by_core={"enabled": True})

    artifact = entity_factory.build_entity_from_dict(obj)

    assert artifact.to_dict()["added_by_core"] == {"enabled": True}
    assert entity_factory.build_entity_from_dict(artifact.to_dict()).to_dict() == artifact.to_dict()


def test_update_attributes_takes_every_serialized_field() -> None:
    artifact = entity_factory.build_entity_from_dict(_artifact_dict(extensions=[{"name": "old"}]))
    backend = entity_factory.build_entity_from_dict(
        _artifact_dict(extensions=[{"name": "added-elsewhere"}], added_by_core=1)
    )

    artifact._update_attributes(backend)

    assert artifact.extensions == [{"name": "added-elsewhere"}]
    assert artifact.to_dict() == backend.to_dict()


def test_log_to_dict_keeps_its_own_fields() -> None:
    log = entity_factory.build_entity_from_dict(
        {
            "project": "project",
            "id": "log-id",
            "kind": "log",
            "run": "run-id",
            "metadata": {"project": "project", "name": "log-id", "version": "log-id"},
            "spec": {},
            "status": {},
            "extensions": [{"name": "extension"}],
        }
    )

    data = log.to_dict()

    assert {key: data[key] for key in ("project", "id", "run", "extensions")} == {
        "project": "project",
        "id": "log-id",
        "run": "run-id",
        "extensions": [{"name": "extension"}],
    }


def test_from_dict_reads_sections_as_they_are() -> None:
    run = entity_factory.build_entity_from_dict(
        {
            "project": "project",
            "id": "run-id",
            "kind": "python+job:run",
            "metadata": {"project": "project"},
            "spec": {"task": "python+job://project/task-id", "function": "python://project/function:id"},
            "status": {"state": "STATE_ADDED_BY_A_NEWER_CORE"},
        }
    )

    assert run.metadata.to_dict() == {"project": "project"}
    assert run.status.state == "STATE_ADDED_BY_A_NEWER_CORE"
