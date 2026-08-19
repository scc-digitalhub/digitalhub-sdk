# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations


class ContextEntitySecretProcessor:
    def read_secret_data(
        self,
        project: str,
        entity_type: str,
        **kwargs,
    ) -> dict:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.DATA.value,
            project=context.name,
            entity_type=entity_type,
        )
        return context.client.read_object(api, **kwargs)

    def update_secret_data(
        self,
        project: str,
        entity_type: str,
        data: dict,
        **kwargs,
    ) -> None:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.DATA.value,
            project=context.name,
            entity_type=entity_type,
        )
        context.client.update_object(api, data, **kwargs)
