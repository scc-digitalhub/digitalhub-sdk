"""
Artifact base specification module.
"""
from __future__ import annotations

from digitalhub_core.entities._base.spec import Spec, SpecParams


class ArtifactSpec(Spec):
    """
    Artifact specification.
    """

    def __init__(
        self,
        path: str | None = None,
        src_path: str | None = None,
        hash: str | None = None,
        size: int | None = None,
        file_type: str | None = None,
        file_extension: str | None = None,
        **kwargs,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        path : str
            The target path of the artifact.
        src_path : str
            The source path of the artifact.
        hash : str
            The hash of the artifact.
        size : int
            The size of the artifact.
        file_type : str
            The mimetype of the artifact.
        file_extension : str
            The file extension of the artifact.
        **kwargs
            Keywords arguments.
        """
        self.path = path
        self.src_path = src_path
        self.hash = hash
        self.size = size
        self.file_type = file_type
        self.file_extension = file_extension

        self._any_setter(**kwargs)


class ArtifactParams(SpecParams):
    """
    Artifact base parameters.
    """

    path: str = None
    """Target path of the artifact."""

    src_path: str = None
    """Source path of the artifact."""

    hash: str = None
    """Hash of the artifact."""

    size: int = None
    """Size of the artifact."""

    file_type: str = None
    """Mimetype of the artifact."""

    file_extension: str = None
    """File extension of the artifact."""
