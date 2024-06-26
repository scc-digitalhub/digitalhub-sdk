from __future__ import annotations

import typing
from typing import Any

from digitalhub_core.entities._builders.metadata import build_metadata
from digitalhub_core.entities._builders.spec import build_spec
from digitalhub_core.entities._builders.status import build_status
from digitalhub_core.entities.projects.entity import CTX_ENTITIES, FUNC_MAP, Project
from digitalhub_core.utils.generic_utils import build_uuid
from digitalhub_data.entities.dataitems.crud import (
    create_dataitem_from_dict,
    delete_dataitem,
    get_dataitem,
    list_dataitems,
    new_dataitem,
)
from digitalhub_data.entities.entity_types import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub_data.entities.dataitems.entity._base import Dataitem


DATAITEMS = EntityTypes.DATAITEMS.value

CTX_ENTITIES.append(DATAITEMS)
FUNC_MAP[DATAITEMS] = create_dataitem_from_dict


class ProjectData(Project):

    """
    ProjectData class.
    """

    #############################
    #  Dataitems
    #############################

    def new_dataitem(self, **kwargs) -> Dataitem:
        """
        Create a Dataitem.

        Parameters
        ----------
        **kwargs
            Keyword arguments.

        Returns
        -------
        Dataitem
           Object instance.
        """
        kwargs["project"] = self.name
        obj = new_dataitem(**kwargs)
        self._add_object(obj, DATAITEMS)
        return obj

    def get_dataitem(self, entity_name: str | None = None, entity_id: str | None = None, **kwargs) -> Dataitem:
        """
        Get object from backend.

        Parameters
        ----------
        entity_name : str
            Entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Dataitem
            Instance of Dataitem class.
        """
        obj = get_dataitem(self.name, entity_name=entity_name, entity_id=entity_id, **kwargs)
        self._add_object(obj, DATAITEMS)
        return obj

    def delete_dataitem(self, entity_name: str | None = None, entity_id: str | None = None, **kwargs) -> None:
        """
        Delete a Dataitem from project.

        Parameters
        ----------
        entity_name : str
            Entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        None
        """
        delete_dataitem(self.name, entity_name=entity_name, entity_id=entity_id, **kwargs)
        self._delete_object(DATAITEMS, entity_name, entity_id)

    def set_dataitem(self, dataitem: Dataitem) -> None:
        """
        Set a Dataitem.

        Parameters
        ----------
        dataitem : Dataitem
            Dataitem to set.

        Returns
        -------
        None
        """
        self._add_object(dataitem, DATAITEMS)

    def list_dataitems(self, **kwargs) -> list[dict]:
        """
        List dataitems associated with the project.

        Parameters
        ----------
        **kwargs : dict
            Filters to apply to the list. Shold be params={"filter": "value"}.

        Returns
        -------
        list[dict]
            List of objects related to project.
        """
        return list_dataitems(self.name, **kwargs)

    def log_dataitem(
        self,
        name: str,
        kind: str,
        path: str,
        target_path: str | None = None,
        data: Any | None = None,
        extension: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Log an dataitem to the project.

        Parameters
        ----------
        name : str
            Name that identifies the object.
        kind : str
            Kind of the dataitem.
        path : str
            Destination path of the dataitem.
        target_path : str
            Target path of the dataitem.
        data : Any
            Dataframe to log.
        extension : str
            Extension of the dataitem.
        **kwargs : dict
            New dataitem parameters.

        Returns
        -------
        Dataitem
            Object instance.
        """
        dataitem = new_dataitem(self.name, name, kind, path, **kwargs)
        if kind == "table":
            dataitem.write_df(target_path, data, extension)

    @staticmethod
    def _parse_dict(obj: dict, validate: bool = True) -> dict:
        """
        Get dictionary and parse it to a valid entity dictionary.

        Parameters
        ----------
        entity : str
            Entity type.
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        # Override methods to search in digitalhub_data
        name = build_uuid(obj.get("name"))
        kind = obj.get("kind")
        metadata = build_metadata(kind, **obj.get("metadata", {}))
        spec = build_spec(kind, validate=validate, **obj.get("spec", {}))
        status = build_status(kind, **obj.get("status", {}))
        user = obj.get("user")
        local = obj.get("local", False)
        return {
            "name": name,
            "kind": kind,
            "metadata": metadata,
            "spec": spec,
            "status": status,
            "user": user,
            "local": local,
        }


def project_from_parameters(
    name: str,
    kind: str,
    description: str | None = None,
    source: str | None = None,
    labels: list[str] | None = None,
    local: bool = False,
    context: str | None = None,
    **kwargs,
) -> ProjectData:
    """
    Create project.

    Parameters
    ----------
    name : str
        Name that identifies the object.
    kind : str
        Kind of the object.
    description : str
        Description of the object.
    source : str
        Remote git source for object.
    labels : list[str]
        List of labels.
    local : bool
        Flag to determine if object will be exported to backend.
    context : str
        The context of the project.
    **kwargs
        Spec keyword arguments.

    Returns
    -------
    ProjectData
        ProjectData object.
    """
    name = build_uuid(name)
    spec = build_spec(
        kind,
        context=context,
        **kwargs,
    )
    metadata = build_metadata(
        kind,
        project=name,
        name=name,
        description=description,
        labels=labels,
        source=source,
    )
    status = build_status(kind)
    return ProjectData(
        name=name,
        kind=kind,
        metadata=metadata,
        spec=spec,
        status=status,
        local=local,
    )


def project_from_dict(obj: dict) -> ProjectData:
    """
    Create project from dictionary.

    Parameters
    ----------
    obj : dict
        Dictionary to create object from.

    Returns
    -------
    ProjectData
        ProjectData object.
    """
    return ProjectData.from_dict(obj)
