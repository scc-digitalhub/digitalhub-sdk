# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import Mock

import pytest
from pydantic import BaseModel

import digitalhub.entities._mixin.source.entity as source_entity_module
from digitalhub.entities._mixin.source.builder import SourceBuilderMixin
from digitalhub.entities._mixin.source.entity import SourceEntityMixin
from digitalhub.entities._mixin.source.models import HandlerSourceCode
from digitalhub.utils.exceptions import EntityError


class PythonSourceCode(HandlerSourceCode):
    DEFAULT_LANG: ClassVar[str | None] = "python"
    REQUIRE_HANDLER: ClassVar[bool] = True


class SourceSpec(BaseModel):
    source: PythonSourceCode


class BuiltEntity:
    def _post_build_source_check(self):
        return self


class SourceBuilderBase:
    ENTITY_SPEC_CLASS = SourceSpec

    def build(self, *args, **kwargs):
        self.kwargs = kwargs
        self.spec = SourceSpec.model_validate(kwargs)
        return BuiltEntity()

    def from_dict(self, obj):
        self.obj = obj
        return BuiltEntity()


class SourceBuilder(SourceBuilderMixin, SourceBuilderBase):
    pass


class SourceEntity(SourceEntityMixin):
    def __init__(self, source: PythonSourceCode, context_root: Path):
        self.spec = SimpleNamespace(source=source)
        self.project = "project"
        self.name = "entity"
        self.id = "entity-id"
        self.ENTITY_TYPE = "function"
        self._context = Mock(return_value=SimpleNamespace(root=context_root, config={}))

    def _is_inlineable_source(self, path: str) -> bool:
        return path.endswith(".py")


class ExportFailure:
    def export(self):
        raise RuntimeError("export failed")


class ExportableSourceEntity(SourceEntityMixin, ExportFailure):
    def __init__(self, source: PythonSourceCode, context_root: Path):
        self.spec = SimpleNamespace(source=source)
        context = SimpleNamespace(root=context_root, ensure_root=Mock(return_value=context_root))
        self._context = Mock(return_value=context)

    def _is_inlineable_source(self, path: str) -> bool:
        return path.endswith(".py")


def test_source_code_normalizes_inline_code_and_validates_required_fields():
    source = PythonSourceCode(code="print('hello')", handler="main")

    assert source.base64 == "cHJpbnQoJ2hlbGxvJyk="
    assert source.lang == "python"
    assert "code" not in source.model_dump()

    with pytest.raises(EntityError, match="Handler must be provided"):
        PythonSourceCode(source="main.py")


def test_source_builder_collects_top_level_inputs_without_mutating_nested_source():
    nested_source = {"source": "nested.py", "handler": "nested"}
    builder = SourceBuilder()

    entity = builder.build(source=nested_source, handler="top-level", code="print('hello')")

    assert entity is not None
    assert builder.kwargs == {
        "source": {
            "source": "nested.py",
            "handler": "nested",
            "code": "print('hello')",
        }
    }
    assert builder.spec.source.source == "nested.py"
    assert builder.spec.source.base64 == "cHJpbnQoJ2hlbGxvJyk="
    assert nested_source == {"source": "nested.py", "handler": "nested"}


def test_source_builder_normalizes_code_src_and_source_model_inputs():
    source = PythonSourceCode(source="nested.py", handler="nested")
    builder = SourceBuilder()

    builder.build(source=source, code_src="remote.py")

    assert builder.spec.source.source == "nested.py"
    assert builder.spec.source.handler == "nested"
    assert source.source == "nested.py"


def test_source_entity_inlines_only_runtime_approved_files(tmp_path, monkeypatch):
    source_path = tmp_path / "main.py"
    source_path.write_text("print('hello')", encoding="utf-8")
    entity = SourceEntity(PythonSourceCode(source=str(source_path), handler="main"), tmp_path)
    monkeypatch.setattr(source_entity_module, "has_local_scheme", lambda _: True)

    entity._post_build_source_check()

    assert entity.spec.source.base64 == "cHJpbnQoJ2hlbGxvJyk="
    assert entity.spec.source.source == str(source_path)


def test_source_entity_archives_directories_and_cleans_temporary_archive(tmp_path, monkeypatch):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "main.py").write_text("print('hello')", encoding="utf-8")
    entity = SourceEntity(PythonSourceCode(source=str(source_dir), handler="main"), tmp_path)
    uploaded_paths = []
    store = Mock()

    def upload(path, destination):
        uploaded_paths.append(Path(path))
        assert uploaded_paths[-1].is_file()
        assert destination == "store://project/entity/archive.zip"

    store.upload.side_effect = upload
    get_default_store_uri = Mock(return_value="s3://default")
    monkeypatch.setattr(source_entity_module, "has_local_scheme", lambda _: True)
    monkeypatch.setattr(source_entity_module, "get_default_store_uri", get_default_store_uri)
    monkeypatch.setattr(
        source_entity_module,
        "build_zip_path",
        lambda _entity, _name, **_kwargs: "store://project/entity/archive.zip",
    )
    monkeypatch.setattr(source_entity_module, "get_store", lambda _destination: store)

    entity._post_build_source_check()

    assert entity.spec.source.source == "store://project/entity/archive.zip"
    assert len(uploaded_paths) == 1
    assert not uploaded_paths[0].exists()
    get_default_store_uri.assert_called_once_with({})


def test_source_export_restores_base64_when_export_raises(tmp_path, monkeypatch):
    source = PythonSourceCode(source="main.py", handler="main", base64="cHJpbnQoJ2hlbGxvJyk=")
    entity = ExportableSourceEntity(source, tmp_path)
    context = entity._context.return_value
    monkeypatch.setattr(source_entity_module, "has_local_scheme", lambda _: True)
    monkeypatch.setattr(source_entity_module, "write_text", lambda *_args: None)

    with pytest.raises(RuntimeError, match="export failed"):
        entity.export()

    assert source.base64 == "cHJpbnQoJ2hlbGxvJyk="
    context.ensure_root.assert_called_once_with()
