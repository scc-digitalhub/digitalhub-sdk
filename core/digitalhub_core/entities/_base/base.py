from __future__ import annotations


class ModelObj:
    """
    Base class for all entities. It implements the to_dict method to represent
    the object as a dictionary and a _any_setter method to set attributes
    coming from a constructor.
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

    def __repr__(self) -> str:
        """
        Return string representation of the entity object.

        Returns
        -------
        str
            A string representing the entity instance.
        """
        return str(self.to_dict())
