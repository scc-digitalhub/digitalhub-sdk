"""
RunStatusData module.
"""
from __future__ import annotations

from digitalhub_core.entities.runs.status import ENTITY_FUNC, RunStatus
from digitalhub_data.entities.dataitems.crud import get_dataitem_from_key

ENTITY_FUNC["dataitems"] = get_dataitem_from_key


class RunStatusData(RunStatus):
    """
    A class representing a run status.
    """
