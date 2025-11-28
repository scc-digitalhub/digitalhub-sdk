# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod


class ParameterStrategy(ABC):
    """
    Abstract base class for parameter building strategies.

    Defines interface for parameter builders that handle specific
    operations or parameter types.
    """

    @abstractmethod
    def build(self, **kwargs) -> dict:
        """
        Build parameters for specific operation.

        Parameters
        ----------
        **kwargs : dict
            Raw parameters to transform.

        Returns
        -------
        dict
            Formatted parameters.
        """
        pass


class SearchParameterStrategy(ParameterStrategy):
    """
    Strategy for building Solr search parameters.

    Handles complex search filter construction including entity types,
    names, kinds, time ranges, descriptions, and labels.
    """

    def build(self, **kwargs) -> dict:
        """
        Build search parameters with Solr filters.

        Parameters
        ----------
        **kwargs : dict
            Raw search parameters including entity_types, name, kind,
            created, updated, description, labels, etc.

        Returns
        -------
        dict
            Formatted parameters with 'fq' (filter query) list.
        """
        fq = []

        # Entity types
        if (entity_types := kwargs.pop("entity_types", None)) is not None:
            entity_types = self._format_entity_types(entity_types)
            fq.append(f"type:({entity_types})")

        # Name
        if (name := kwargs.pop("name", None)) is not None:
            fq.append(f'metadata.name:"{name}"')

        # Kind
        if (kind := kwargs.pop("kind", None)) is not None:
            fq.append(f'kind:"{kind}"')

        # Time range
        created = kwargs.pop("created", None)
        updated = kwargs.pop("updated", None)
        created = created if created is not None else "*"
        updated = updated if updated is not None else "*"
        fq.append(f"metadata.updated:[{created} TO {updated}]")

        # Description
        if (description := kwargs.pop("description", None)) is not None:
            fq.append(f'metadata.description:"{description}"')

        # Labels
        if (labels := kwargs.pop("labels", None)) is not None:
            labels = self._format_labels(labels)
            fq.append(f"metadata.labels:({labels})")

        kwargs["fq"] = fq
        return kwargs

    @staticmethod
    def _format_entity_types(entity_types: list[str] | str) -> str:
        """
        Format entity types for Solr query.

        Parameters
        ----------
        entity_types : list[str] or str
            Entity type or types to format.

        Returns
        -------
        str
            Formatted entity types string.
        """
        if not isinstance(entity_types, list):
            entity_types = [entity_types]
        if len(entity_types) == 1:
            return entity_types[0]
        return " OR ".join(entity_types)

    @staticmethod
    def _format_labels(labels: list[str]) -> str:
        """
        Format labels for Solr query.

        Parameters
        ----------
        labels : list[str]
            Labels to format.

        Returns
        -------
        str
            Formatted labels string.
        """
        if len(labels) == 1:
            return labels[0]
        return " AND ".join(labels)


class ListParameterStrategy(ParameterStrategy):
    """
    Strategy for building list operation parameters.

    Handles filtering parameters for entity list operations including
    query, name, kind, user, state, timestamps, and relationships.
    """

    ALLOWED_PARAMS = [
        "q",
        "name",
        "kind",
        "user",
        "state",
        "created",
        "updated",
        "versions",
        "function",
        "workflow",
        "action",
        "task",
    ]

    def build(self, **kwargs) -> dict:
        """
        Build list operation parameters.

        Parameters
        ----------
        **kwargs : dict
            Raw list parameters.

        Returns
        -------
        dict
            Formatted parameters with allowed list filters.
        """
        # Extract only allowed parameters
        list_params = {k: kwargs.get(k, None) for k in self.ALLOWED_PARAMS}
        list_params = {k: v for k, v in list_params.items() if v is not None}

        # Remove from kwargs and return filtered params
        for k in self.ALLOWED_PARAMS:
            kwargs.pop(k, None)

        kwargs["list_params"] = list_params
        return kwargs
