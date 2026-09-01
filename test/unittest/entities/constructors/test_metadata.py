import pytest

import digitalhub.entities._constructors.metadata as metadata_constructor
from digitalhub.utils.exceptions import BuilderError


def test_build_metadata_adds_defaults(monkeypatch) -> None:
    monkeypatch.setattr(metadata_constructor, "get_timestamp", lambda: "timestamp")
    monkeypatch.setattr(metadata_constructor, "random_name", lambda: "generated-name")

    metadata = metadata_constructor.build_metadata(project="my-project")

    assert metadata.to_dict() == {
        "project": "my-project",
        "name": "generated-name",
        "version": "generated-name",
        "created": "timestamp",
        "updated": "timestamp",
    }


def test_build_metadata_uses_created_as_default_updated() -> None:
    metadata = metadata_constructor.build_metadata(
        name="pipeline",
        version="1",
        created="created-time",
    )

    assert metadata.created == "created-time"
    assert metadata.updated == "created-time"
    assert metadata.name == "pipeline"
    assert metadata.version == "1"


def test_build_metadata_rejects_non_list_relationships() -> None:
    with pytest.raises(BuilderError, match="Invalid relationships format"):
        metadata_constructor.build_metadata(relationships={"type": "part_of"})


def test_build_metadata_rejects_malformed_relationships() -> None:
    with pytest.raises(BuilderError, match="Malformed relationship"):
        metadata_constructor.build_metadata(relationships=[{"source": 123}])


def test_build_metadata_accepts_valid_relationships() -> None:
    metadata = metadata_constructor.build_metadata(
        relationships=[{"type": "part_of", "source": "source-key", "dest": "dest-key"}]
    )

    assert metadata.relationships == [{"type": "part_of", "source": "source-key", "dest": "dest-key"}]
