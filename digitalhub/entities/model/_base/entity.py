from __future__ import annotations

import typing

from digitalhub.entities._base.material.entity import MaterialEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.metrics import MetricType, set_metrics, validate_metric_value
from digitalhub.entities._processors.context import context_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.model._base.spec import ModelSpec
    from digitalhub.entities.model._base.status import ModelStatus


class Model(MaterialEntity):
    """
    A class representing a model.
    """

    ENTITY_TYPE = EntityTypes.MODEL.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: ModelSpec,
        status: ModelStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)
        self.spec: ModelSpec
        self.status: ModelStatus

    def save(self, update: bool = False) -> Model:
        """
        Save entity into backend.

        Parameters
        ----------
        update : bool
            Flag to indicate update.

        Returns
        -------
        Model
            Entity saved.
        """
        obj: Model = super().save(update)
        obj._get_metrics()
        return obj

    def log_metric(
        self,
        key: str,
        value: MetricType,
        overwrite: bool = False,
        single_value: bool = False,
    ) -> None:
        """
        Log metric into entity status.
        A metric is named by a key and value (single number or list of numbers).
        The metric by default is put in a list or appended to an existing list.
        If single_value is True, the value will be a single number.

        Parameters
        ----------
        key : str
            Key of the metric.
        value : MetricType
            Value of the metric.
        overwrite : bool
            If True, overwrite existing metric.
        single_value : bool
            If True, value is a single value.

        Returns
        -------
        None

        Examples
        --------
        Log a new value in a list
        >>> entity.log_metric("loss", 0.002)

        Append a new value in a list
        >>> entity.log_metric("loss", 0.0019)

        Log a list of values and append them to existing metric:
        >>> entity.log_metric("loss", [0.0018, 0.0015])

        Log a single value (not represented as list):
        >>> entity.log_metric("accuracy", 0.9, single_value=True)

        Log a list of values and overwrite existing metric:
        >>> entity.log_metric("accuracy", [0.8, 0.9], overwrite=True)
        """
        self._set_metrics(key, value, overwrite, single_value)
        context_processor.update_metric(self.project, self.ENTITY_TYPE, self.id, key, self.status.metrics[key])

    ##############################
    # Helper methods
    ##############################

    def _get_metrics(self) -> None:
        """
        Get model metrics from backend.

        Returns
        -------
        None
        """
        self.status.metrics = context_processor.read_metrics(
            project=self.project,
            entity_type=self.ENTITY_TYPE,
            entity_id=self.id,
        )

    def _set_metrics(
        self,
        key: str,
        value: MetricType,
        overwrite: bool,
        single_value: bool,
    ) -> None:
        """
        Set model metrics.

        Parameters
        ----------
        key : str
            Key of the metric.
        value : MetricType
            Value of the metric.
        overwrite : bool
            If True, overwrite existing metric.
        single_value : bool
            If True, value is a single value.

        Returns
        -------
        None
        """
        value = validate_metric_value(value)
        self.status.metrics = set_metrics(
            self.status.metrics,
            key,
            value,
            overwrite,
            single_value,
        )
