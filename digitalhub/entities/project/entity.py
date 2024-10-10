from __future__ import annotations

import typing
from pathlib import Path
from typing import Any

from digitalhub.client.builder import get_client
from digitalhub.context.builder import set_context
from digitalhub.entities._base.crud import (
    create_entity_api_base,
    read_entity_api_base,
    read_entity_api_ctx,
    update_entity_api_base,
)
from digitalhub.entities._base.entity.base import Entity
from digitalhub.entities._builders.metadata import build_metadata
from digitalhub.entities._builders.name import build_name
from digitalhub.entities._builders.spec import build_spec
from digitalhub.entities._builders.status import build_status
from digitalhub.entities.artifact.crud import (
    artifact_from_dict,
    delete_artifact,
    get_artifact,
    get_artifact_versions,
    import_artifact,
    list_artifacts,
    log_artifact,
    new_artifact,
    update_artifact,
)
from digitalhub.entities.dataitem.crud import (
    dataitem_from_dict,
    delete_dataitem,
    get_dataitem,
    get_dataitem_versions,
    import_dataitem,
    list_dataitems,
    log_dataitem,
    new_dataitem,
    update_dataitem,
)
from digitalhub.entities.entity_types import EntityTypes
from digitalhub.entities.function.crud import (
    delete_function,
    function_from_dict,
    get_function,
    get_function_versions,
    import_function,
    list_functions,
    new_function,
    update_function,
)
from digitalhub.entities.model.crud import (
    delete_model,
    get_model,
    get_model_versions,
    import_model,
    list_models,
    log_model,
    model_from_dict,
    new_model,
    update_model,
)
from digitalhub.entities.run.crud import delete_run, get_run, list_runs
from digitalhub.entities.secret.crud import (
    delete_secret,
    get_secret,
    get_secret_versions,
    import_secret,
    list_secrets,
    new_secret,
    update_secret,
)
from digitalhub.entities.workflow.crud import (
    delete_workflow,
    get_workflow,
    get_workflow_versions,
    import_workflow,
    list_workflows,
    new_workflow,
    update_workflow,
    workflow_from_dict,
)
from digitalhub.utils.exceptions import BackendError, EntityAlreadyExistsError, EntityError
from digitalhub.utils.generic_utils import get_timestamp
from digitalhub.utils.io_utils import write_yaml
from digitalhub.utils.uri_utils import map_uri_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.metadata import Metadata
    from digitalhub.entities.artifact.entity._base import Artifact
    from digitalhub.entities.dataitem.entity._base import Dataitem
    from digitalhub.entities.function.entity import Function
    from digitalhub.entities.model.entity._base import Model
    from digitalhub.entities.project.spec import ProjectSpec
    from digitalhub.entities.project.status import ProjectStatus
    from digitalhub.entities.run.entity import Run
    from digitalhub.entities.secret.entity import Secret
    from digitalhub.entities.workflow.entity import Workflow


ARTIFACTS = EntityTypes.ARTIFACT.value + "s"
FUNCTIONS = EntityTypes.FUNCTION.value + "s"
WORKFLOWS = EntityTypes.WORKFLOW.value + "s"
DATAITEMS = EntityTypes.DATAITEM.value + "s"
MODELS = EntityTypes.MODEL.value + "s"

CTX_ENTITIES = [ARTIFACTS, FUNCTIONS, WORKFLOWS, DATAITEMS, MODELS]

FROM_DICT_MAP = {
    ARTIFACTS: artifact_from_dict,
    FUNCTIONS: function_from_dict,
    WORKFLOWS: workflow_from_dict,
    DATAITEMS: dataitem_from_dict,
    MODELS: model_from_dict,
}

IMPORT_MAP = {
    ARTIFACTS: import_artifact,
    FUNCTIONS: import_function,
    WORKFLOWS: import_workflow,
    DATAITEMS: import_dataitem,
    MODELS: import_model,
}


class Project(Entity):
    """
    A class representing a project.
    """

    ENTITY_TYPE = EntityTypes.PROJECT.value

    def __init__(
        self,
        name: str,
        kind: str,
        metadata: Metadata,
        spec: ProjectSpec,
        status: ProjectStatus,
        user: str | None = None,
        local: bool = False,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)
        self.id = name
        self.name = name
        self.key = f"store://{name}"
        self.spec: ProjectSpec
        self.status: ProjectStatus

        # Add attributes to be used in the to_dict method
        self._obj_attr.extend(["id", "name"])

        # Set client
        self._client = get_client(local)

        # Set context
        set_context(self)

    ##############################
    #  Save / Refresh / Export
    ##############################

    def save(self, update: bool = False) -> Project:
        """
        Save entity into backend.

        Parameters
        ----------
        update : bool
            If True, the object will be updated.

        Returns
        -------
        Project
            Entity saved.
        """
        obj = self._refresh_to_dict()

        if not update:
            new_obj = create_entity_api_base(self._client, self.ENTITY_TYPE, obj)
            new_obj["local"] = self._client.is_local()
            self._update_attributes(new_obj)
            return self

        self.metadata.updated = obj["metadata"]["updated"] = get_timestamp()
        new_obj = update_entity_api_base(self._client, self.ENTITY_TYPE, obj)
        new_obj["local"] = self._client.is_local()
        self._update_attributes(new_obj)
        return self

    def refresh(self) -> Project:
        """
        Refresh object from backend.

        Returns
        -------
        Project
            Project object.
        """
        new_obj = read_entity_api_base(self._client, self.ENTITY_TYPE, self.name)
        new_obj["local"] = self._client.is_local()
        self._update_attributes(new_obj)
        return self

    def export(self, filename: str | None = None) -> str:
        """
        Export object as a YAML file. If the objects are not embedded, the objects are
        exported as a YAML file.

        Parameters
        ----------
        filename : str
            Name of the export YAML file. If not specified, the default value is used.

        Returns
        -------
        str
            Exported file.
        """
        obj = self._refresh_to_dict()

        if filename is None:
            filename = f"{self.kind}_{self.name}.yml"
        pth = Path(self.spec.context) / filename
        pth.parent.mkdir(parents=True, exist_ok=True)
        obj = self._export_not_embedded(obj)
        write_yaml(pth, obj)
        return str(pth)

    def _refresh_to_dict(self) -> dict:
        """
        Try to refresh object to collect entities related to project.

        Returns
        -------
        dict
            Entity object in dictionary format.
        """
        try:
            return self.refresh().to_dict()
        except BackendError:
            return self.to_dict()

    def _export_not_embedded(self, obj: dict) -> dict:
        """
        Export project objects if not embedded.

        Parameters
        ----------
        obj : dict
            Project object in dictionary format.

        Returns
        -------
        dict
            Updatated project object in dictionary format with referenced entities.
        """
        # Cycle over entity types
        for entity_type in CTX_ENTITIES:
            # Entity types are stored as a list of entities
            for idx, entity in enumerate(obj.get("spec", {}).get(entity_type, [])):
                # Export entity if not embedded is in metadata, else do nothing
                if not entity["metadata"]["embedded"]:
                    # Get entity object from backend
                    obj_dict: dict = read_entity_api_ctx(entity["key"])

                    # Create from dict (not need to new method, we do not save to backend)
                    ent = FROM_DICT_MAP[entity_type](obj_dict)

                    # Export and stor ref in object metadata inside project
                    pth = ent.export()
                    obj["spec"][entity_type][idx]["metadata"]["ref"] = pth

        # Return updated object
        return obj

    def _import_entities(self) -> None:
        """
        Import project entities.

        Returns
        -------
        None
        """
        # Cycle over entity types
        for entity_type in CTX_ENTITIES:
            # Entity types are stored as a list of entities
            for entity in getattr(self.spec, entity_type, []):
                entity_metadata = entity["metadata"]
                embedded = entity_metadata.get("embedded", False)
                ref = entity_metadata.get("ref", None)

                # Import entity if not embedded
                if not embedded and ref is not None:
                    # Import entity from local ref
                    if map_uri_scheme(ref) == "local":
                        try:
                            IMPORT_MAP[entity_type](ref)
                        except FileNotFoundError:
                            msg = f"File not found: {ref}."
                            raise EntityError(msg)

                # If entity is embedded, create it and try to save
                elif embedded:
                    try:
                        FROM_DICT_MAP[entity_type](entity).save()
                    except EntityAlreadyExistsError:
                        pass

    ##############################
    #  Static interface methods
    ##############################

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
        name = build_name(obj.get("name"))
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

    ##############################
    #  Artifacts
    ##############################

    def new_artifact(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = True,
        path: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        path : str
            Object path on local file system or remote storage. It is also the destination path of upload() method.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        >>> obj = project.new_artifact(name="my-artifact",
        >>>                            kind="artifact",
        >>>                            path="s3://my-bucket/my-key")
        """
        obj = new_artifact(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def log_artifact(
        self,
        name: str,
        kind: str,
        source: str,
        path: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Create and upload an object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        source : str
            Artifact location on local path.
        path : str
            Destination path of the artifact. If not provided, it's generated.
        **kwargs : dict
            New artifact spec parameters.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        >>> obj = project.log_artifact(name="my-artifact",
        >>>                            kind="artifact",
        >>>                            source="./local-path")
        """
        obj = log_artifact(
            project=self.name,
            name=name,
            kind=kind,
            source=source,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_artifact(
        self,
        identifier: str,
        entity_id: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_artifact("store://my-artifact-key")

        Using entity name:
        >>> obj = project.get_artifact("my-artifact-name"
        >>>                            entity_id="my-artifact-id")
        """
        obj = get_artifact(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_artifact_versions(
        self,
        identifier: str,
        **kwargs,
    ) -> list[Artifact]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Artifact]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_artifact_versions("store://my-artifact-key")

        Using entity name:
        >>> obj = project.get_artifact_versions("my-artifact-name")
        """
        return get_artifact_versions(identifier, project=self.name, **kwargs)

    def list_artifacts(self, **kwargs) -> list[Artifact]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Artifact]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_artifacts()
        """
        return list_artifacts(self.name, **kwargs)

    def import_artifact(
        self,
        file: str,
        **kwargs,
    ) -> Artifact:
        """
        Import object from a YAML file.

        Parameters
        ----------
        file : str
            Path to YAML file.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Artifact
            Object instance.

        Examples
        --------
        >>> obj = project.import_artifact("my-artifact.yaml")
        """
        return import_artifact(file, **kwargs)

    def update_artifact(self, entity: Artifact) -> Artifact:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Artifact
            Object to update.

        Returns
        -------
        Artifact
            Entity updated.

        Examples
        --------
        >>> obj = project.update_artifact(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_artifact(entity)

    def delete_artifact(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        **kwargs,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_artifact("store://my-artifact-key")

        Otherwise:
        >>> project.delete_artifact("my-artifact-name",
        >>>                         delete_all_versions=True)
        """
        delete_artifact(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            **kwargs,
        )
        self.refresh()

    ##############################
    #  Dataitems
    ##############################

    def new_dataitem(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = True,
        path: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        path : str
            Object path on local file system or remote storage. It is also the destination path of upload() method.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        >>> obj = project.new_dataitem(name="my-dataitem",
        >>>                            kind="dataitem",
        >>>                            path="s3://my-bucket/my-key")
        """
        obj = new_dataitem(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def log_dataitem(
        self,
        name: str,
        kind: str,
        source: str | None = None,
        data: Any | None = None,
        extension: str | None = None,
        path: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create and upload an object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        data : Any
            Dataframe to log.
        extension : str
            Extension of the dataitem.
        source : str
            Dataitem location on local path.
        data : Any
            Dataframe to log. Alternative to source.
        extension : str
            Extension of the output dataframe.
        path : str
            Destination path of the dataitem. If not provided, it's generated.
        **kwargs : dict
            New dataitem spec parameters.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        >>> obj = project.log_dataitem(name="my-dataitem",
        >>>                            kind="table",
        >>>                            data=df)
        """
        obj = log_dataitem(
            project=self.name,
            name=name,
            kind=kind,
            path=path,
            source=source,
            data=data,
            extension=extension,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_dataitem(
        self,
        identifier: str,
        entity_id: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_dataitem("store://my-dataitem-key")

        Using entity name:
        >>> obj = project.get_dataitem("my-dataitem-name"
        >>>                            entity_id="my-dataitem-id")
        """
        obj = get_dataitem(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_dataitem_versions(
        self,
        identifier: str,
        **kwargs,
    ) -> list[Dataitem]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Dataitem]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_dataitem_versions("store://my-dataitem-key")

        Using entity name:
        >>> obj = project.get_dataitem_versions("my-dataitem-name")
        """
        return get_dataitem_versions(identifier, project=self.name, **kwargs)

    def list_dataitems(self, **kwargs) -> list[Dataitem]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Dataitem]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_dataitems()
        """
        return list_dataitems(self.name, **kwargs)

    def import_dataitem(
        self,
        file: str,
        **kwargs,
    ) -> Dataitem:
        """
        Import object from a YAML file.

        Parameters
        ----------
        file : str
            Path to YAML file.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Dataitem
            Object instance.

        Examples
        --------
        >>> obj = project.import_dataitem("my-dataitem.yaml")
        """
        return import_dataitem(file, **kwargs)

    def update_dataitem(self, entity: Dataitem) -> Dataitem:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Dataitem
            Object to update.

        Returns
        -------
        Dataitem
            Entity updated.

        Examples
        --------
        >>> obj = project.update_dataitem(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_dataitem(entity)

    def delete_dataitem(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        **kwargs,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_dataitem("store://my-dataitem-key")

        Otherwise:
        >>> project.delete_dataitem("my-dataitem-name",
        >>>                         project="my-project",
        >>>                         delete_all_versions=True)
        """
        delete_dataitem(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            **kwargs,
        )
        self.refresh()

    ##############################
    #  Models
    ##############################

    def new_model(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = True,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        path : str
            Object path on local file system or remote storage. It is also the destination path of upload() method.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        >>> obj = project.new_model(name="my-model",
        >>>                            kind="model",
        >>>                            path="s3://my-bucket/my-key")
        """
        obj = new_model(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def log_model(
        self,
        name: str,
        kind: str,
        source: str,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create and upload an object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        source : str
            Model location on local path.
        path : str
            Destination path of the model. If not provided, it's generated.
        **kwargs : dict
            New model spec parameters.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        >>> obj = project.log_model(name="my-model",
        >>>                            kind="model",
        >>>                            source="./local-path")
        """
        obj = log_model(
            project=self.name,
            name=name,
            kind=kind,
            source=source,
            path=path,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_model(
        self,
        identifier: str,
        entity_id: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_model("store://my-model-key")

        Using entity name:
        >>> obj = project.get_model("my-model-name"
        >>>                            entity_id="my-model-id")
        """
        obj = get_model(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_model_versions(
        self,
        identifier: str,
        **kwargs,
    ) -> list[Model]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Model]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_model_versions("store://my-model-key")

        Using entity name:
        >>> obj = project.get_model_versions("my-model-name")
        """
        return get_model_versions(identifier, project=self.name, **kwargs)

    def list_models(self, **kwargs) -> list[Model]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Model]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_models()
        """
        return list_models(self.name, **kwargs)

    def import_model(
        self,
        file: str,
        **kwargs,
    ) -> Model:
        """
        Import object from a YAML file.

        Parameters
        ----------
        file : str
            Path to YAML file.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Model
            Object instance.

        Examples
        --------
        >>> obj = project.import_model("my-model.yaml")
        """
        return import_model(file, **kwargs)

    def update_model(self, entity: Model) -> Model:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Model
            Object to update.

        Returns
        -------
        Model
            Entity updated.

        Examples
        --------
        >>> obj = project.update_model(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_model(entity)

    def delete_model(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        **kwargs,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_model("store://my-model-key")

        Otherwise:
        >>> project.delete_model("my-model-name",
        >>>                         project="my-project",
        >>>                         delete_all_versions=True)
        """
        delete_model(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            **kwargs,
        )
        self.refresh()

    ##############################
    #  Functions
    ##############################

    def new_function(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = True,
        **kwargs,
    ) -> Function:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Function
            Object instance.

        Examples
        --------
        >>> obj = project.new_function(name="my-function",
        >>>                            kind="python",
        >>>                            code_src="function.py",
        >>>                            handler="function-handler")
        """
        obj = new_function(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_function(
        self,
        identifier: str,
        entity_id: str | None = None,
        **kwargs,
    ) -> Function:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Function
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_function("store://my-function-key")

        Using entity name:
        >>> obj = project.get_function("my-function-name"
        >>>                            entity_id="my-function-id")
        """
        obj = get_function(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_function_versions(
        self,
        identifier: str,
        **kwargs,
    ) -> list[Function]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Function]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_function_versions("store://my-function-key")

        Using entity name:
        >>> obj = project.get_function_versions("my-function-name")
        """
        return get_function_versions(identifier, project=self.name, **kwargs)

    def list_functions(self, **kwargs) -> list[Function]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Function]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_functions()
        """
        return list_functions(self.name, **kwargs)

    def import_function(
        self,
        file: str,
        **kwargs,
    ) -> Function:
        """
        Import object from a YAML file.

        Parameters
        ----------
        file : str
            Path to YAML file.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Function
            Object instance.

        Examples
        --------
        >>> obj = project.import_function("my-function.yaml")
        """
        return import_function(file, **kwargs)

    def update_function(self, entity: Function) -> Function:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Function
            Object to update.

        Returns
        -------
        Function
            Entity updated.

        Examples
        --------
        >>> obj = project.update_function(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_function(entity)

    def delete_function(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
        **kwargs,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        cascade : bool
            Cascade delete.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_function("store://my-function-key")

        Otherwise:
        >>> project.delete_function("my-function-name",
        >>>                         delete_all_versions=True)
        """
        delete_function(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
            **kwargs,
        )
        self.refresh()

    ##############################
    #  Workflows
    ##############################

    def new_workflow(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = True,
        **kwargs,
    ) -> Workflow:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Workflow
            Object instance.

        Examples
        --------
        >>> obj = project.new_workflow(name="my-workflow",
        >>>                            kind="kfp",
        >>>                            code_src="pipeline.py",
        >>>                            handler="pipeline-handler")
        """
        obj = new_workflow(
            project=self.name,
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_workflow(
        self,
        identifier: str,
        entity_id: str | None = None,
        **kwargs,
    ) -> Workflow:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Workflow
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_workflow("store://my-workflow-key")

        Using entity name:
        >>> obj = project.get_workflow("my-workflow-name"
        >>>                            entity_id="my-workflow-id")
        """
        obj = get_workflow(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_workflow_versions(
        self,
        identifier: str,
        **kwargs,
    ) -> list[Workflow]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Workflow]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_workflow_versions("store://my-workflow-key")

        Using entity name:
        >>> obj = project.get_workflow_versions("my-workflow-name")
        """
        return get_workflow_versions(identifier, project=self.name, **kwargs)

    def list_workflows(self, **kwargs) -> list[Workflow]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Workflow]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_workflows()
        """
        return list_workflows(self.name, **kwargs)

    def import_workflow(
        self,
        file: str,
        **kwargs,
    ) -> Workflow:
        """
        Import object from a YAML file.

        Parameters
        ----------
        file : str
            Path to YAML file.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Workflow
            Object instance.

        Examples
        --------
        >>> obj = project.import_workflow("my-workflow.yaml")
        """
        return import_workflow(file, **kwargs)

    def update_workflow(self, entity: Workflow) -> Workflow:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Workflow
            Object to update.

        Returns
        -------
        Workflow
            Entity updated.

        Examples
        --------
        >>> obj = project.update_workflow(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_workflow(entity)

    def delete_workflow(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
        **kwargs,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        cascade : bool
            Cascade delete.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_workflow("store://my-workflow-key")

        Otherwise:
        >>> project.delete_workflow("my-workflow-name",
        >>>                         delete_all_versions=True)
        """
        delete_workflow(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
            **kwargs,
        )
        self.refresh()

    ##############################
    #  Secrets
    ##############################

    def new_secret(
        self,
        name: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = True,
        secret_value: str | None = None,
        **kwargs,
    ) -> Secret:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        uuid : str
            ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        secret_value : str
            Value of the secret.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Secret
            Object instance.

        Examples
        --------
        >>> obj = project.new_secret(name="my-secret",
        >>>                          secret_value="my-secret-value")
        """
        obj = new_secret(
            project=self.name,
            name=name,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            secret_value=secret_value,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_secret(
        self,
        identifier: str,
        entity_id: str | None = None,
        **kwargs,
    ) -> Secret:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Secret
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_secret("store://my-secret-key")

        Using entity name:
        >>> obj = project.get_secret("my-secret-name"
        >>>                          entity_id="my-secret-id")
        """
        obj = get_secret(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            **kwargs,
        )
        self.refresh()
        return obj

    def get_secret_versions(
        self,
        identifier: str,
        **kwargs,
    ) -> list[Secret]:
        """
        Get object versions from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Secret]
            List of object instances.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_secret_versions("store://my-secret-key")

        Using entity name:
        >>> obj = project.get_secret_versions("my-secret-name")
        """
        return get_secret_versions(identifier, project=self.name, **kwargs)

    def list_secrets(self, **kwargs) -> list[Secret]:
        """
        List all latest version objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Secret]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_secrets()
        """
        return list_secrets(self.name, **kwargs)

    def import_secret(
        self,
        file: str,
        **kwargs,
    ) -> Secret:
        """
        Import object from a YAML file.

        Parameters
        ----------
        file : str
            Path to YAML file.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Secret
            Object instance.

        Examples
        --------
        >>> obj = project.import_secret("my-secret.yaml")
        """
        return import_secret(file, **kwargs)

    def update_secret(self, entity: Secret) -> Secret:
        """
        Update object. Note that object spec are immutable.

        Parameters
        ----------
        entity : Secret
            Object to update.

        Returns
        -------
        Secret
            Entity updated.

        Examples
        --------
        >>> obj = project.update_secret(obj)
        """
        if entity.project != self.name:
            raise ValueError(f"Entity {entity.name} is not in project {self.name}.")
        return update_secret(entity)

    def delete_secret(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        **kwargs,
    ) -> None:
        """
        Delete object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity name.
        entity_id : str
            Entity ID.
        delete_all_versions : bool
            Delete all versions of the named entity. If True, use entity name instead of entity key as identifier.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        If delete_all_versions is False:
        >>> project.delete_secret("store://my-secret-key")

        Otherwise:
        >>> project.delete_secret("my-secret-name",
        >>>                       delete_all_versions=True)
        """
        delete_secret(
            identifier=identifier,
            project=self.name,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            **kwargs,
        )
        self.refresh()

    ##############################
    #  Runs
    ##############################

    def get_run(
        self,
        identifier: str,
        **kwargs,
    ) -> Run:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        Run
            Object instance.

        Examples
        --------
        Using entity key:
        >>> obj = project.get_run("store://my-secret-key")

        Using entity ID:
        >>> obj = project.get_run("123")
        """
        obj = get_run(
            identifier=identifier,
            project=self.name,
            **kwargs,
        )
        self.refresh()
        return obj

    def list_runs(self, **kwargs) -> list[Run]:
        """
        List all latest objects from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Run]
            List of object instances.

        Examples
        --------
        >>> objs = project.list_runs()
        """
        if kwargs is None:
            kwargs = {}
        return list_runs(self.name, **kwargs)

    def delete_run(
        self,
        identifier: str,
        **kwargs,
    ) -> None:
        """
        Delete run from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity ID.
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        dict
            Response from backend.

        Examples
        --------
        >>> project.delete_run("store://my-run-key")

        """
        delete_run(
            identifier=identifier,
            project=self.name,
            **kwargs,
        )
        self.refresh()
