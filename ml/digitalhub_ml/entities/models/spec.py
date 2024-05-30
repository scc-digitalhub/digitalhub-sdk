"""
Model base specification module.
"""
from __future__ import annotations

from digitalhub_core.entities._base.spec import Spec, SpecParams


class ModelSpec(Spec):
    """
    Model specifications.
    """

    def __init__(
        self,
        path: str | None = None,
        framework: str | None = None,
        algorithm: str | None = None,
        **kwargs,
    ) -> None:
        """
        Constructor.
        """

        self.path = path
        self.framework = framework
        self.algorithm = algorithm

        self._any_setter(**kwargs)


class ModelParams(SpecParams):
    """
    Model parameters.
    """

    path: str
    """Path to the model."""

    framework: str = None
    """Model framework (e.g. 'pytorch')."""

    algorithm: str = None
    """Model algorithm (e.g. 'resnet')."""


class ModelSpecModel(ModelSpec):
    """
    Model specifications.
    """

    def __init__(
        self,
        base_model: str | None = None,
        parameters: dict | None = None,
        metrics: dict | None = None,
        **kwargs,
    ) -> None:
        """
        Constructor.
        """
        self.base_model = base_model
        self.parameters = parameters
        self.metrics = metrics

        self._any_setter(**kwargs)


class ModelParamsModel(ModelParams):
    """
    Model parameters.
    """

    base_model: str = None
    """Base model."""

    parameters: dict = None
    """Model parameters."""

    metrics: dict = None
    """Model metrics."""
