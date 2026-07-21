# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class EntityTypes(Enum):
    """
    Entity types.
    """

    ARTIFACT = "artifact"
    DATAITEM = "dataitem"
    EXTENSION = "extension"
    FUNCTION = "function"
    CONTAINERIMAGE = "containerimage"
    LOG = "log"
    MODEL = "model"
    PROJECT = "project"
    RUN = "run"
    SECRET = "secret"
    TASK = "task"
    TRIGGER = "trigger"
    WORKFLOW = "workflow"


class Relationship(Enum):
    """
    Relationship enumeration.
    """

    CONSUMES = "consumes"
    PRODUCEDBY = "produced_by"
    RUN_OF = "run_of"
    STEP_OF = "step_of"
    PART_OF = "part_of"


class State(Enum):
    """
    State enumeration.
    """

    BUILT = "BUILT"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    CREATED = "CREATED"
    CREATING = "CREATING"
    DELETED = "DELETED"
    DELETING = "DELETING"
    ERROR = "ERROR"
    FSM_ERROR = "FSM_ERROR"
    IDLE = "IDLE"
    NONE = "NONE"
    ONLINE = "ONLINE"
    PENDING = "PENDING"
    READY = "READY"
    RESUME = "RESUME"
    RUN_ERROR = "RUN_ERROR"
    RUNNING = "RUNNING"
    STOP = "STOP"
    STOPPED = "STOPPED"
    SUCCESS = "SUCCESS"
    UNKNOWN = "UNKNOWN"
    UPLOADING = "UPLOADING"


class EntityKinds(Enum):
    """
    Entity kinds.
    """

    GENERIC = "_generic"
    ARTIFACT_ARTIFACT = "artifact"
    DATAITEM_CROISSANT = "croissant"
    DATAITEM_DATAITEM = "dataitem"
    DATAITEM_TABLE = "table"
    EXTENSION_EXTENSION = "extension"
    CONTAINERIMAGE_CONTAINERIMAGE = "container-image"
    LOG_LOG = "log"
    MODEL_HUGGINGFACE = "huggingface"
    MODEL_MLFLOW = "mlflow"
    MODEL_MODEL = "model"
    MODEL_SKLEARN = "sklearn"
    MODEL_TVM_IR = "tvm-ir"
    MODEL_TVM_SO = "tvm-so"
    PROJECT_PROJECT = "project"
    SECRET_SECRET = "secret"
    TRIGGER_AUTOML = "automl"
    TRIGGER_LIFECYCLE = "lifecycle"
    TRIGGER_SCHEDULER = "scheduler"
