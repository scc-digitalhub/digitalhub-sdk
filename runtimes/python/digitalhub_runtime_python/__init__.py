from __future__ import annotations

from digitalhub_runtime_python.utils.utils import handler

from digitalhub.entities.entity_types import EntityTypes
from digitalhub.registry.registry import registry
from digitalhub.registry.utils import create_info

root = "digitalhub_runtime_python"
runtime_info = {
    "module": f"{root}.runtimes.runtime",
    "class_name": "RuntimePython",
    "kind_registry_module": f"{root}.runtimes.kind_registry",
    "kind_registry_class_name": "kind_registry",
}

root_ent = f"{root}.entities"


# Function
entity_type = EntityTypes.FUNCTION.value
func_kind = "python"
prefix = entity_type.capitalize()
suffix = func_kind.capitalize()
func_info = create_info(root_ent, entity_type, prefix, suffix, runtime_info)
registry.register(func_kind, func_info)


# Tasks
entity_type = EntityTypes.TASK.value
for i in ["job", "build", "serve"]:
    task_kind = f"{func_kind}+{i}"
    prefix = entity_type.capitalize()
    suffix = i.capitalize()
    task_info = create_info(root_ent, entity_type, prefix, suffix, runtime_info)
    registry.register(task_kind, task_info)


# Runs
entity_type = EntityTypes.RUN.value
run_kind = f"{func_kind}+run"
prefix = entity_type.capitalize()
suffix = func_kind.capitalize()
run_info = create_info(root_ent, entity_type, prefix, suffix, runtime_info)
registry.register(run_kind, run_info)
