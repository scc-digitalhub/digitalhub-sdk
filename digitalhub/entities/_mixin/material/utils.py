# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.utils.logger.logger import get_logger

logger = get_logger(__name__)


def log_warning(
    requested_kind: str | None,
    log_kind: str,
    entity_type: str,
) -> None:
    """
    Log a warning if the requested kind is different from the log kind.

    Parameters
    ----------
    requested_kind : str | None
        The kind requested by the user.
    log_kind : str
        The kind used for logging.
    entity_type : str
        The type of the entity being logged.
    """
    if requested_kind is not None:
        if requested_kind != log_kind:
            raise ValueError(
                f"Detected 'kind' in kwargs: kind='{requested_kind}'. This method is intended for logging {entity_type} of kind '{log_kind}'. Try to use the method 'log_{requested_kind}' (if it exists)."
            )
        logger.warning("Detected 'kind' in kwargs. The kind parameter is not necessary and will be ignored.")
