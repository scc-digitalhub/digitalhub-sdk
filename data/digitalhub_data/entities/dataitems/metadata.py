"""
Dataitem metadata module.
"""
from __future__ import annotations

from digitalhub_core.entities._base.metadata import Metadata


class DataitemMetadata(Metadata):
    """
    A class representing Dataitem metadata.
    """

    def __init__(
        self,
        project: str | None = None,
        name: str | None = None,
        version: str | None = None,
        source: str | None = None,
        labels: list[str] | None = None,
        created: str | None = None,
        updated: str | None = None,
        description: str | None = None,
        embedded: bool = False,
        **kwargs,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        project : str
            Project name.
        version : str
            Version of the object.
        description : str
            Description of the entity.

        See Also
        --------
        Metadata.__init__
        """
        super().__init__(name, source, labels, embedded, created, updated)
        self.project = project
        self.version = version
        self.description = description


class DataitemMetadataDataitem(DataitemMetadata):
    """
    A class representing Dataitem dataitem metadata.
    """


class DataitemMetadataTable(DataitemMetadata):
    """
    A class representing Dataitem table metadata.
    """


class DataitemMetadataIceberg(DataitemMetadata):
    """
    A class representing Dataitem iceberg metadata.
    """
