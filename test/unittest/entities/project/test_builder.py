from unittest.mock import Mock

from digitalhub.entities.project._base.builder import ProjectProjectBuilder


def test_project_builder_preserves_extensions(monkeypatch) -> None:
    builder = ProjectProjectBuilder()
    build_entity = Mock(return_value="project")
    monkeypatch.setattr(builder, "build_entity", build_entity)
    extensions = [{"key": "value"}]

    result = builder.build(
        name="project",
        kind="project/project",
        extensions=extensions,
    )

    assert result == "project"
    build_entity.assert_called_once_with(
        name="project",
        kind="project/project",
        metadata=build_entity.call_args.kwargs["metadata"],
        spec=build_entity.call_args.kwargs["spec"],
        status=build_entity.call_args.kwargs["status"],
        extensions=extensions,
    )


def test_project_builder_parses_extensions_from_dict(monkeypatch) -> None:
    builder = ProjectProjectBuilder()
    build_entity = Mock(return_value="project")
    monkeypatch.setattr(builder, "build_entity", build_entity)
    extensions = [{"key": "value"}]

    result = builder.from_dict(
        {
            "name": "project",
            "kind": "project/project",
            "metadata": {},
            "spec": {},
            "status": {},
            "extensions": extensions,
        }
    )

    assert result == "project"
    assert build_entity.call_args.kwargs["extensions"] == extensions
