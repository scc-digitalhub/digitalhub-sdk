# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Compatibility exports for infrastructure models.

Runtime packages should import these models from
``digitalhub.entities._commons.models``.
"""

from digitalhub.entities._frameworks.k8s.models import (
    RESOURCE_REGEX,
    CorePort,
    CorePullPolicy,
    CoreServiceType,
    Env,
    K8s,
    Resource,
    SharedVolumeSpec,
    SpecEmptyDir,
    SpecEphemeral,
    SpecPVC,
    Volume,
    VolumeType,
)

__all__ = [
    "RESOURCE_REGEX",
    "CorePort",
    "CorePullPolicy",
    "CoreServiceType",
    "Env",
    "K8s",
    "Resource",
    "SharedVolumeSpec",
    "SpecEmptyDir",
    "SpecEphemeral",
    "SpecPVC",
    "Volume",
    "VolumeType",
]
