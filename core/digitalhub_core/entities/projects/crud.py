"""
Project operations module.
"""
from __future__ import annotations

import importlib.util as imputil
import typing
from pathlib import Path

from digitalhub_core.client.builder import build_client, get_client
from digitalhub_core.context.builder import delete_context
from digitalhub_core.entities.projects.entity import project_from_dict, project_from_parameters
from digitalhub_core.utils.api import api_base_delete, api_base_read, api_base_update
from digitalhub_core.utils.exceptions import BackendError, EntityError
from digitalhub_core.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub_core.entities.projects.entity import Project


ENTITY_TYPE = "projects"


def create_project(**kwargs) -> Project:
    """
    Create a new project.

    Parameters
    ----------
    **kwargs
        Keyword arguments.

    Returns
    -------
    Project
        A Project instance.
    """
    return project_from_parameters(**kwargs)


def create_project_from_dict(obj: dict) -> Project:
    """
    Create a new Project instance from a dictionary.

    Parameters
    ----------
    obj : dict
        Dictionary to create object from.

    Returns
    -------
    Project
        Project object.
    """
    return project_from_dict(obj)


def load_project(
    name: str | None = None,
    filename: str | None = None,
    local: bool = False,
    config: dict | None = None,
    setup_kwargs: dict | None = None,
    **kwargs,
) -> Project:
    """
    Load project and context from backend or file.

    Parameters
    ----------
    name : str
        Project name.
    local : bool
        Flag to determine if backend is local.
    config : dict
        DHCore env configuration.
    setup_kwargs : dict
        Setup keyword arguments.
    **kwargs
        Keyword arguments.

    Returns
    -------
    Project
        A Project instance with setted context.
    """
    if name is not None:
        return get_project(name=name, local=local, config=config, setup_kwargs=setup_kwargs)
    if filename is not None:
        return import_project(filename, local=local, config=config, setup_kwargs=setup_kwargs)
    raise EntityError("Either name or filename must be provided.")


def get_or_create_project(
    name: str,
    local: bool = False,
    config: dict | None = None,
    setup_kwargs: dict | None = None,
    **kwargs,
) -> Project:
    """
    Get or create a project.

    Parameters
    ----------
    name : str
        Project name.
    local : bool
        Flag to determine if backend is local.
    config : dict
        DHCore env configuration.
    setup_kwargs : dict
        Setup keyword arguments.
    **kwargs
        Keyword arguments.

    Returns
    -------
    Project
        A Project instance.
    """
    try:
        return get_project(name, local, config=config, setup_kwargs=setup_kwargs, **kwargs)
    except BackendError:
        return new_project(name, local=local, config=config, setup_kwargs=setup_kwargs, **kwargs)


def new_project(
    name: str,
    description: str | None = None,
    source: str | None = None,
    labels: list[str] | None = None,
    local: bool = False,
    config: dict | None = None,
    context: str | None = None,
    setup_kwargs: dict | None = None,
    **kwargs,
) -> Project:
    """
    Create project.

    Parameters
    ----------
    name : str
        Name that identifies the object.
    kind : str
        Kind of the object.
    uuid : str
        ID of the object in form of UUID.
    description : str
        Description of the object.
    source : str
        Remote git source for object.
    labels : list[str]
        List of labels.
    local : bool
        Flag to determine if object will be exported to backend.
    config : dict
        DHCore env configuration.
    context : str
        The context of the project.
    setup_kwargs : dict
        Setup keyword arguments.
    **kwargs
        Keyword arguments.

    Returns
    -------
    Project
        Project object.
    """
    build_client(local, config)
    obj = create_project(
        name=name,
        kind="project",
        description=description,
        source=source,
        labels=labels,
        local=local,
        context=context,
        **kwargs,
    )
    obj.save()
    return _setup_project(obj, setup_kwargs)


def get_project(
    name: str,
    local: bool = False,
    config: dict | None = None,
    setup_kwargs: dict | None = None,
    **kwargs,
) -> Project:
    """
    Retrieves project details from backend.

    Parameters
    ----------
    name : str
        The Project name.
    local : bool
        Flag to determine if backend is local.
    config : dict
        DHCore env configuration.
    setup_kwargs : dict
        Setup keyword arguments.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    Project
        Object instance.
    """
    build_client(local, config)
    api = api_base_read("projects", name)
    client = get_client(local)
    obj = client.read_object(api, **kwargs)
    obj["local"] = local
    project = create_project_from_dict(obj)
    return _setup_project(project, setup_kwargs)


def import_project(
    file: str,
    local: bool = False,
    config: dict | None = None,
    setup_kwargs: dict | None = None,
) -> Project:
    """
    Import an Project object from a file using the specified file path.

    Parameters
    ----------
    file : str
        Path to the file.
    local : bool
        Flag to determine if backend is local.
    config : dict
        DHCore env configuration.

    Returns
    -------
    Project
        Object instance.
    """
    build_client(local, config)
    obj: dict = read_yaml(file)
    obj["local"] = local
    project = create_project_from_dict(obj)
    return _setup_project(project, setup_kwargs)


def delete_project(
    name: str, cascade: bool = True, clean_context: bool = True, local: bool = False, **kwargs
) -> list[dict]:
    """
    Delete a project.

    Parameters
    ----------
    name : str
        Project name.
    cascade : bool
        Flag to determine if delete is cascading.
    clean_context : bool
        Flag to determine if context will be deleted. If a context is deleted,
        all its objects are unreacheable.
    local : bool
        Flag to determine if backend is local.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    dict
        Response from backend.
    """
    client = get_client(local)
    api = api_base_delete("projects", name)
    params = kwargs.get("params", {})
    if params is None or not params:
        kwargs["params"] = {}
    kwargs["params"]["cascade"] = str(cascade).lower()
    response = client.delete_object(api, **kwargs)
    if clean_context:
        delete_context(name)
    return response


def update_project(entity: Project, local: bool = False, **kwargs) -> dict:
    """
    Update object in backend.

    Parameters
    ----------
    entity : Project
        The object to update.
    local : bool
        Flag to determine if backend is local.
    **kwargs : dict
        Parameters to pass to the API call.

    Returns
    -------
    dict
        Response from backend.
    """
    api = api_base_update("projects", entity.name)
    client = get_client(local)
    return client.update_object(api, entity.to_dict(), **kwargs)


def _setup_project(project: Project, setup_kwargs: dict = None) -> Project:
    """
    Search for setup_project.py file and launch setup
    hanlder as project hook.

    Parameters
    ----------
    project : Project
        The project to scafold.
    setup_kwargs : dict
        Arguments to pass to setup handler.

    Returns
    -------
    Project
        Set up project.
    """
    if setup_kwargs is None:
        setup_kwargs = {}
    check_pth = Path(project.spec.context, ".CHECK")
    setup_pth = Path(project.spec.context, "setup_project.py")
    if setup_pth.exists() and not check_pth.exists():
        spec = imputil.spec_from_file_location("setup_project", setup_pth)
        mod = imputil.module_from_spec(spec)
        spec.loader.exec_module(mod)
        handler = getattr(mod, "setup")
        project = handler(project, **setup_kwargs)
        check_pth.touch()
    return project
