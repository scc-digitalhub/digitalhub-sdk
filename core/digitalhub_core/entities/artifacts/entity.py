"""
Artifact module.
"""
from __future__ import annotations

import typing
from pathlib import Path
from urllib.parse import urlparse

from digitalhub_core.context.builder import get_context
from digitalhub_core.entities._base.entity import Entity
from digitalhub_core.entities._builders.metadata import build_metadata
from digitalhub_core.entities._builders.spec import build_spec
from digitalhub_core.entities._builders.status import build_status
from digitalhub_core.entities.entity_types import EntityTypes
from digitalhub_core.stores.builder import get_store
from digitalhub_core.utils.api import api_ctx_create, api_ctx_read, api_ctx_update
from digitalhub_core.utils.exceptions import EntityError
from digitalhub_core.utils.file_utils import get_file_info
from digitalhub_core.utils.generic_utils import build_uuid, check_overwrite, get_timestamp
from digitalhub_core.utils.io_utils import write_yaml
from digitalhub_core.utils.uri_utils import check_local_path

if typing.TYPE_CHECKING:
    from digitalhub_core.context.context import Context
    from digitalhub_core.entities._base.metadata import Metadata
    from digitalhub_core.entities.artifacts.spec import ArtifactSpec
    from digitalhub_core.entities.artifacts.status import ArtifactStatus


class Artifact(Entity):
    """
    A class representing a artifact.

    Artifacts are (binary) objects stored in one of the artifact
    stores of the platform, and available to every process, module
    and component as files.
    """

    ENTITY_TYPE = EntityTypes.ARTIFACTS.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: ArtifactSpec,
        status: ArtifactStatus,
        user: str | None = None,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        project : str
            Project name.
        name : str
            Name of the object.
        uuid : str
            Version of the object.
        kind : str
            Kind of the object.
        metadata : Metadata
            Metadata of the object.
        spec : ArtifactSpec
            Specification of the object.
        status : ArtifactStatus
            Status of the object.
        user : str
            Owner of the object.
        """
        super().__init__()
        self.project = project
        self.name = name
        self.id = uuid
        self.kind = kind
        self.key = f"store://{project}/{self.ENTITY_TYPE}/{kind}/{name}:{uuid}"
        self.metadata = metadata
        self.spec = spec
        self.status = status
        self.user = user

        # Add attributes to be used in the to_dict method
        self._obj_attr.extend(["project", "name", "id", "key"])

    #############################
    #  Save / Refresh / Export
    #############################

    def save(self, update: bool = False) -> Artifact:
        """
        Save entity into backend.

        Parameters
        ----------
        update : bool
            Flag to indicate update.

        Returns
        -------
        Artifact
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

    def refresh(self) -> Artifact:
        """
        Refresh object from backend.

        Returns
        -------
        Artifact
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
        pth = self._context().root / filename
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
    #  Artifacts Methods
    #############################

    def as_file(self) -> str:
        """
        Get artifact as file. In the case of a local store, the store returns the current
        path of the artifact. In the case of a remote store, the artifact is downloaded in
        a temporary directory.

        Returns
        -------
        str
            Path of the artifact (temporary or not).
        """
        # Check if target path is provided and if it is remote
        trg = self.spec.path
        self._check_remote(trg)

        # If local store, return local artifact path
        # Check if source path is provided and if it is local
        store = get_store(trg)
        if store.is_local():
            self._check_local(self.spec.src_path)
            return self.spec.src_path

        return store.download(trg)

    def download(
        self,
        destination: str | None = None,
        overwrite: bool = False,
    ) -> str:
        """
        Download artifact from remote storage.

        Parameters
        ----------
        destination : str
            Destination path as filename.
        overwrite : bool
            Specify if overwrite an existing file. Default value is False.

        Returns
        -------
        str
            Path of the downloaded artifact.
        """

        # Check if target path is remote
        path = self.spec.path
        self._check_remote(path)

        # Check if download destination path is specified and rebuild it if necessary
        if destination is None:
            filename = Path(urlparse(path).path).name
            destination = f"{self.project}/{self.ENTITY_TYPE}/{self.id}/{filename}"

        # Check if destination path is local
        self._check_local(destination)

        # Check if destination path exists for overwrite
        check_overwrite(destination, overwrite)

        # Download artifact and return path
        store = get_store(path)
        return store.download(path, destination)

    def upload(self, source: str | None = None) -> str:
        """
        Upload artifact to remote storage from given local path to
        spec path destination.

        Parameters
        ----------
        source : str
            Source path is the local path of the artifact.

        Returns
        -------
        str
            Path of the uploaded artifact.
        """
        # Check if target path is remote
        path = self.spec.path
        self._check_remote(path)

        # Check if source path is provided and if it is local
        src = source if source is not None else self.spec.src_path
        self._check_local(src)

        self.refresh()
        self._get_file_info(src)
        self.save(update=True)

        # Get store and upload artifact and return remote path
        store = get_store(path)
        return store.upload(src, path)

    #############################
    #  Private Helpers
    #############################

    @staticmethod
    def _check_local(path: str) -> None:
        """
        Check through URI scheme if given path is local or not.

        Parameters
        ----------
        path : str
            Path of some source.

        Returns
        -------
        None

        Raises
        ------
        EntityError
            If source path is not local.
        """
        if not check_local_path(path):
            raise EntityError("Only local paths are supported for source paths.")

    @staticmethod
    def _check_remote(path: str) -> None:
        """
        Check through URI scheme if given path is remote.

        Parameters
        ----------
        path : str
            Path of some source.

        Returns
        -------
        None

        Raises
        ------
        EntityError
            If source path is local.
        """
        if check_local_path(path):
            raise EntityError("Only remote paths are supported for target paths.")

    def _get_file_info(self, src_path: str) -> None:
        """
        Get file info from path.

        Parameters
        ----------
        src_path : str
            Local path of some source.

        Returns
        -------
        None
        """
        file_info = get_file_info(self.spec.path, src_path)
        self.status.add_file(file_info)

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
        name = obj.get("name")
        kind = obj.get("kind")
        uuid = build_uuid(obj.get("id"))
        metadata = build_metadata(kind, **obj.get("metadata", {}))
        spec = build_spec(kind, validate=validate, **obj.get("spec", {}))
        status = build_status(kind, **obj.get("status", {}))
        user = obj.get("user")
        return {
            "project": project,
            "name": name,
            "uuid": uuid,
            "kind": kind,
            "metadata": metadata,
            "spec": spec,
            "status": status,
            "user": user,
        }


def artifact_from_parameters(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    description: str | None = None,
    source: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = True,
    path: str | None = None,
    src_path: str | None = None,
    **kwargs,
) -> Artifact:
    """
    Create an instance of the Artifact class with the provided parameters.

    Parameters
    ----------
    project : str
        Project name.
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
    embedded : bool
        Flag to determine if object must be embedded in project.
    path : str
        Object path on local file system or remote storage.
        If not provided, it's generated.
    src_path : str
        Local object path.
    **kwargs
        Spec keyword arguments.

    Returns
    -------
    Artifact
        Artifact object.
    """
    if path is None:
        raise EntityError("Path must be provided.")
    uuid = build_uuid(uuid)
    metadata = build_metadata(
        kind,
        project=project,
        name=name,
        version=uuid,
        description=description,
        source=source,
        labels=labels,
        embedded=embedded,
    )
    spec = build_spec(
        kind,
        path=path,
        src_path=src_path,
        **kwargs,
    )
    status = build_status(kind)
    return Artifact(
        project=project,
        name=name,
        uuid=uuid,
        kind=kind,
        metadata=metadata,
        spec=spec,
        status=status,
    )


def artifact_from_dict(obj: dict) -> Artifact:
    """
    Create artifact from dictionary.

    Parameters
    ----------
    obj : dict
        Dictionary to create object from.

    Returns
    -------
    Artifact
        Artifact object.
    """
    return Artifact.from_dict(obj)
