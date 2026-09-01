from types import SimpleNamespace

import pytest

import digitalhub.entities._constructors.uuid as uuid_constructor


def test_build_uuid_returns_provided_slugified_uuid() -> None:
    assert uuid_constructor.build_uuid("run-id") == "run-id"


def test_build_uuid_rejects_non_slugified_uuid() -> None:
    with pytest.raises(ValueError, match="Invalid ID: Run ID"):
        uuid_constructor.build_uuid("Run ID")


def test_build_uuid_generates_uuid_when_not_provided(monkeypatch) -> None:
    monkeypatch.setattr(uuid_constructor, "uuid4", lambda: SimpleNamespace(hex="generated-uuid"))

    assert uuid_constructor.build_uuid() == "generated-uuid"
