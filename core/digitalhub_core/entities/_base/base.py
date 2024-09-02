from __future__ import annotations

from digitalhub_core.utils.generic_utils import dict_to_json


class ModelObj:
    """
    Base class for all entities.
    It implements to_dict abd to_json method to represent
    the object as a dictionary/json and an any_setter method to
    set generic attributes coming from a constructor.
    """

    def to_dict(self) -> dict:
        """
        Return object as dict with all non private keys.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        obj = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_") and value is not None:
                if hasattr(value, "to_dict"):
                    sub_dict = value.to_dict()
                    if sub_dict:
                        obj[key] = sub_dict
                else:
                    obj[key] = value
        return obj

    def to_json(self) -> str:
        """
        Return object as json with all non private keys.

        Returns
        -------
        str
            A json string containing the attributes of the entity instance.
        """
        return dict_to_json(self.to_dict())

    def _any_setter(self, **kwargs) -> None:
        """
        Set any attribute of the object.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to be set as attributes.

        Returns
        -------
        None
        """
        for k, v in kwargs.items():
            if k not in self.__dict__:
                setattr(self, k, v)

    def _get_private_attrs(self) -> dict:
        """
        Return all private attributes of the object.

        Returns
        -------
        dict
            A dictionary containing the private attributes of the entity instance.
        """
        return {k: v for k, v in self.__dict__.items() if k.startswith("_")}

    def __repr__(self) -> str:
        """
        Return string representation of the entity object.

        Returns
        -------
        str
            A string representing the entity instance.
        """
        return str(self.to_dict())
