# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._commons.utils import build_log_name_from_source
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import SourcesOrListOfSources

logger = get_logger(__name__)


def kind_warning(
    requested_kind: str | None,
    set_kind: str,
    entity_type: str,
) -> None:
    """
    Log a warning if the requested kind is different from the set kind.

    Parameters
    ----------
    requested_kind : str | None
        The kind requested by the user.
    set_kind : str
        The kind that is set for the entity.
    entity_type : str
        The type of the entity being logged.
    """
    if requested_kind is not None:
        if requested_kind != set_kind:
            raise ValueError(
                f"Detected 'kind' in kwargs: kind='{requested_kind}'. This method is intended for logging {entity_type} of kind '{set_kind}'. Try to use the method '<log/register>_{requested_kind}' (if it exists)."
            )
        logger.warning("Detected 'kind' in kwargs. The kind parameter is not necessary and will be ignored.")


def name_warning(inferred_name: str, entity_kind: str) -> None:
    """
    Log a warning when an entity name is inferred from its source.

    Parameters
    ----------
    inferred_name : str
        The name inferred from the source path.
    entity_kind : str
        The kind of entity for which the name was inferred.
    """
    logger.warning(f"Name not provided for '{entity_kind}'. Inferred name: '{inferred_name}'.")


def build_register_name(
    name: str | None,
    source: SourcesOrListOfSources,
    entity_type: str,
    entity_kind: str,
) -> str:
    """
    Build an entity name from a source and warn about the inferred name.

    Parameters
    ----------
    source : SourcesOrListOfSources
        Source path or paths used to infer the name.
    entity_type : str
        Entity type used to build the validation error.
    entity_kind : str
        Entity kind used to identify the inferred name in the warning.

    Returns
    -------
    str
        The inferred entity name.
    """
    if isinstance(source, list) and len(source) != 1:
        raise ValueError(f"register_{entity_type} requires a single source path.")
    if name is not None:
        return name
    if isinstance(source, list):
        source = source[0]
    name = build_log_name_from_source(source)
    name_warning(inferred_name=name, entity_kind=entity_kind)
    return name
