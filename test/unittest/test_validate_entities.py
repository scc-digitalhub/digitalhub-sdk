import pytest

from test._digitalhub_test_helpers.validate_entities import EntityValidator


class SchemaRegistryStub:
    def __init__(self, schema):
        self.schema = schema

    def get_schema(self, kind):
        return self.schema


def test_validate_supports_unicode_property_regex():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "pattern": r"^\p{L}+$",
            }
        },
        "required": ["name"],
    }
    validator = EntityValidator(SchemaRegistryStub(schema))

    validator.validate({"name": "Caf\u00e9"}, "artifact")

    with pytest.raises(AssertionError, match="Validation failed"):
        validator.validate({"name": "Caf\u00e91"}, "artifact")
