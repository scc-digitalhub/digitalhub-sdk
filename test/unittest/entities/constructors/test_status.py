import pytest

from digitalhub.entities._constructors.status import build_status
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.utils.exceptions import BuilderError


def test_build_status_defaults_to_created() -> None:
    status = build_status(GenericStatus)

    assert status.to_dict() == {"state": "CREATED"}


def test_build_status_preserves_valid_state_and_extra_fields() -> None:
    status = build_status(GenericStatus, state="READY", message="available")

    assert status.to_dict() == {"state": "READY", "message": "available"}


def test_build_status_rejects_unknown_state() -> None:
    with pytest.raises(BuilderError, match="Invalid state: ready"):
        build_status(GenericStatus, state="ready")
