# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
"""Shared entity fixture validation tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from digitalhub.factory.entity import entity_factory
from jsonschema import ValidationError, validate


class SchemaRegistry:
    """Registry for JSON schemas with lazy loading."""

    def __init__(self, schemas_path: Path):
        self._schemas_path = schemas_path
        self._schema_paths = {path.stem: path for path in schemas_path.rglob("*.json")}

    def get_schema(self, kind: str) -> dict[str, Any]:
        """Load and cache schema by kind."""
        if kind not in self._schema_paths:
            raise ValueError(f"Schema not found for kind: {kind}")
        return json.loads(self._schema_paths[kind].read_text())

    @property
    def available_kinds(self) -> set[str]:
        """Return all available schema kinds."""
        return set(self._schema_paths.keys())


class EntityValidator:
    """Validator for entity JSON files."""

    def __init__(self, schema_registry: SchemaRegistry):
        self.schema_registry = schema_registry

    def load_entity(self, path: Path) -> dict[str, Any]:
        """Load entity from JSON file."""
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in {path}: {error}") from error

    def build_from_file(self, path: Path) -> tuple[dict[str, Any], str]:
        """Build entity object from JSON file using factory."""
        entity = self.load_entity(path)

        if "kind" not in entity:
            raise ValueError(f"Missing 'kind' field in {path}")
        if "spec" not in entity:
            raise ValueError(f"Missing 'spec' field in {path}")

        kind = entity["kind"]
        built = entity_factory.build_spec(kind, **entity["spec"])
        return built.to_dict(), kind

    def validate(self, built: dict[str, Any], kind: str) -> None:
        """Validate built object against its schema."""
        schema = self.schema_registry.get_schema(kind)
        try:
            validate(instance=built, schema=schema)
        except ValidationError as error:
            raise AssertionError(f"Validation failed for kind '{kind}': {error.message}") from error

    def check_schema_completeness(
        self,
        built: dict[str, Any],
        kind: str,
        ignore: set[str] | None = None,
    ) -> list[str]:
        """Check if rebuilt object includes all schema properties."""
        schema = self.schema_registry.get_schema(kind)
        missing_fields = []

        if "properties" in schema:
            schema_fields = set(schema["properties"].keys())
            built_fields = set(built.keys())
            missing_fields = sorted(schema_fields - built_fields - (ignore or set()))

        return missing_fields


def discover_entities(entities_path: Path) -> dict[str, Path]:
    """Discover entity files with collision-resistant naming."""
    entities = {}
    for path in entities_path.rglob("*.json"):
        key = str(path.relative_to(entities_path))
        entities[key] = path
    return entities


def create_test_validate(root: Path, ignore: list[str] | None = None) -> type:
    """Create validation tests for the fixture directories below ``root``."""
    entities_path = root / "entities"
    schemas_path = root / "schemas"
    schema_registry = SchemaRegistry(schemas_path)
    validator = EntityValidator(schema_registry)
    entity_paths = discover_entities(entities_path)
    ignored_fields = set(ignore or [])

    class TestValidate:
        """Test entity JSON files build correctly and validate against schemas."""

        @pytest.mark.parametrize("entity_file", sorted(entity_paths.keys()))
        def test_entity_validation(self, entity_file: str):
            """Test that entity builds from JSON and validates against its schema."""
            path = entity_paths[entity_file]
            built, kind = validator.build_from_file(path)
            validator.validate(built, kind)

        @pytest.mark.parametrize("entity_file", sorted(entity_paths.keys()))
        def test_schema_field_completeness(self, entity_file: str):
            """Test that rebuilt object includes all schema properties."""
            path = entity_paths[entity_file]
            built, kind = validator.build_from_file(path)

            missing = validator.check_schema_completeness(built, kind, ignored_fields)
            if missing:
                schema = validator.schema_registry.get_schema(kind)
                required = schema.get("required", [])
                missing_required = [field for field in missing if field in required]
                missing_optional = [field for field in missing if field not in required]

                message_parts = []
                if missing_required:
                    message_parts.append(f"Missing REQUIRED fields: {missing_required}")
                if missing_optional:
                    message_parts.append(f"Missing optional fields: {missing_optional}")

                pytest.fail(f"Schema completeness check failed for '{kind}': {'; '.join(message_parts)}")

    return TestValidate
