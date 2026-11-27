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


def test_processors_are_created_where_they_are_used() -> None:
    # A module-level processor is a singleton: every user imports the module
    # that builds it, which turns that module into an import hub.
    violations = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        for node in ast.parse(path.read_text()).body:
            value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id.endswith("Processor"):
                violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{node.lineno}: {value.func.id}()")

    assert violations == [], "\n".join(violations)


def _active_record_calls(source: str) -> list[tuple[int, str]]:
    calls = []
    for cls in ast.parse(source).body:
        if not (isinstance(cls, ast.ClassDef) and cls.name.endswith("Processor")):
            continue
        for node in ast.walk(cls):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            method, receiver = node.func.attr, node.func.value
            # Calls on the processor itself, on its attributes, or on a processor
            # or runtime built on the spot are not entity calls.
            built_on_the_spot = isinstance(receiver, ast.Call) and ast.unparse(receiver.func).endswith(
                ("Processor", "build_runtime")
            )
            if built_on_the_spot or ast.unparse(receiver).split(".")[0] == "self":
                continue
            # dict.update(other) takes an argument; the entity methods take none.
            no_arguments = not node.args and not node.keywords
            if method in ("save", "run", "wait") or (method in ("update", "refresh") and no_arguments):
                calls.append((node.lineno, ast.unparse(node.func)))
    return calls


def test_processors_do_not_call_active_record_methods() -> None:
    # save(), update(), refresh(), run() and wait() of an entity call the processors
    # back. Processors use the CRUD processor, then _update_attributes() when
    # the caller keeps the same object.
    violations = [
        f"{path.relative_to(PACKAGE_ROOT.parent)}:{line}: {call}()"
        for path in sorted(PACKAGE_ROOT.rglob("*.py"))
        for line, call in _active_record_calls(path.read_text())
    ]

    assert violations == [], "\n".join(violations)


def test_entities_and_contexts_resolve_clients_at_use_time() -> None:
    # The default client is reached only through resolve_client(), the single
    # hook for per-project credentials. Holding get_client() or the factory
    # here reintroduces clients that go stale after set_client_config().
    roots = (PACKAGE_ROOT / "entities", PACKAGE_ROOT / "context")
    forbidden = {"get_client", "client_factory"}
    violations = []
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            for node in ast.walk(ast.parse(path.read_text())):
                if not isinstance(node, ast.ImportFrom) or node.module != "digitalhub.stores.client.factory":
                    continue
                for alias in node.names:
                    if alias.name in forbidden:
                        violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{node.lineno}: {alias.name}")

    assert violations == [], "\n".join(violations)


def test_client_components_receive_configuration_explicitly() -> None:
    # Clients with different configurations coexist only if no component
    # reads the global one. The default client factory is the one reader.
    client_root = PACKAGE_ROOT / "stores" / "client"
    allowed = {client_root / "common" / "config.py", client_root / "factory.py"}
    violations = []
    for path in sorted(client_root.rglob("*.py")):
        if path in allowed:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.ImportFrom):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.Attribute):
                names = [node.attr]
            elif isinstance(node, ast.Name):
                names = [node.id]
            if "get_client_config" in names or "_default_config" in names:
                violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{node.lineno}")

    assert violations == [], "\n".join(violations)


def test_stores_receive_credentials_instead_of_reaching_the_client() -> None:
    # Stores get their credentials from the session that builds them, so the
    # session can later give each project its own. Only the store API module
    # reads the client, for the default store URI.
    data_root = PACKAGE_ROOT / "stores" / "data"
    allowed = {data_root / "api.py"}
    violations = []
    for path in sorted(data_root.rglob("*.py")):
        if path in allowed:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module == "digitalhub.stores.client.factory":
                violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{node.lineno}")

    assert violations == [], "\n".join(violations)


def test_runtime_state_is_owned_by_sessions() -> None:
    # Connection pools, identities, clients, contexts and stores belong to the
    # session; a module-level instance would escape its configuration.
    owners = {"Client", "ClientConfigurator", "ContextBuilder", "HttpTransport", "Session", "StoreBuilder"}
    violations = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        for node in ast.parse(path.read_text()).body:
            value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in owners:
                violations.append(f"{path.relative_to(PACKAGE_ROOT.parent)}:{node.lineno}: {value.func.id}()")

    assert violations == [], "\n".join(violations)
