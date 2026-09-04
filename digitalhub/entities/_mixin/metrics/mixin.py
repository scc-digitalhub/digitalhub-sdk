# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import ClassVar

from digitalhub.entities._commons.metrics import MetricType, update_metrics, validate_metric_value
from digitalhub.entities._processors.processors import metrics_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.metrics.status import MetricsStatus


class MetricsMixin:
    """Mixin for entities that expose metric logging and retrieval."""

    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str
    status: MetricsStatus

    def _init_metrics_state(self) -> None:
        self._entity_has_metrics: bool | None = None

    def _has_metrics(self) -> bool:
        """
        Verify that the entity has metrics.

        Raises
        ------
        ValueError
            If the entity does not have metrics.
        """
        if self._entity_has_metrics is True:
            return True
        self._entity_has_metrics = bool(self._read_metrics()) or bool(self.status.metrics)
        return self._entity_has_metrics

    @property
    def metrics(self) -> dict[str, MetricType]:
        """
        Get metrics from entity status.

        Returns
        -------
        dict[str, MetricType]
            Metrics dictionary.
        """
        if not self._has_metrics():
            return {}
        elif not bool(self.status.metrics):
            return self._read_metrics()
        return self.status.metrics

    def _log_metric(
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
        """
        validate_metric_value(value)

        if not self._has_metrics():
            self.status.metrics = {}
            self.save(update=True)
            metrics = {}
        else:
            metrics = self._read_metrics()

        updated_metrics = self._update_metrics(metrics, key, value, overwrite, single_value)
        metrics_processor.update_metric(self.project, self.ENTITY_TYPE, self.id, key, updated_metrics[key])
        self._entity_has_metrics = True

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

        Examples
        --------
        Log a new value in a list
        >>> entity.log_metric("loss", 0.002)

        Append a new value in a list
        >>> entity.log_metric("loss", 0.0019)

        Log a list of values and append them to existing metric:
        >>> entity.log_metric(
        ...     "loss",
        ...     [
        ...         0.0018,
        ...         0.0015,
        ...     ],
        ... )

        Log a single value (not represented as list):
        >>> entity.log_metric(
        ...     "accuracy",
        ...     0.9,
        ...     single_value=True,
        ... )

        Log a list of values and overwrite existing metric:
        >>> entity.log_metric(
        ...     "accuracy",
        ...     [0.8, 0.9],
        ...     overwrite=True,
        ... )
        """
        self._log_metric(key, value, overwrite, single_value)

    def log_metrics(
        self,
        metrics: dict[str, MetricType],
        overwrite: bool = False,
    ) -> None:
        """
        Log metrics into entity status. If a metric is a list, it will be logged as a list.
        Otherwise, it will be logged as a single value.

        Parameters
        ----------
        metrics : dict[str, MetricType]
            Dict of metrics to log.
        overwrite : bool
            If True, overwrite existing metrics.

        Examples
        --------
        Log multiple metrics at once
        >>> entity.log_metrics(
        ...     {
        ...         "loss": 0.002,
        ...         "accuracy": 0.95,
        ...     }
        ... )

        Log metrics with lists and single values
        >>> entity.log_metrics(
        ...     {
        ...         "loss": [
        ...             0.1,
        ...             0.05,
        ...         ],
        ...         "epoch": 10,
        ...     }
        ... )

        Append to existing metrics (default behavior)
        >>> entity.log_metrics(
        ...     {
        ...         "loss": 0.001,
        ...         "accuracy": 0.96,
        ...     }
        ... )  # Appends to existing

        Overwrite existing metrics
        >>> entity.log_metrics(
        ...     {
        ...         "loss": 0.0005,
        ...         "accuracy": 0.98,
        ...     },
        ...     overwrite=True,
        ... )

        See Also
        --------
        log_metric
        """
        stored_metrics = self._read_metrics()
        for key, value in metrics.items():
            if isinstance(value, list):
                self._log_metric(key, value, overwrite)
                continue

            if not overwrite and self._has_metrics() and key in stored_metrics:
                self._log_metric(key, value)
                continue

            self._log_metric(key, value, overwrite, single_value=True)

    def _read_metrics(self) -> dict[str, MetricType]:
        """
        Get model metrics from backend.
        """
        return metrics_processor.read_metrics(
            project=self.project,
            entity_type=self.ENTITY_TYPE,
            entity_id=self.id,
        )

    def _update_metrics(
        self,
        metrics: dict[str, MetricType],
        key: str,
        value: MetricType,
        overwrite: bool,
        single_value: bool,
    ) -> dict[str, MetricType]:
        """
        Set model metrics.
        """
        return update_metrics(metrics, key, value, overwrite, single_value)
