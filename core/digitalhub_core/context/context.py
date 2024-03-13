"""
Context module.
"""
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from digitalhub_core.entities.projects.entity import Project


class Context:
    """
    Context class.

    It contains the project name, client and information about the type of client.
    It exposes CRUD operations for the entities and act as a layer between the
    project object and the client.
    The context is created by the context builder.
    """

    def __init__(self, project: Project) -> None:
        """
        Constructor.

        Parameters
        ----------
        project : Project
            The project object to create the context from.
        """
        self.name = project.name
        self.client = project._client
        self.local = project._client.is_local()
        self.project_dir = project.spec.context

    def create_object(self, api: str, obj: dict, **kwargs) -> dict:
        """
        Create an object.

        Parameters
        ----------
        obj : dict
            The object to create.
        api : str
            The api to create the object with.

        Returns
        -------
        dict
            The created object.
        """
        return self.client.create_object(api, obj, **kwargs)

    def read_object(self, api: str, **kwargs) -> dict:
        """
        Get an object.

        Parameters
        ----------
        api : str
            The api to get the object with.

        Returns
        -------
        dict
            The read object.
        """
        return self.client.read_object(api, **kwargs)

    def update_object(self, api: str, obj: dict, **kwargs) -> dict:
        """
        Update an object.

        Parameters
        ----------
        obj : dict
            The object to update.
        api : str
            The api to update the object with.

        Returns
        -------
        dict
            The updated object.
        """
        return self.client.update_object(api, obj, **kwargs)

    def delete_object(self, api: str, **kwargs) -> dict:
        """
        Delete an object.

        Parameters
        ----------
        api : str
            The api to delete the object with.

        Returns
        -------
        dict
            The deleted object.
        """
        return self.client.delete_object(api, **kwargs)

    def list_objects(self, api: str, **kwargs) -> dict:
        """
        List objects.

        Parameters
        ----------
        api : str
            The api to list the objects with.
        filters : dict
            The filters to list the objects with.

        Returns
        -------
        dict
            The list of objects.
        """
        return self.client.list_objects(api, **kwargs)
