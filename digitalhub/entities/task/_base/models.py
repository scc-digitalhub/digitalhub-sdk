# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


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

    size_limit: Optional[str] = None

    medium: Optional[str] = None


class SpecPVC(BaseModel):
    """
    Spec PVC model.
    """

    size: Optional[str] = None


class SpecEphemeral(BaseModel):
    """
    Ephemeral volume model.
    """

    size: Optional[str] = None


class SharedVolumeSpec(BaseModel):
    """
    Shared volume spec model.
    """

    size: Optional[str] = None


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

    spec: Optional[Union[SpecEmptyDir, SpecPVC, SpecEphemeral, SharedVolumeSpec]] = None
    """Volume spec."""


class Resource(BaseModel):
    """
    Resource model.
    """

    cpu: Optional[str] = Field(default=None, pattern=r"[\d]+|^([0-9])+([a-zA-Z])+$")
    """CPU resource model."""

    mem: Optional[str] = Field(default=None, pattern=r"[\d]+|^([0-9])+([a-zA-Z])+$")
    """Memory resource model."""

    gpu: Optional[str] = Field(default=None, pattern=r"[\d]+|^([0-9])+([a-zA-Z])+$")
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

    volumes: Optional[list[Volume]] = None
    """List of volumes."""

    resources: Optional[Resource] = None
    """Resources restrictions."""

    envs: Optional[list[Env]] = None
    """Env variables."""

    secrets: Optional[list[str]] = None
    """List of secret names."""

    profile: Optional[str] = None
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
