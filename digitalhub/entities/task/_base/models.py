# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

RESOURCE_REGEX = r"[\d]+|^([0-9])+([a-zA-Z])+$"


class VolumeType(Enum):
    """
    Volume type.
    """

    PERSISTENT_VOLUME_CLAIM = "persistent_volume_claim"
    EMPTY_DIR = "empty_dir"
    EPHEMERAL = "ephemeral"
    SHARED_VOLUME = "shared_volume"


class SpecEmptyDir(BaseModel):
    """
    Spec empty dir model.
    """

    size_limit: str | None = None

    medium: str | None = None


class SpecPVC(BaseModel):
    """
    Spec PVC model.
    """

    size: str | None = None


class SpecEphemeral(BaseModel):
    """
    Ephemeral volume model.
    """

    size: str | None = None


class SharedVolumeSpec(BaseModel):
    """
    Shared volume spec model.
    """

    size: str | None = None


class Volume(BaseModel):
    """
    Volume model.
    """

    model_config = ConfigDict(use_enum_values=True)

    volume_type: VolumeType
    """Volume type."""

    name: str
    """Volume name."""

    mount_path: str
    """Volume mount path inside the container."""

    spec: SpecEmptyDir | SpecPVC | SpecEphemeral | SharedVolumeSpec | None = None
    """Volume spec."""


class Resource(BaseModel):
    """
    Resource model.
    """

    cpu: Annotated[str, Field(pattern=RESOURCE_REGEX)] | int | None = None
    """CPU resource model."""

    mem: Annotated[str, Field(pattern=RESOURCE_REGEX)] | int | None = None
    """Memory resource model."""

    gpu: Annotated[str, Field(pattern=RESOURCE_REGEX)] | int | None = None
    """GPU resource model."""


class Env(BaseModel):
    """
    Env variable model.
    """

    name: str
    """Env variable name."""

    value: str
    """Env variable value."""


class K8s(BaseModel):
    """
    Kubernetes resource model.
    """

    volumes: list[Volume] | None = None
    """List of volumes."""

    resources: Resource | None = None
    """Resources restrictions."""

    envs: list[Env] | None = None
    """Env variables."""

    secrets: list[str] | None = None
    """List of secret names."""

    profile: str | None = None
    """Profile template."""


class CorePort(BaseModel):
    """
    Port mapper model.
    """

    port: int
    target_port: int


class CoreServiceType(Enum):
    """
    CoreServiceType enum.
    """

    EXTERNAL_NAME = "ExternalName"
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


class CorePullPolicy(Enum):
    """
    CorePullPolicy enum.
    """

    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"
