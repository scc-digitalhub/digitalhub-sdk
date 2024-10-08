from __future__ import annotations

from digitalhub.entities._base.status.base import Status
from digitalhub.entities.artifact.crud import get_artifact
from digitalhub.entities.dataitem.crud import get_dataitem
from digitalhub.entities.entity_types import EntityTypes
from digitalhub.entities.model.crud import get_model
from digitalhub.entities.utils import parse_entity_key

ENTITY_FUNC = {
    EntityTypes.ARTIFACT.value: get_artifact,
    EntityTypes.DATAITEM.value: get_dataitem,
    EntityTypes.MODEL.value: get_model,
}


class RunStatus(Status):
    """
    Status class for run entities.
    """

    def __init__(
        self,
        state: str,
        message: str | None = None,
        outputs: list | None = None,
        results: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(state, message)
        self.outputs = outputs
        self.results = results

        self._any_setter(**kwargs)

    def get_results(self) -> dict:
        """
        Get results.

        Returns
        -------
        dict
            The results.
        """
        if not hasattr(self, "results") or self.results is None:
            return {}
        return self.results

    def get_outputs(self, as_key: bool = False, as_dict: bool = False) -> dict:
        """
        Get outputs.

        Parameters
        ----------
        as_key : bool
            If True, return outputs as keys.
        as_dict : bool
            If True, return outputs as dictionaries.

        Returns
        -------
        dict
            The outputs.
        """
        outputs = {}
        if not hasattr(self, "outputs") or self.outputs is None:
            return outputs

        for parameter, key in self.outputs.items():
            entity_type = self._get_entity_type(key)
            entity = ENTITY_FUNC[entity_type](key)
            if as_key:
                entity = entity.key
            if as_dict:
                entity = entity.to_dict()
            outputs[parameter] = entity

        return outputs

    @staticmethod
    def _get_entity_type(key: str) -> str:
        """
        Get entity type.

        Parameters
        ----------
        key : str
            The key of the entity.

        Returns
        -------
        str
            The entity type.
        """
        _, entity_type, _, _, _ = parse_entity_key(key)
        return entity_type

    def get_values(self, values_list: list) -> dict:
        """
        Get values.

        Parameters
        ----------
        values_list : list
            The values list to search in.

        Returns
        -------
        dict
            The values.
        """
        if not hasattr(self, "results") or self.results is None:
            return {}
        return {k: v for k, v in self.get_results().items() if k in values_list}
