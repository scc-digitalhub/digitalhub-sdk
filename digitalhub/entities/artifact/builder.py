from __future__ import annotations

import typing

from digitalhub.entities._builders.metadata import build_metadata
from digitalhub.entities._builders.name import build_name
from digitalhub.entities._builders.spec import build_spec
from digitalhub.entities._builders.status import build_status
from digitalhub.entities._builders.uuid import build_uuid
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact.entity._base import Artifact

# Manage class mapper
cls_mapper = {}

try:
    from digitalhub.entities.artifact.entity.artifact import ArtifactArtifact

    cls_mapper["artifact"] = ArtifactArtifact
except ImportError:
    pass


def _choose_artifact_type(kind: str) -> type[Artifact]:
    """
    Choose class based on kind.

    Parameters
    ----------
    kind : str
        Kind the object.

    Returns
    -------
    type[Artifact]
        Class of the artifact.
    """
    try:
        return cls_mapper[kind]
    except KeyError:
        raise EntityError(f"Unknown artifact kind: {kind}")


def artifact_from_parameters(
    project: str,
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
    project : str
        Project name.
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
    """
    if path is None:
        raise EntityError("Path must be provided.")
    name = build_name(name)
    uuid = build_uuid(uuid)
    metadata = build_metadata(
        kind,
        project=project,
        name=name,
        version=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
    )
    spec = build_spec(
        kind,
        path=path,
        **kwargs,
    )
    status = build_status(kind)
    cls = _choose_artifact_type(kind)
    return cls(
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
    Create a new object from dictionary.

    Parameters
    ----------
    obj : dict
        Dictionary to create object from.

    Returns
    -------
    Artifact
        Object instance.
    """
    kind = obj.get("kind")
    cls = _choose_artifact_type(kind)
    return cls.from_dict(obj)
