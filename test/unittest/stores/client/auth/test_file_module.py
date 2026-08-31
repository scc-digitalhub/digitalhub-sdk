from dotenv import dotenv_values

from digitalhub.stores.client.auth import file_module
from digitalhub.stores.client.common.config import ClientConfig, get_client_config, set_client_config


def test_write_dotenv_preserves_unrelated_values(tmp_path) -> None:
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("UNRELATED=keep\nDHCORE_ACCESS_TOKEN=old\n")
    original_config = get_client_config()

    try:
        set_client_config(ClientConfig(config_ini_path=tmp_path / "config.ini"))
        file_module.write_dotenv({"dhcore_access_token": "new"})
    finally:
        set_client_config(original_config)

    assert dotenv_values(dotenv_file) == {
        "UNRELATED": "keep",
        "DHCORE_ACCESS_TOKEN": "new",
    }
