# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[2] / "digitalhub"


def _runtime_imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text())
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    imports = []
    for node in ast.walk(tree):
        parent = parents.get(node)
        inside_type_checking = False
        while parent is not None:
            if isinstance(parent, ast.If):
                test = parent.test
                if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                    inside_type_checking = True
                    break
                if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                    inside_type_checking = True
                    break
            parent = parents.get(parent)
        if inside_type_checking:
            continue

        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append((node.lineno, node.module))
        elif isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
    return imports


def test_common_modules_remain_pure() -> None:
    common_root = PACKAGE_ROOT / "entities" / "_commons"
    forbidden_prefixes = (
        "digitalhub.context",
        "digitalhub.entities._processors",
    )

    violations = []
    for path in sorted(common_root.rglob("*.py")):
        for line, module in _runtime_imports(path):
            forbidden_dependency = any(
                module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_prefixes
            )
            imports_crud_module = "crud" in module.split(".")
            if forbidden_dependency or imports_crud_module:
                violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{line}: {module}")

    assert violations == [], "\n".join(violations)


def test_pure_helpers_remain_in_their_owner_modules() -> None:
    assert (PACKAGE_ROOT / "entities" / "_commons" / "keys.py").is_file()
    assert (PACKAGE_ROOT / "entities" / "_processors" / "crud_factory.py").is_file()
    assert not (PACKAGE_ROOT / "entities" / "_commons" / "crud_factory.py").exists()


def test_transport_and_reader_modules_do_not_depend_on_entities() -> None:
    roots = (
        PACKAGE_ROOT / "stores" / "client",
        PACKAGE_ROOT / "stores" / "readers",
    )
    violations = []
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            for line, module in _runtime_imports(path):
                if module == "digitalhub.entities" or module.startswith("digitalhub.entities."):
                    violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{line}: {module}")

    assert violations == [], "\n".join(violations)


def test_entity_mixins_do_not_import_public_crud_modules() -> None:
    mixin_root = PACKAGE_ROOT / "entities" / "_mixin"
    violations = []
    for path in sorted(mixin_root.rglob("*.py")):
        for line, module in _runtime_imports(path):
            if "crud" in module.split("."):
                violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{line}: {module}")

    assert violations == [], "\n".join(violations)


def test_processors_remain_explicit_without_provider_registry() -> None:
    processor_root = PACKAGE_ROOT / "entities" / "_processors"
    assert not (processor_root / "operations.py").exists()
    assert not (processor_root / "service_locator.py").exists()
