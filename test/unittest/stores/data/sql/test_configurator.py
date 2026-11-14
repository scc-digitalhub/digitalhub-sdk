from unittest.mock import Mock

from sqlalchemy.engine import make_url

from digitalhub.stores.client.common.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.data.sql import configurator as configurator_module
from digitalhub.stores.data.sql.configurator import SqlStoreConfigurator


def test_get_sql_conn_string_encodes_special_credentials(monkeypatch) -> None:
    credentials = {
        CredentialsVars.DB_USERNAME.value: "data@user",
        CredentialsVars.DB_PASSWORD.value: "p@ss:/#word",
        ConfigurationVars.DB_HOST.value: "database.example",
        ConfigurationVars.DB_PORT.value: "5433",
        ConfigurationVars.DB_DATABASE.value: "analytics",
    }
    client = Mock()
    client.get_credentials_and_config.return_value = credentials
    monkeypatch.setattr(configurator_module, "get_client", lambda: client)
    configurator = object.__new__(SqlStoreConfigurator)

    connection_string = configurator.get_sql_conn_string()
    parsed_url = make_url(connection_string)

    assert parsed_url.drivername == "postgresql+pg8000"
    assert parsed_url.username == "data@user"
    assert parsed_url.password == "p@ss:/#word"
    assert parsed_url.host == "database.example"
    assert parsed_url.port == 5433
    assert parsed_url.database == "analytics"
