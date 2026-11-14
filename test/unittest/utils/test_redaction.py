from digitalhub.stores.client.common.redaction import REDACTED, redact_dict, redact_headers


def test_redact_headers_masks_sensitive_names_case_insensitively() -> None:
    headers = {
        "Authorization": "Bearer token",
        "cOoKiE": "session-cookie",
        "X-API-Key": "api-key",
        "Accept": "application/json",
    }

    assert redact_headers(headers) == {
        "Authorization": REDACTED,
        "cOoKiE": REDACTED,
        "X-API-Key": REDACTED,
        "Accept": "application/json",
    }


def test_redact_dict_recursively_masks_sensitive_values() -> None:
    data = {
        "refresh_token": "refresh-value",
        "nested": [
            {"DB_PASSWORD": "db-password", "name": "demo"},
            {"client-secret": "client-secret"},
        ],
        "credential_id": "credential-id",
    }

    assert redact_dict(data) == {
        "refresh_token": REDACTED,
        "nested": [
            {"DB_PASSWORD": REDACTED, "name": "demo"},
            {"client-secret": REDACTED},
        ],
        "credential_id": REDACTED,
    }
    assert data["refresh_token"] == "refresh-value"
