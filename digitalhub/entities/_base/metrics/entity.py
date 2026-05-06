# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.metrics import MetricType, update_metrics, validate_metric_value
from digitalhub.entities._processors.processors import context_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.metrics.status import MetricsStatus


class MetricsEntity(ContextEntity):
    """
    Mixin class for entities with metrics.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.status: MetricsStatus

    @property
    def metrics(self) -> dict[str, MetricType]:
        """
        Get metrics from entity status.

        Returns
        -------
        dict[str, MetricType]
            Metrics dictionary.
        """
        if not self._has_metrics() or not self.status.metrics:
            return {}
        return self._read_metrics()

    def _has_metrics(self) -> bool:
        """
        Check if the entity has any metrics.

        Returns
        -------
        bool
            True if the entity has metrics, False otherwise.
        """
        return self.status.metrics is not None

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
        # Validate metric value
        validate_metric_value(value)

        # Set up metrics dict if it doesn't exist
        if not self._has_metrics():
            self.status.metrics = {}
            self.save(update=True)
            metrics = {}
        else:
            metrics = self._read_metrics()

        updated_metrics = self._update_metrics(metrics, key, value, overwrite, single_value)
        context_processor.update_metric(self.project, self.ENTITY_TYPE, self.id, key, updated_metrics[key])

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

        See also
        --------
        log_metric
        """
        for key, value in metrics.items():
            # For lists, use log_metric which handles appending correctly
            if isinstance(value, list):
                self._log_metric(key, value, overwrite)

            # For single values, check if we should append or create new
            else:
                if not overwrite and key in self.status.metrics:
                    self._log_metric(key, value)
                else:
                    self._log_metric(key, value, overwrite, single_value=True)

    def _read_metrics(self) -> dict[str, MetricType]:
        """
        Get model metrics from backend.

        Returns
        -------
        dict[str, MetricType]
            The metrics dictionary retrieved from the backend.
        """
        return context_processor.read_metrics(
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
    ) -> None:
        """
        Set model metrics.

        Parameters
        ----------
        metrics : dict[str, MetricType]
            Current metrics dictionary to update.
        key : str
            Key of the metric.
        value : MetricType
            Value of the metric.
        overwrite : bool
            If True, overwrite existing metric.
        single_value : bool
            If True, value is a single value.
        """
        return update_metrics(
            metrics,
            key,
            value,
            overwrite,
            single_value,
        )
