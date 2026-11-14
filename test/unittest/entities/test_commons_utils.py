import inspect
from typing import get_type_hints

import pytest

from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.utils.exceptions import BackendError, EntityNotExistsError, ForbiddenError, UnauthorizedError


class Refreshable:
    def __init__(self, refresh_error: Exception | None = None) -> None:
        self.refresh_error = refresh_error
        self.call_count = 0

    def refresh(self) -> None:
        if self.refresh_error is not None:
            raise self.refresh_error

    @refresh_decorator
    def operation(self, value: int, *, double: bool = False) -> int:
        """Perform the decorated operation."""
        self.call_count += 1
        return value * 2 if double else value


def test_refresh_decorator_preserves_metadata_and_signature() -> None:
    operation = Refreshable.operation

    assert operation.__name__ == "operation"
    assert operation.__doc__ == "Perform the decorated operation."
    assert tuple(inspect.signature(operation).parameters) == ("self", "value", "double")
    assert get_type_hints(operation) == {"value": int, "double": bool, "return": int}


def test_refresh_decorator_continues_when_entity_is_missing() -> None:
    entity = Refreshable(EntityNotExistsError("not persisted yet"))

    assert entity.operation(3, double=True) == 6
    assert entity.call_count == 1


@pytest.mark.parametrize("error_type", [BackendError, UnauthorizedError, ForbiddenError])
def test_refresh_decorator_propagates_other_backend_errors(error_type: type[Exception]) -> None:
    entity = Refreshable(error_type("backend failure"))

    with pytest.raises(error_type, match="backend failure"):
        entity.operation(3)

    assert entity.call_count == 0
