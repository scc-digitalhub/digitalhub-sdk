# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

RESOURCE_REGEX = r"[\d]+|^([0-9])+([a-zA-Z])+$"


class VolumeType(Enum):
    """Volume type."""

    PERSISTENT_VOLUME_CLAIM = "persistent_volume_claim"
    EMPTY_DIR = "empty_dir"
    EPHEMERAL = "ephemeral"
    SHARED_VOLUME = "shared_volume"


class SpecEmptyDir(BaseModel):
    """Spec empty dir model."""

    size_limit: str | None = None
    medium: str | None = None


class SpecPVC(BaseModel):
    """Spec PVC model."""

    size: str | None = None


class SpecEphemeral(BaseModel):
    """Ephemeral volume model."""

    size: str | None = None


class SharedVolumeSpec(BaseModel):
    """Shared volume spec model."""

    size: str | None = None


class Volume(BaseModel):
    """Volume model."""

    model_config = ConfigDict(use_enum_values=True)

    volume_type: VolumeType
    name: str
    mount_path: str
    spec: SpecEmptyDir | SpecPVC | SpecEphemeral | SharedVolumeSpec | None = None


class Resource(BaseModel):
    """Resource model."""

    cpu: Annotated[str, Field(pattern=RESOURCE_REGEX)] | int | None = None
    mem: Annotated[str, Field(pattern=RESOURCE_REGEX)] | int | None = None
    gpu: Annotated[str, Field(pattern=RESOURCE_REGEX)] | int | None = None
    disk: Annotated[str, Field(pattern=RESOURCE_REGEX)] | int | None = None


class Env(BaseModel):
    """Environment variable model."""

    name: str
    value: str


class K8s(BaseModel):
    """Kubernetes execution model shared by Task and Run specs."""

    volumes: list[Volume] | None = None
    resources: Resource | None = None
    envs: list[Env] | None = None
    secrets: list[str] | None = None
    profile: str | None = None


class CorePort(BaseModel):
    """Port mapper model."""

    port: int
    target_port: int


class CoreServiceType(Enum):
    """Core service type."""

    EXTERNAL_NAME = "ExternalName"
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


class CorePullPolicy(Enum):
    """Core image pull policy."""

    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"
