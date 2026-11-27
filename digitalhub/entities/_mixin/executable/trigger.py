# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._mixin.executable.base import ExecutableBaseMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities.trigger._base.entity import Trigger


class ExecutableTriggerMixin(ExecutableBaseMixin):
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
            Template of the runs the trigger creates. It is checked against
            the run spec of ``action``, like the parameters of ``run()``.
        **kwargs : dict
            Trigger construction parameters.

        Returns
        -------
        Trigger
            Created trigger.

        Raises
        ------
        EntityError
            If the action is not supported or the template is not a dictionary.
        TypeError
            If the template has parameters the run spec does not accept.
        ValueError
            If a template value has the wrong type.
        """
        return ContextEntityExecutableProcessor().create_trigger(
            self,
            action,
            kind,
            name,
            template=template,
            **kwargs,
        )

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
        return ContextEntityExecutableProcessor().get_executable_trigger(self, identifier)

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
        return ContextEntityExecutableProcessor().list_executable_triggers(
            self,
            q=q,
            name=name,
            kind=kind,
            user=user,
            created=created,
            updated=updated,
            versions=versions,
            task=task,
        )
