"""
Project module.
"""
from __future__ import annotations

import typing

from sdk.entities.api import DTO_ARTF, DTO_DTIT, DTO_FUNC, DTO_WKFL, create_api_proj
from sdk.entities.artifact.artifact import Artifact
from sdk.entities.artifact.operations import delete_artifact, get_artifact, new_artifact
from sdk.entities.base_entity import Entity, EntityMetadata, EntitySpec
from sdk.entities.dataitem.dataitem import Dataitem
from sdk.entities.dataitem.operations import delete_dataitem, get_dataitem, new_dataitem
from sdk.entities.function.function import Function
from sdk.entities.function.operations import delete_function, get_function, new_function
from sdk.entities.workflow.operations import delete_workflow, get_workflow, new_workflow
from sdk.entities.workflow.workflow import Workflow
from sdk.utils.factories import get_client, set_context
from sdk.utils.utils import get_uiid

if typing.TYPE_CHECKING:
    from sdk.client.client import Client


DTO_LIST = [DTO_ARTF, DTO_FUNC, DTO_WKFL, DTO_DTIT]


class ProjectMetadata(EntityMetadata):
    """
    Project metadata.
    """


class ProjectSpec(EntitySpec):
    """
    Project specification.
    """
    def __init__(
        self,
        context: str = None,
        source: str = None,
        functions: list[dict] = None,
        artifacts: list[dict] = None,
        workflows: list[dict] = None,
        dataitems: list[dict] = None,
        **kwargs,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        **kwargs
            Additional keyword arguments.

        Notes
        -----
        If some of the attributes are not in the signature,
        they will be added as new attributes.
        """
        self.context = context
        self.source = source
        self.functions = functions if functions is not None else []
        self.artifacts = artifacts if artifacts is not None else []
        self.workflows = workflows if workflows is not None else []
        self.dataitems = dataitems if dataitems is not None else []

        # Set new attributes
        for k, v in kwargs.items():
            if k not in self.__dict__:
                self.__setattr__(k, v)

        set_context(self)

class Project(Entity):
    """
    A class representing a project.
    """

    def __init__(
        self,
        name: str,
        metadata: ProjectMetadata = None,
        spec: ProjectSpec = None,
        local: bool = False,
        uuid: str = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Project instance.

        Parameters
        ----------
        name : str
            Name of the project.
        metadata : ProjectMetadata, optional
            Metadata for the function, default is None.
        spec : ProjectSpec, optional
            Specification for the function, default is None.
        local: bool, optional
            Specify if run locally, default is False.
        **kwargs
            Additional keyword arguments.
        """
        super().__init__()
        self.name = name
        self.kind = "project"
        self.metadata = metadata if metadata is not None else ProjectMetadata(name=name)
        self.spec = spec if spec is not None else ProjectSpec()
        self.id = uuid if uuid is not None else get_uiid()

        # Client and local flag
        self._local = local
        self._client = get_client() if not self.local else None

        # Object attributes
        self._artifacts = []
        self._functions = []
        self._workflows = []
        self._dataitems = []

        # Set new attributes
        for k, v in kwargs.items():
            if k not in self._obj_attr:
                self.__setattr__(k, v)

    #############################
    #  Save / Export
    #############################

    def save(self, uuid: bool = None) -> dict:
        """
        Save project and context into backend.

        Parameters
        ----------
        save_object : bool, optional
            Flag to determine if object related to project will be saved.

        uuid : bool, optional
            Ignored, placed for compatibility with other objects.

        Returns
        -------
        dict
            Mapping representation of Project from backend.

        """
        responses = []
        if self.local:
            raise Exception("Use .export() for local execution.")

        obj = self.to_dict()

        # Try to create project
        # (try to avoid error response if project already exists)
        try:
            api = create_api_proj()
            response = self.client.create_object(obj, api)
            responses.append(response)
        except Exception:
            ...

        # Try to save objects related to project
        # (try to avoid error response if object does not exists)
        for i in DTO_LIST:
            for j in self._get_objects(i):
                try:
                    obj = j.save(uuid=j.id)
                    responses.append(obj)
                except Exception:
                    ...

        return responses

    def export(self, filename: str = None) -> None:
        """
        Export object as a YAML file. If the objects are not embedded, the objects are
        exported as a YAML file.

        Parameters
        ----------
        filename : str, optional
            Name of the export YAML file. If not specified, the default value is used.

        Returns
        -------
        None

        """
        obj = self.to_dict()
        filename = filename if filename is not None else "project.yaml"
        self.export_object(filename, obj)

        # Export objects related to project if not embedded
        for i in DTO_LIST:
            for obj in self._get_objects(i):
                if not obj.embedded:
                    obj.export()

    #############################
    #  Generic operations for objects (artifacts, functions, workflows, dataitems)
    #############################

    def _add_object(self, obj: Entity, kind: str) -> None:
        """
        Add object to project as class object and spec.

        Parameters
        ----------
        obj : Entity
            Object to be added to project.
        kind : str
            Kind of object to be added to project.

        Returns
        -------
        None
        """
        # Add to project spec
        obj_dict = obj.to_dict_essential() if not obj.embedded else obj.to_dict()
        attr = getattr(self.spec, kind, []) + [obj_dict]
        setattr(self.spec, kind, attr)

        # Add to project objects
        if kind in DTO_LIST:
            kind = f"_{kind}"
        attr = getattr(self, kind, []) + [obj]
        setattr(self, kind, attr)

    def _delete_object(self, name: str, kind: str, uuid: str = None) -> None:
        """
        Delete object from project.

        Parameters
        ----------
        name : str
            Name of object to be deleted.
        kind : str
            Kind of object to be deleted.
        uuid : str, optional
            UUID of object to be deleted.

        Returns
        -------
        None
        """
        if uuid is None:
            attr_name = "name"
            var = name
        else:
            attr_name = "id"
            var = uuid

        # Delete from project spec
        spec_list = getattr(self.spec, kind, [])
        setattr(self.spec, kind, [i for i in spec_list if i.get(attr_name) != var])

        # Delete from project objects
        if kind in DTO_LIST:
            kind = f"_{kind}"
        obj_list = getattr(self, kind, [])
        setattr(self, kind, [i for i in obj_list if getattr(i, attr_name) != var])

    def _get_objects(self, kind: str) -> object:
        """
        Get objects related to project.

        Parameters
        ----------
        kind : str
            Kind of object to be retrieved.

        Returns
        -------
        object
            Object related to project.
        """
        if kind in DTO_LIST:
            kind = f"_{kind}"
        return getattr(self, kind, [])

    #############################
    #  Artifacts
    #############################

    def new_artifact(
        self,
        name: str,
        description: str = None,
        kind: str = None,
        key: str = None,
        src_path: str = None,
        target_path: str = None,
        local: bool = False,
        embed: bool = False,
    ) -> Artifact:
        """
        Create an instance of the Artifact class with the provided parameters.

        Parameters
        ----------
        name : str
            Identifier of the artifact.
        description : str, optional
            Description of the artifact.
        kind : str, optional
            The type of the artifact.
        key : str
            Representation of artfact like store://etc..
        src_path : str
            Path to the artifact on local file system or remote storage.
        target_path : str
            Path of destionation for the artifact.
        local : bool, optional
            Flag to determine if object has local execution.
        embed : bool, optional
            Flag to determine if object must be embedded in project.

        Returns
        -------
        Artifact
            Instance of the Artifact class representing the specified artifact.
        """
        obj = new_artifact(
            project=self.name,
            name=name,
            description=description,
            kind=kind,
            key=key,
            src_path=src_path,
            target_path=target_path,
            local=local,
            embed=embed,
        )
        self._add_object(obj, DTO_ARTF)
        return obj

    def get_artifact(self, name: str, uuid: str = None) -> Artifact:
        """
        Get a Artifact from backend.

        Parameters
        ----------
        name : str
            Identifier of the artifact.
        uuid : str, optional
            Identifier of the artifact version.

        Returns
        -------
        Artifact
            Instance of Artifact class.
        """
        obj = get_artifact(
            project=self.name,
            name=name,
            uuid=uuid,
        )
        self._add_object(obj, DTO_ARTF)
        return obj

    def delete_artifact(self, name: str, uuid: str = None) -> None:
        """
        Delete a Artifact from project.

        Parameters
        ----------
        name : str
            Identifier of the artifact.
        uuid : str, optional
            Identifier of the artifact version.

        Returns
        -------
        None
        """
        if not self.local:
            delete_artifact(self.name, name)
        self._delete_object(name, DTO_ARTF, uuid=uuid)

    def set_artifact(self, artifact: Artifact) -> None:
        """
        Set a Artifact.

        Parameters
        ----------
        artifact : Artifact
            Artifact to set.

        Returns
        -------
        None
        """
        self._add_object(artifact, DTO_ARTF)

    #############################
    #  Functions
    #############################

    def new_function(
        self,
        name: str,
        description: str = None,
        kind: str = None,
        source: str = None,
        image: str = None,
        tag: str = None,
        handler: str = None,
        local: bool = False,
        embed: bool = False,
    ) -> Function:
        """
        Create a Function instance with the given parameters.

        Parameters
        ----------
        project : str
            Name of the project.
        name : str
            Identifier of the Function.
        description : str, optional
            Description of the Function.
        kind : str, optional
            The type of the Function.
        source : str, optional
            Path to the Function's source code on the local file system or remote storage.
        image : str, optional
            Name of the Function's Docker image.
        tag : str, optional
            Tag of the Function's Docker image.
        handler : str, optional
            Function handler name.
        local : bool, optional
            Flag to determine if object has local execution.
        embed : bool, optional
            Flag to determine if object must be embedded in project.

        Returns
        -------
        Function
            Instance of the Function class representing the specified function.
        """
        obj = new_function(
            project=self.name,
            name=name,
            description=description,
            kind=kind,
            source=source,
            image=image,
            tag=tag,
            handler=handler,
            local=local,
            embed=embed,
        )
        self._add_object(obj, DTO_FUNC)
        return obj

    def get_function(self, name: str, uuid: str = None) -> Function:
        """
        Get a Function from backend.

        Parameters
        ----------
        name : str
            Identifier of the function.
        uuid : str, optional
            Identifier of the function version.

        Returns
        -------
        Function
            Instance of Function class.
        """
        obj = get_function(
            project=self.name,
            name=name,
            uuid=uuid,
        )
        self._add_object(obj, DTO_FUNC)
        return obj

    def delete_function(self, name: str, uuid: str = None) -> None:
        """
        Delete a Function from project.

        Parameters
        ----------
        name : str
            Identifier of the function.
        uuid : str, optional
            Identifier of the function version.

        Returns
        -------
        None
        """
        if not self.local:
            delete_function(self.name, name)
        self._delete_object(name, DTO_FUNC, uuid=uuid)

    def set_function(self, function: Function) -> None:
        """
        Set a Function.

        Parameters
        ----------
        function : Function
            Function to set.

        Returns
        -------
        None
        """
        self._add_object(function, DTO_FUNC)

    #############################
    #  Workflows
    #############################

    def new_workflow(
        self,
        name: str,
        description: str = None,
        kind: str = None,
        test: str = None,
        local: bool = False,
        embed: bool = False,
    ) -> Workflow:
        """
        Create a new Workflow instance with the specified parameters.

        Parameters
        ----------
        project : str
            A string representing the project associated with this workflow.
        name : str
            The name of the workflow.
        description : str, optional
            A description of the workflow.
        kind : str, optional
            The kind of the workflow.
        spec : dict, optional
            The specification for the workflow.
        local : bool, optional
            Flag to determine if object has local execution.
        embed : bool, optional
            Flag to determine if object must be embedded in project.

        Returns
        -------
        Workflow
            An instance of the created workflow.
        """
        obj = new_workflow(
            project=self.name,
            name=name,
            description=description,
            kind=kind,
            test=test,
            local=local,
            embed=embed,
        )
        self._add_object(obj, DTO_WKFL)
        return obj

    def get_workflow(self, name: str, uuid: str = None) -> Workflow:
        """
        Get a Workflow from backend.

        Parameters
        ----------
        name : str
            Identifier of the workflow.
        uuid : str, optional
            Identifier of the workflow version.

        Returns
        -------
        Workflow
            Instance of Workflow class.
        """
        obj = get_workflow(
            project=self.name,
            name=name,
            uuid=uuid,
        )
        self._add_object(obj, DTO_WKFL)
        return obj

    def delete_workflow(self, name: str, uuid: str = None) -> None:
        """
        Delete a Workflow from project.

        Parameters
        ----------
        name : str
            Identifier of the workflow.
        uuid : str, optional
            Identifier of the workflow version.

        Returns
        -------
        None
        """
        if not self.local:
            delete_workflow(self.name, name)
        self._delete_object(name, DTO_WKFL, uuid=uuid)

    def set_workflow(self, workflow: Workflow) -> None:
        """
        Set a Workflow.

        Parameters
        ----------
        workflow : Workflow
            Workflow to set.

        Returns
        -------
        None
        """
        self._add_object(workflow, DTO_WKFL)

    #############################
    #  Dataitems
    #############################

    def new_dataitem(
        self,
        name: str,
        description: str = None,
        kind: str = None,
        key: str = None,
        path: str = None,
        local: bool = False,
        embed: bool = False,
    ) -> Dataitem:
        """
        Create a Dataitem.

        Parameters
        ----------
        name : str
            Identifier of the dataitem.
        description : str, optional
            Description of the dataitem.
        kind : str, optional
            The type of the dataitem.
        key : str
            Representation of artfact like store://etc..
        path : str
            Path to the dataitem on local file system or remote storage.
        local : bool, optional
            Flag to determine if object has local execution.
        embed : bool, optional
            Flag to determine if object must be embedded in project.

        Returns
        -------
        Dataitem
            Instance of the Dataitem class representing the specified dataitem.
        """
        obj = new_dataitem(
            project=self.name,
            name=name,
            description=description,
            kind=kind,
            key=key,
            path=path,
            local=local,
            embed=embed,
        )
        self._add_object(obj, DTO_DTIT)
        return obj

    def get_dataitem(self, name: str, uuid: str = None) -> Dataitem:
        """
        Get a Dataitem from backend.

        Parameters
        ----------
        name : str
            Identifier of the dataitem.
        uuid : str, optional
            Identifier of the dataitem version.

        Returns
        -------
        Dataitem
            Instance of Dataitem class.
        """
        obj = get_dataitem(
            project=self.name,
            name=name,
            uuid=uuid,
        )
        self._add_object(obj, DTO_DTIT)
        return obj

    def delete_dataitem(self, name: str, uuid: str = None) -> None:
        """
        Delete a Dataitem from project.

        Parameters
        ----------
        name : str
            Identifier of the dataitem.
        uuid : str, optional
            Identifier of the dataitem version.

        Returns
        -------
        None
        """
        if not self.local:
            delete_dataitem(self.name, name)
        self._delete_object(name, DTO_DTIT, uuid=uuid)

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
        self._add_object(dataitem, DTO_DTIT)

    #############################
    #  Getters and Setters
    #############################

    @property
    def client(self) -> Client:
        """
        Get client.
        """
        if self._client is None and not self.local:
            raise Exception("Client is not specified.")
        return self._client

    @property
    def local(self) -> bool:
        """
        Get local flag.
        """
        return self._local

    #############################
    #  Generic Methods
    #############################

    @classmethod
    def from_dict(cls, obj_dict: dict) -> "Project":
        """
        Create Project instance from a dictionary.

        Parameters
        ----------
        obj_dict : dict
            Dictionary to create Project from.

        Returns
        -------
        Project
            Project instance.

        """
        name = obj_dict.get("name")
        if name is None:
            raise Exception("Project name not specified.")

        spec = obj_dict.get("spec")
        if spec is None:
            spec = {}

        metadata = ProjectMetadata.from_dict(obj_dict.get("metadata", {"name": name}))

        # Process spec
        spec_list = DTO_LIST + ["source", "context"]
        new_spec = {k: v for k, v in spec.items() if k in spec_list}
        new_spec = ProjectSpec.from_dict(new_spec)
        obj = cls(name, metadata=metadata, spec=new_spec)

        # Add objects to project from spec
        for i in [Function.from_dict(i) for i in spec.get(DTO_FUNC, [])]:
            obj._add_object(i, DTO_FUNC)
        for i in [Artifact.from_dict(i) for i in spec.get(DTO_ARTF, [])]:
            obj._add_object(i, DTO_ARTF)
        for i in [Workflow.from_dict(i) for i in spec.get(DTO_WKFL, [])]:
            obj._add_object(i, DTO_WKFL)
        for i in [Dataitem.from_dict(i) for i in spec.get(DTO_DTIT, [])]:
            obj._add_object(i, DTO_DTIT)

        return obj
