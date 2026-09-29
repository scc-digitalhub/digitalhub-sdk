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
    # Read the original shortcut's rules so this wrapper can accept the same inputs.
    shortcut_signature = inspect.signature(shortcut)
    project_parameter = shortcut_signature.parameters.get("project")
    context_parameter = shortcut_signature.parameters.get("context")
    # The wrapper fills in the project itself; some shortcuts call that value "context".
    injected_parameter = project_parameter or (context_parameter if inject_context else None)
    # Hide the value filled by this wrapper so callers do not have to pass it again.
    project_signature = shortcut_signature.replace(
        parameters=tuple(
            parameter
            for parameter in shortcut_signature.parameters.values()
            if injected_parameter is None or parameter.name != injected_parameter.name
        )
    )

    @wraps(shortcut)
    def bound_shortcut(*args, **kwargs):

        # This shortcut already belongs to one project, so callers cannot choose another.
        if "project" in kwargs:
            raise TypeError("Project-bound shortcuts do not accept a project parameter.")

        # Check required inputs and names before forwarding them to the original shortcut.
        arguments = project_signature.bind(*args, **kwargs)
        if validate_entity_project:
            # Prevent an update from changing an entity owned by a different project.
            entity = arguments.arguments["entity"]
            if getattr(entity, "project", None) != project.name:
                raise ValueError(f"Entity to update is not in project {project.name}.")

        shortcut_arguments = dict(arguments.arguments)
        # Find extra named inputs to forward.
        keyword_parameter = next(
            (
                parameter
                for parameter in project_signature.parameters.values()
                if parameter.kind is inspect.Parameter.VAR_KEYWORD
            ),
            None,
        )
        if keyword_parameter is not None:
            # No extra inputs means the group is absent, so use an empty mapping.
            shortcut_arguments.update(shortcut_arguments.pop(keyword_parameter.name, {}))

        if injected_parameter is not None:
            # Add the project that was fixed when this wrapper was created.
            shortcut_arguments[injected_parameter.name] = project.name

        # Run the original shortcut with the caller's inputs and the bound project.
        result = shortcut(**shortcut_arguments)

        if refresh_project:
            # Reload only when requested, so the object reflects changes made by the shortcut.
            project.refresh()

        return result

    # Show callers and editor tools only the inputs they can actually provide.
    bound_shortcut.__signature__ = project_signature
    # Keep type hints in sync with that public signature.
    bound_shortcut.__annotations__ = {
        name: annotation
        for name, annotation in getattr(shortcut, "__annotations__", {}).items()
        if injected_parameter is None or name != injected_parameter.name
    }
    return bound_shortcut
