# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import ClassVar

from digitalhub.stores.client.compiler.params.state import ParameterState


class SearchParameterStrategy:
    """
    Strategy for building Solr search parameters.
    """

    def build(self, state: ParameterState) -> ParameterState:
        """
        Build search parameters with Solr filters.
        """
        fq = []

        # Entity types
        entity_types, state = state.pop("entity_types", None)
        if entity_types is not None:
            entity_types = self._format_entity_types(entity_types)
            fq.append(f"type:({entity_types})")

        # Name
        name, state = state.pop("name", None)
        if name is not None:
            fq.append(f'metadata.name:"{name}"')

        # Kind
        kind, state = state.pop("kind", None)
        if kind is not None:
            fq.append(f'kind:"{kind}"')

        # Time range
        created, state = state.pop("created", None)
        updated, state = state.pop("updated", None)
        created = created if created is not None else "*"
        updated = updated if updated is not None else "*"
        fq.append(f"metadata.updated:[{created} TO {updated}]")

        # Description
        description, state = state.pop("description", None)
        if description is not None:
            fq.append(f'metadata.description:"{description}"')

        # Labels
        labels, state = state.pop("labels", None)
        if labels is not None:
            labels = self._format_labels(labels)
            fq.append(f"metadata.labels:({labels})")

        return state.with_value("fq", fq)

    @staticmethod
    def _format_entity_types(entity_types: list[str] | str) -> str:
        """
        Format entity types for Solr query.
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
        """
        if len(labels) == 1:
            return labels[0]
        return " AND ".join(labels)


class ListParameterStrategy:
    """
    Strategy for building list operation parameters.
    """

    ALLOWED_PARAMS: ClassVar[list[str]] = [
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

    def build(self, state: ParameterState) -> ParameterState:
        """
        Build list operation parameters.
        """
        # Extract only allowed parameters
        list_params = {k: state.values.get(k, None) for k in self.ALLOWED_PARAMS}
        list_params = {k: v for k, v in list_params.items() if v is not None}

        # Remove extracted filters from the state values.
        for key in self.ALLOWED_PARAMS:
            _, state = state.pop(key, None)

        return state.with_value("list_params", list_params)
