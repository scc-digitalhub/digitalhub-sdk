# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass

from digitalhub.stores.client.common.enums import BackendOp, HttpMethod, OpsType
from digitalhub.stores.client.compiler.params.profile import ParamsProfile


@dataclass(frozen=True, slots=True)
class OpsSpec:
    """Compilation rules for one semantic backend operation."""

    method: HttpMethod
    operation_type: OpsType
    route_operation: BackendOp
    params_profile: ParamsProfile | None = None


OPERATION_SPECS: dict[BackendOp, OpsSpec] = {
    BackendOp.CREATE: OpsSpec(HttpMethod.POST, OpsType.ENTITY_CREATE, BackendOp.CREATE),
    BackendOp.READ: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_READ,
        BackendOp.READ,
        params_profile=ParamsProfile.READ,
    ),
    BackendOp.READ_ALL_VERSIONS: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_LIST,
        route_operation=BackendOp.LIST,
        params_profile=ParamsProfile.READ_ALL_VERSIONS,
    ),
    BackendOp.UPDATE: OpsSpec(HttpMethod.PUT, OpsType.ENTITY_UPDATE, BackendOp.UPDATE),
    BackendOp.DELETE: OpsSpec(
        HttpMethod.DELETE,
        OpsType.ENTITY_DELETE,
        BackendOp.DELETE,
        params_profile=ParamsProfile.DELETE,
    ),
    BackendOp.DELETE_ALL_VERSIONS: OpsSpec(
        HttpMethod.DELETE,
        OpsType.ENTITY_DELETE,
        BackendOp.DELETE_ALL_VERSIONS,
        params_profile=ParamsProfile.DELETE_ALL_VERSIONS,
    ),
    BackendOp.LIST: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_LIST,
        BackendOp.LIST,
        params_profile=ParamsProfile.LIST,
    ),
    BackendOp.LIST_FIRST: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_LIST,
        BackendOp.LIST,
        params_profile=ParamsProfile.LIST,
    ),
    BackendOp.SEARCH: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_SEARCH,
        BackendOp.SEARCH,
        params_profile=ParamsProfile.SEARCH,
    ),
    BackendOp.STOP: OpsSpec(
        HttpMethod.POST,
        OpsType.ENTITY_CREATE,
        BackendOp.STOP,
        params_profile=ParamsProfile.STOP_RESUME,
    ),
    BackendOp.RESUME: OpsSpec(
        HttpMethod.POST,
        OpsType.ENTITY_CREATE,
        BackendOp.RESUME,
        params_profile=ParamsProfile.STOP_RESUME,
    ),
    BackendOp.SHARE: OpsSpec(
        HttpMethod.POST,
        OpsType.ENTITY_CREATE,
        BackendOp.SHARE,
        params_profile=ParamsProfile.SHARE,
    ),
    BackendOp.SHARE_READ: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_READ,
        route_operation=BackendOp.SHARE,
    ),
    BackendOp.UNSHARE: OpsSpec(
        HttpMethod.DELETE,
        OpsType.ENTITY_DELETE,
        route_operation=BackendOp.SHARE,
        params_profile=ParamsProfile.SHARE,
    ),
    BackendOp.DATA_READ: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_READ,
        route_operation=BackendOp.DATA,
    ),
    BackendOp.DATA_UPDATE: OpsSpec(
        HttpMethod.PUT,
        OpsType.ENTITY_UPDATE,
        route_operation=BackendOp.DATA,
    ),
    BackendOp.FILES_READ: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_READ,
        route_operation=BackendOp.FILES,
    ),
    BackendOp.FILES_UPDATE: OpsSpec(
        HttpMethod.PUT,
        OpsType.ENTITY_UPDATE,
        route_operation=BackendOp.FILES,
    ),
    BackendOp.LOGS_READ: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_READ,
        route_operation=BackendOp.LOGS,
        params_profile=ParamsProfile.LOGS,
    ),
    BackendOp.METRICS_READ: OpsSpec(
        HttpMethod.GET,
        OpsType.ENTITY_READ,
        route_operation=BackendOp.METRICS,
        params_profile=ParamsProfile.METRICS,
    ),
    BackendOp.METRICS_UPDATE: OpsSpec(
        HttpMethod.PUT,
        OpsType.ENTITY_UPDATE,
        route_operation=BackendOp.METRICS,
        params_profile=ParamsProfile.METRICS,
    ),
}


def get_operation_spec(operation: BackendOp) -> OpsSpec:
    """Return compilation rules for a backend operation."""
    try:
        return OPERATION_SPECS[operation]
    except KeyError as error:
        raise ValueError(f"Unsupported backend operation '{operation}'.") from error
