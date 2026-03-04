# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class FactoryEnum(Enum):
    """
    Enumeration for factory.
    """

    RGX_RUNTIMES = r"digitalhub_runtime_.*"
    REG_ENTITIES = "digitalhub.entities.builders"
    REG_ENTITIES_VAR = "entity_builders"
    REG_RUNTIME_VAR = "runtime_builders"


class BuilderMethodsEnum(Enum):
    """
    Enumeration for builder methods.
    """

    BUILD_SPEC = "build_spec"
    BUILD_METADATA = "build_metadata"
    BUILD_STATUS = "build_status"
    GET_ENTITY_TYPE = "get_entity_type"
    GET_EXECUTABLE_KIND = "get_executable_kind"
    GET_ACTION_FROM_TASK_KIND = "get_action_from_task_kind"
    GET_TASK_KIND_FROM_ACTION = "get_task_kind_from_action"
    GET_RUN_KIND_FROM_ACTION = "get_run_kind_from_action"
    GET_ALL_KINDS = "get_all_kinds"
    GET_SPEC_VALIDATOR = "get_spec_validator"
