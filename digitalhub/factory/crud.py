# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import typing
from collections.abc import Callable
from functools import wraps
from typing import Any

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project


def bind_project_shortcut(
    shortcut: Callable[..., Any],
    project: Project,
    refresh_project: bool,
    validate_entity_project: bool = False,
    inject_context: bool = False,
) -> Callable[..., Any]:
    """Bind a global shortcut to a project while preserving its public signature."""
    shortcut_signature = inspect.signature(shortcut)
    project_parameter = shortcut_signature.parameters.get("project")
    context_parameter = shortcut_signature.parameters.get("context")
    injected_parameter = project_parameter or (context_parameter if inject_context else None)

    project_signature = shortcut_signature.replace(
        parameters=tuple(
            parameter
            for parameter in shortcut_signature.parameters.values()
            if injected_parameter is None or parameter.name != injected_parameter.name
        )
    )

    @wraps(shortcut)
    def bound_shortcut(*args, **kwargs):
        if "project" in kwargs:
            raise TypeError("Project-bound shortcuts do not accept a project parameter.")

        arguments = project_signature.bind(*args, **kwargs)
        if validate_entity_project:
            entity = arguments.arguments["entity"]
            if getattr(entity, "project", None) != project.name:
                raise ValueError(f"Entity to update is not in project {project.name}.")
        if injected_parameter is None:
            result = shortcut(**arguments.arguments)
        else:
            result = shortcut(**{injected_parameter.name: project.name, **arguments.arguments})
        if refresh_project:
            project.refresh()
        return result

    bound_shortcut.__signature__ = project_signature
    bound_shortcut.__annotations__ = {
        name: annotation
        for name, annotation in getattr(shortcut, "__annotations__", {}).items()
        if injected_parameter is None or name != injected_parameter.name
    }
    return bound_shortcut
