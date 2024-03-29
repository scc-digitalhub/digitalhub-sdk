from __future__ import annotations

from digitalhub_core.utils.logger import LOGGER
from digitalhub_data_dbt.utils.env import get_connection
from psycopg2 import sql


def cleanup(tables: list[str]) -> None:
    """
    Cleanup environment.

    Parameters
    ----------
    tables : list[str]
        List of tables to delete.

    Returns
    -------
    None
    """
    try:
        connection = get_connection()
        with connection:
            with connection.cursor() as cursor:
                for table in tables:
                    LOGGER.info(f"Dropping table '{table}'.")
                    query = sql.SQL("DROP TABLE {table}").format(table=sql.Identifier(table))
                    cursor.execute(query)
    except Exception:
        msg = "Something got wrong during environment cleanup."
        LOGGER.exception(msg)
        raise RuntimeError(msg)
    finally:
        LOGGER.info("Closing connection to postgres.")
        connection.close()
