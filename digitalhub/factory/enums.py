# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class FactoryEnum(Enum):
    """
    Enumeration for factory.
    """

    RUNTIMES_ENTRY_POINT_GROUP = "digitalhub.runtimes"
    REG_ENTITIES = "digitalhub.entities.builders"
    REG_ENTITY_PLUGINS_VAR = "entity_plugins"
    REG_CRUD_PLUGINS_VAR = "crud_plugins"
    REG_GENERIC_ENTITIES_VAR = "generic_entity_builders"


class BuilderMethodsEnum(Enum):
    """
    Enumeration for builder methods.
    """

    BUILD_SPEC = "build_spec"
    BUILD_STATUS = "build_status"
    GET_ENTITY_TYPE = "get_entity_type"
    GET_EXECUTABLE_KIND = "get_executable_kind"
    GET_ACTION_FROM_TASK_KIND = "get_action_from_task_kind"
    GET_TASK_KIND_FROM_ACTION = "get_task_kind_from_action"
    GET_RUN_KIND_FROM_ACTION = "get_run_kind_from_action"
