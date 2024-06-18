"""
Task module.
"""
from __future__ import annotations

import typing

from digitalhub_core.context.builder import get_context
from digitalhub_core.entities._base.entity import Entity
from digitalhub_core.entities._builders.metadata import build_metadata
from digitalhub_core.entities._builders.spec import build_spec
from digitalhub_core.entities._builders.status import build_status
from digitalhub_core.entities.entity_types import EntityTypes
from digitalhub_core.entities.runs.crud import delete_run, get_run, new_run, run_from_parameters
from digitalhub_core.utils.api import api_ctx_create, api_ctx_read, api_ctx_update
from digitalhub_core.utils.generic_utils import build_uuid, get_timestamp
from digitalhub_core.utils.io_utils import write_yaml

if typing.TYPE_CHECKING:
    from digitalhub_core.context.context import Context
    from digitalhub_core.entities._base.metadata import Metadata
    from digitalhub_core.entities.runs.entity import Run
    from digitalhub_core.entities.tasks.spec import TaskSpec
    from digitalhub_core.entities.tasks.status import TaskStatus


class Task(Entity):
    """
    A class representing a task.
    """

    ENTITY_TYPE = EntityTypes.TASKS.value

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: TaskSpec,
        status: TaskStatus,
        user: str | None = None,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        project : str
            Project name.
        uuid : str
            UUID.
        kind : str
            Kind of the object.
        metadata : Metadata
            Metadata of the object.
        spec : TaskSpec
            Specification of the object.
        status : TaskStatus
            Status of the object.
        user : str
            Owner of the object.
        """
        super().__init__()
        self.project = project
        self.id = uuid
        self.kind = kind
        self.key = f"store://{project}/{self.ENTITY_TYPE}/{kind}/{uuid}"
        self.metadata = metadata
        self.spec = spec
        self.status = status
        self.user = user

        # Add attributes to be used in the to_dict method
        self._obj_attr.extend(["project", "id", "key"])

    #############################
    #  Save / Refresh / Export
    #############################

    def save(self, update: bool = False) -> Task:
        """
        Save entity into backend.

        Parameters
        ----------
        update : bool
            Flag to indicate update.

        Returns
        -------
        Task
            Entity saved.
        """
        obj = self.to_dict()

        if not update:
            api = api_ctx_create(self.project, self.ENTITY_TYPE)
            new_obj = self._context().create_object(api, obj)
            self._update_attributes(new_obj)
            return self

        self.metadata.updated = obj["metadata"]["updated"] = get_timestamp()
        api = api_ctx_update(self.project, self.ENTITY_TYPE, self.id)
        new_obj = self._context().update_object(api, obj)
        self._update_attributes(new_obj)
        return self

    def refresh(self) -> Task:
        """
        Refresh object from backend.

        Returns
        -------
        Task
            Entity refreshed.
        """
        api = api_ctx_read(self.project, self.ENTITY_TYPE, self.id)
        obj = self._context().read_object(api)
        self._update_attributes(obj)
        return self

    def export(self, filename: str | None = None) -> None:
        """
        Export object as a YAML file.

        Parameters
        ----------
        filename : str
            Name of the export YAML file. If not specified, the default value is used.

        Returns
        -------
        None
        """
        obj = self.to_dict()
        if filename is None:
            filename = f"{self.kind}_{self.name}_{self.id}.yml"
        pth = self._context().project_dir / filename
        pth.parent.mkdir(parents=True, exist_ok=True)
        write_yaml(pth, obj)

    #############################
    #  Context
    #############################

    def _context(self) -> Context:
        """
        Get context.

        Returns
        -------
        Context
            Context.
        """
        return get_context(self.project)

    #############################
    #  Task methods
    #############################

    def run(
        self,
        run_kind: str,
        local_execution: bool = False,
        **kwargs,
    ) -> Run:
        """
        Run task.

        Parameters
        ----------
        run_kind : str
            Kind of the run.
        local_execution : bool
            Flag to indicate if the run will be executed locally.
        **kwargs
            Keyword arguments.

        Returns
        -------
        Run
            Run object.
        """
        return self.new_run(
            project=self.project,
            task=self._get_task_string(),
            kind=run_kind,
            local_execution=local_execution,
            **kwargs,
        )

    def _get_task_string(self) -> str:
        """
        Get task string.

        Returns
        -------
        str
            Task string.
        """
        splitted = self.spec.function.split("://")
        return f"{self.kind}://{splitted[1]}"

    #############################
    # CRUD Methods for Run
    #############################

    def new_run(self, **kwargs) -> Run:
        """
        Create a new run.

        Parameters
        ----------
        **kwargs
            Keyword arguments.

        Returns
        -------
        Run
            Run object.
        """
        if kwargs["local_execution"]:
            return run_from_parameters(**kwargs)
        return new_run(**kwargs)

    def get_run(self, entity_id: str) -> Run:
        """
        Get run.

        Parameters
        ----------
        entity_id : str
            Entity ID.

        Returns
        -------
        Run
            Run object.
        """
        return get_run(self.project, entity_id)

    def delete_run(self, entity_id: str) -> None:
        """
        Delete run.

        Parameters
        ----------
        entity_id : str
            Entity ID.

        Returns
        -------
        None
        """
        delete_run(self.project, entity_id)

    #############################
    #  Static interface methods
    #############################

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
        project = obj.get("project")
        kind = obj.get("kind")

        uuid = build_uuid(obj.get("id"))
        metadata = build_metadata(kind, **obj.get("metadata", {}))
        spec = build_spec(kind, validate=validate, **obj.get("spec", {}))
        status = build_status(kind, **obj.get("status", {}))
        user = obj.get("user")
        return {
            "project": project,
            "uuid": uuid,
            "kind": kind,
            "metadata": metadata,
            "spec": spec,
            "status": status,
            "user": user,
        }


def task_from_parameters(
    project: str,
    kind: str,
    uuid: str | None = None,
    source: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> Task:
    """
    Create a new object instance.

    Parameters
    ----------
    project : str
        Project name.
    kind : str
        Kind of the object.
    uuid : str
        ID of the object in form of UUID.
    source : str
        Remote git source for object.
    labels : list[str]
        List of labels.
    **kwargs
        Spec keyword arguments.

    Returns
    -------
    Task
       Object instance.
    """
    uuid = build_uuid(uuid)
    metadata = build_metadata(
        kind=kind,
        project=project,
        name=uuid,
        source=source,
        labels=labels,
    )
    spec = build_spec(kind, **kwargs)
    status = build_status(kind)
    return Task(
        project=project,
        uuid=uuid,
        kind=kind,
        metadata=metadata,
        spec=spec,
        status=status,
    )


def task_from_dict(obj: dict) -> Task:
    """
    Create Task object from dictionary.

    Parameters
    ----------
    obj : dict
        Dictionary representation of Task.

    Returns
    -------
    Task
        Task object.
    """
    return Task.from_dict(obj)
