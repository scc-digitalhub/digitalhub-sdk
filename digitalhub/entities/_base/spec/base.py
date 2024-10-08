from __future__ import annotations

from pydantic import BaseModel

from digitalhub.entities._base.base import ModelObj


class Spec(ModelObj):
    """
    A class representing the specification of an entity.
    Specification is a collection of information about an entity
    thought to be immutable by the user.
    """

    @classmethod
    def from_dict(cls, obj: dict) -> Spec:
        """
        Return entity specification object from dictionary.

        Parameters
        ----------
        obj : dict
            A dictionary containing the attributes of the entity specification.

        Returns
        -------
        EntitySpec
            An entity specification object.
        """
        return cls(**obj)


class SpecParams(BaseModel, extra="ignore"):
    """
    A class representing the parameters of an entity.
    This base class is used to define the parameters of an entity
    specification and is used to validate the parameters passed
    to the constructor.
    """


class MaterialSpec(Spec):
    """
    Material specification class.
    """

    def __init__(self, path: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = path


class MaterialParams(SpecParams):
    """
    Material parameters class.
    """

    path: str
    """Target path to file(s)"""
