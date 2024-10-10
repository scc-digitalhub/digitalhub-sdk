from __future__ import annotations

from digitalhub.entities._base.spec.base import Spec, SpecParams


class SecretSpec(Spec):
    """
    Secret specifications.
    """

    def __init__(self, path: str | None = None, provider: str | None = None, **kwargs) -> None:
        """
        Constructor.

        Parameters
        ----------
        path : str
            Path to the secret.
        provider : str
            Provider of the secret.
        """
        self.path = path
        self.provider = provider


class SecretParams(SpecParams):
    """
    Secret parameters.
    """

    path: str = None
    """Path to the secret."""

    provider: str = None
    """Provider of the secret."""
