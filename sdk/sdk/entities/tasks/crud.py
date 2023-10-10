"""
Module for performing operations on tasks.
"""
from __future__ import annotations

import typing

from sdk.context.builder import get_context
from sdk.entities.tasks.entity import task_from_dict, task_from_parameters
from sdk.utils.api import api_base_delete, api_base_read
from sdk.utils.commons import TASK
from sdk.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from sdk.entities.tasks.entity import Task


def create_task(**kwargs) -> Task:
    """
    Create a new object instance.

    Parameters
    ----------
    **kwargs
        Keyword arguments.

    Returns
    -------
    Task
       Object instance.
    """
    return task_from_parameters(**kwargs)


def new_task(
    project: str,
    kind: str | None = None,
    function: str = "",
    resources: dict | None = None,
    uuid: str | None = None,
    **kwargs,
) -> Task:
    """
    Create a new object instance.

    Parameters
    ----------
    project : str
        Name of the project.
    kind : str, default "task"
        The type of the Task.
    function : str
        The function string identifying the function.
    resources : dict
        The Kubernetes resources for the Task.
    uuid : str
        UUID.
    **kwargs
        Keyword arguments.

    Returns
    -------
    Task
       Object instance.
    """,
    obj = create_task(
        project=project,
        kind=kind,
        function=function,
        resources=resources,
        uuid=uuid,
        **kwargs,
    )
    obj.save()
    return obj


def get_task(project: str, name: str) -> Task:
    """
    Get object from backend.

    Parameters
    ----------
    project : str
        Name of the project.
    name : str
        The name of the task.

    Returns
    -------
    Task
        Object instance.
    """
    api = api_base_read(TASK, name)
    obj = get_context(project).read_object(api)
    return task_from_dict(obj)


def import_task(file: str) -> Task:
    """
    Get object from file.

    Parameters
    ----------
    file : str
        Path to the file.

    Returns
    -------
    Task
        Object instance.
    """
    obj = read_yaml(file)
    return task_from_dict(obj)


def delete_task(project: str, name: str) -> dict:
    """
    Delete task from the backend.

    Parameters
    ----------
    project : str
        Name of the project.
    name : str
        The name of the task.

    Returns
    -------
    dict
        Response from backend.
    """
    api = api_base_delete(TASK, name)
    return get_context(project).delete_object(api)