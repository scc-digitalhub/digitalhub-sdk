from unittest.mock import Mock

import digitalhub.entities.project.crud as project_crud
from digitalhub.entities._commons.enums import EntityKinds


def test_new_project_passes_extensions_to_processor(monkeypatch) -> None:
    create_project = Mock(return_value="project")
    setup_project = Mock(return_value="configured-project")
    monkeypatch.setattr(project_crud.base_crud_processor, "create_project_entity", create_project)
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
