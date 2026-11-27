# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities.project.crud as project_crud
from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.project._base.processor import ProjectProcessor
from digitalhub.utils.exceptions import BackendError, EntityNotExistsError, UnauthorizedError


def test_new_project_passes_extensions_to_processor(monkeypatch) -> None:
    create_project = Mock(return_value="project")
    setup_project = Mock(return_value="configured-project")
    monkeypatch.setattr(ProjectProcessor, "create_project_entity_from_params", create_project)
    monkeypatch.setattr(project_crud, "setup_project", setup_project)
    extensions = [{"key": "value"}]

    result = project_crud.new_project("my-project", extensions=extensions)

    assert result == "configured-project"
    create_project.assert_called_once_with(
        name="my-project",
        kind=EntityKinds.PROJECT_PROJECT.value,
        description=None,
        labels=None,
        config=None,
        source="./",
        extensions=extensions,
    )
    setup_project.assert_called_once_with("project", None)


def test_get_project_reads_and_configures_project(monkeypatch) -> None:
    read_project = Mock(return_value="project")
    setup_project = Mock(return_value="configured-project")
    monkeypatch.setattr(ProjectProcessor, "read_project_entity", read_project)
    monkeypatch.setattr(project_crud, "setup_project", setup_project)

    result = project_crud.get_project("my-project", setup_kwargs={"context": "./context"})

    assert result == "configured-project"
    read_project.assert_called_once_with(
        entity_type=project_crud.ENTITY_TYPE,
        entity_name="my-project",
    )
    setup_project.assert_called_once_with("project", {"context": "./context"})


def test_import_project_passes_reset_id_and_setup_kwargs(monkeypatch) -> None:
    import_project = Mock(return_value="project")
    setup_project = Mock(return_value="configured-project")
    monkeypatch.setattr(ProjectProcessor, "import_project_entity", import_project)
    monkeypatch.setattr(project_crud, "setup_project", setup_project)

    result = project_crud.import_project(
        "my-project.yaml",
        setup_kwargs={"context": "./context"},
        reset_id=True,
    )

    assert result == "configured-project"
    import_project.assert_called_once_with(file="my-project.yaml", reset_id=True)
    setup_project.assert_called_once_with("project", {"context": "./context"})


def test_load_project_passes_file_to_processor(monkeypatch) -> None:
    load_project = Mock(return_value="project")
    setup_project = Mock(return_value="configured-project")
    monkeypatch.setattr(ProjectProcessor, "load_project_entity", load_project)
    monkeypatch.setattr(project_crud, "setup_project", setup_project)

    result = project_crud.load_project("my-project.yaml")

    assert result == "configured-project"
    load_project.assert_called_once_with(file="my-project.yaml")
    setup_project.assert_called_once_with("project", None)


def test_list_projects_returns_processor_result(monkeypatch) -> None:
    projects = ["project"]
    list_projects = Mock(return_value=projects)
    monkeypatch.setattr(ProjectProcessor, "list_project_entities", list_projects)

    result = project_crud.list_projects()

    assert result is projects
    list_projects.assert_called_once_with(project_crud.ENTITY_TYPE)


def _get_or_create(monkeypatch, read: Mock, setup: Mock | None = None) -> tuple[object, Mock]:
    new_project = Mock(return_value="created-project")
    monkeypatch.setattr(ProjectProcessor, "read_project_entity", read)
    monkeypatch.setattr(project_crud, "setup_project", setup or Mock(side_effect=lambda obj, kwargs: obj))
    monkeypatch.setattr(project_crud, "new_project", new_project)
    result = project_crud.get_or_create_project(
        "my-project",
        description="A project",
        labels=["production"],
        config={"host": "localhost"},
        context="./context",
        setup_kwargs={"option": True},
        extensions=[{"key": "value"}],
    )
    return result, new_project


def test_get_or_create_project_returns_existing_project(monkeypatch) -> None:
    setup = Mock(return_value="set-up-project")

    result, new_project = _get_or_create(monkeypatch, Mock(return_value="existing-project"), setup)

    assert result == "set-up-project"
    setup.assert_called_once_with("existing-project", {"option": True})
    new_project.assert_not_called()


def test_get_or_create_project_creates_when_project_is_missing(monkeypatch) -> None:
    result, new_project = _get_or_create(monkeypatch, Mock(side_effect=EntityNotExistsError("No such project.")))

    assert result == "created-project"
    new_project.assert_called_once_with(
        "my-project",
        description="A project",
        labels=["production"],
        config={"host": "localhost"},
        setup_kwargs={"option": True},
        source="./context",
        extensions=[{"key": "value"}],
    )


@pytest.mark.parametrize(
    ("read", "setup"),
    [
        (Mock(side_effect=UnauthorizedError("Unauthorized")), None),
        (Mock(side_effect=BackendError("Backend error")), None),
        # An error of the setup hook is not a missing project.
        (Mock(return_value="existing-project"), Mock(side_effect=EntityNotExistsError("hook"))),
    ],
)
def test_get_or_create_project_does_not_create_on_other_errors(monkeypatch, read: Mock, setup: Mock | None) -> None:
    # Every BackendError used to lead to a creation attempt, which hid the cause.
    new_project = Mock()
    monkeypatch.setattr(ProjectProcessor, "read_project_entity", read)
    monkeypatch.setattr(project_crud, "setup_project", setup or Mock())
    monkeypatch.setattr(project_crud, "new_project", new_project)

    with pytest.raises(BackendError):
        project_crud.get_or_create_project("my-project")
    new_project.assert_not_called()


def test_update_project_passes_entity_payload(monkeypatch) -> None:
    entity = SimpleNamespace(
        ENTITY_TYPE=project_crud.ENTITY_TYPE,
        name="my-project",
        to_dict=Mock(return_value={"metadata": {"name": "my-project"}}),
    )
    update_project = Mock(return_value="updated-project")
    monkeypatch.setattr(ProjectProcessor, "update_project_entity", update_project)

    result = project_crud.update_project(entity)

    assert result == "updated-project"
    update_project.assert_called_once_with(entity)


def test_delete_project_passes_cascade_and_context_options(monkeypatch) -> None:
    delete_project = Mock(return_value={"deleted": True})
    monkeypatch.setattr(ProjectProcessor, "delete_project_entity", delete_project)

    result = project_crud.delete_project("my-project", cascade=False, clean_context=False)

    assert result == {"deleted": True}
    delete_project.assert_called_once_with(
        entity_type=project_crud.ENTITY_TYPE,
        entity_name="my-project",
        cascade=False,
        clean_context=False,
    )


def test_search_entity_forwards_filters(monkeypatch) -> None:
    search = Mock(return_value=([], []))
    monkeypatch.setattr(ProjectProcessor, "search_entity", search)

    result = project_crud.search_entity(
        "my-project",
        query="query",
        entity_types=["artifacts"],
        name="artifact",
        kind="artifact",
        created="created",
        updated="updated",
        description="description",
        labels=["production"],
    )

    assert result == ([], [])
    search.assert_called_once_with(
        "my-project",
        query="query",
        entity_types=["artifacts"],
        name="artifact",
        kind="artifact",
        created="created",
        updated="updated",
        description="description",
        labels=["production"],
    )
