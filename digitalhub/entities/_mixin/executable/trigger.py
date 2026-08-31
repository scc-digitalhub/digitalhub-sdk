# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._mixin.executable.base import ExecutableBaseMixin
from digitalhub.entities.trigger.crud import list_triggers
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import SpecValidator
    from digitalhub.entities.task._base.entity import Task
    from digitalhub.entities.trigger._base.entity import Trigger


class ExecutableTriggerMixin(ExecutableBaseMixin):
    if typing.TYPE_CHECKING:

        def _get_or_create_task(self, action: str) -> Task: ...

    def trigger(
        self,
        action: str,
        kind: str,
        name: str,
        template: dict | None = None,
        **kwargs,
    ) -> Trigger:
        """Create and persist a trigger for an executable action.

        Parameters
        ----------
        action : str
            Executable action invoked by the trigger.
        kind : str
            Trigger kind.
        name : str
            Trigger name.
        template : dict, optional
            Run template associated with the trigger.
        **kwargs : dict
            Trigger construction parameters.

        Returns
        -------
        Trigger
            Created trigger.

        Raises
        ------
        EntityError
            If the template is invalid or the action is not supported.
        """
        task = self._get_or_create_task(action)
        task_string = task._get_task_string()
        exec_string = self._get_executable_string()

        run_kind = entity_factory.get_run_kind_from_action(self.kind, action)
        run_validator: SpecValidator = entity_factory.get_spec_validator(run_kind)

        kwargs["project"] = self.project
        kwargs["kind"] = kind
        kwargs["name"] = name

        if template is None:
            template = {}
        if not isinstance(template, dict):
            raise EntityError("Template must be a dictionary")

        template["task"] = task_string
        template[self.ENTITY_TYPE] = exec_string
        template = run_validator(**template).to_dict()

        kwargs[self.ENTITY_TYPE] = exec_string
        kwargs["task"] = task_string
        kwargs["template"] = template

        trigger: Trigger = entity_factory.build_entity_from_params(**kwargs)
        trigger.save()
        return trigger

    def get_trigger(self, identifier: str) -> Trigger:
        """Get a trigger belonging to the executable.

        Parameters
        ----------
        identifier : str
            Trigger ID or key.

        Returns
        -------
        Trigger
            Matching trigger.

        Raises
        ------
        EntityError
            If the trigger does not exist or belongs to another executable.
        """
        entities = self._list_triggers()
        for entity in entities:
            if getattr(entity.spec, self.ENTITY_TYPE) == self._get_executable_string():
                if entity.id == identifier:
                    return entity
                if entity.key == identifier:
                    return entity
        raise EntityError(f"Trigger '{identifier}' does not exist or does not belong to this executable.")

    def list_triggers(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        versions: str | None = None,
        task: str | None = None,
    ) -> list[Trigger]:
        """List triggers associated with the executable.

        Parameters
        ----------
        q : str, optional
            Free-text query.
        name : str, optional
            Trigger name filter.
        kind : str, optional
            Trigger kind filter.
        user : str, optional
            Trigger owner filter.
        created : str, optional
            Creation date filter.
        updated : str, optional
            Update date filter.
        versions : str, optional
            Version selection filter.
        task : str, optional
            Task reference filter.

        Returns
        -------
        list[Trigger]
            Triggers matching the filters.
        """
        return self._list_triggers(
            q=q,
            name=name,
            kind=kind,
            user=user,
            created=created,
            updated=updated,
            versions=versions,
            task=task,
        )

    def _list_triggers(self, **kwargs) -> list[Trigger]:
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        return list_triggers(self.project, **kwargs)
