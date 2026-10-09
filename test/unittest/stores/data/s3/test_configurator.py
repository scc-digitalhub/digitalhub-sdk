# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

import digitalhub.stores.data.s3.configurator as configurator_module
from digitalhub.stores.client.common.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.data.s3.configurator import S3StoreConfigurator


def test_uses_static_credentials_without_calling_sts(monkeypatch) -> None:
    credentials = {
        ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test",
        CredentialsVars.S3_ACCESS_KEY_ID.value: "static-access",
        CredentialsVars.S3_SECRET_ACCESS_KEY.value: "static-secret",
    }
    monkeypatch.setattr(
        configurator_module,
        "get_client",
        lambda: Mock(get_credentials_and_config=lambda: credentials),
    )
    boto3_module = Mock()
    monkeypatch.setattr(configurator_module, "boto3", boto3_module, raising=False)

    configurator = S3StoreConfigurator()
    result = configurator.get_credentials(lowercase_keys=False)

    assert result[CredentialsVars.S3_ACCESS_KEY_ID.value] == "static-access"
    assert result[CredentialsVars.S3_SECRET_ACCESS_KEY.value] == "static-secret"
    boto3_module.client.assert_not_called()


def test_assumes_role_with_web_identity_and_caches_credentials(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "web-identity-token"
    token_file.write_text("identity-token\n", encoding="utf-8")
    credentials = {
        ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test",
        ConfigurationVars.S3_ENDPOINT_URL_STS.value: "https://sts.example.test",
        ConfigurationVars.S3_REGION.value: "eu-west-1",
        CredentialsVars.S3_ROLE_ARN.value: "arn:aws:iam::123456789012:role/test-role",
        CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value: str(token_file),
        CredentialsVars.S3_WEB_IDENTITY_TOKEN.value: "inline-token",
    }
    monkeypatch.setattr(
        configurator_module,
        "get_client",
        lambda: Mock(get_credentials_and_config=lambda: credentials),
    )
    sts_client = Mock()
    sts_client.assume_role_with_web_identity.return_value = {
        "Credentials": {
            "AccessKeyId": "temporary-access",
            "SecretAccessKey": "temporary-secret",
            "SessionToken": "temporary-session",
            "Expiration": datetime.now(timezone.utc) + timedelta(hours=1),
        }
    }
    sts_factory = Mock(return_value=sts_client)
    boto3_module = Mock(client=sts_factory)
    monkeypatch.setattr(configurator_module, "boto3", boto3_module, raising=False)

    configurator = S3StoreConfigurator()
    first_result = configurator.get_credentials(lowercase_keys=False)
    second_result = configurator.get_credentials(lowercase_keys=False)

    assert first_result[CredentialsVars.S3_ACCESS_KEY_ID.value] == "temporary-access"
    assert first_result[CredentialsVars.S3_SECRET_ACCESS_KEY.value] == "temporary-secret"
    assert first_result[CredentialsVars.S3_SESSION_TOKEN.value] == "temporary-session"
    assert second_result == first_result
    boto3_module.client.assert_called_once_with(
        "sts",
        endpoint_url="https://sts.example.test",
        region_name="eu-west-1",
    )
    sts_client.assume_role_with_web_identity.assert_called_once_with(
        RoleArn="arn:aws:iam::123456789012:role/test-role",
        RoleSessionName="digitalhub-s3-store",
        WebIdentityToken="identity-token",
    )


def test_uses_configured_token_when_token_file_is_unavailable(monkeypatch, tmp_path) -> None:
    credentials = {
        ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test",
        ConfigurationVars.S3_ENDPOINT_URL_STS.value: "https://sts.example.test",
        CredentialsVars.S3_ROLE_ARN.value: "arn:aws:iam::123456789012:role/test-role",
        CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value: str(tmp_path / "missing-token"),
        CredentialsVars.S3_WEB_IDENTITY_TOKEN.value: "inline-token",
    }
    monkeypatch.setattr(
        configurator_module,
        "get_client",
        lambda: Mock(get_credentials_and_config=lambda: credentials),
    )
    sts_client = Mock()
    sts_client.assume_role_with_web_identity.return_value = {
        "Credentials": {
            "AccessKeyId": "temporary-access",
            "SecretAccessKey": "temporary-secret",
            "SessionToken": "temporary-session",
            "Expiration": datetime.now(timezone.utc) + timedelta(hours=1),
        }
    }
    sts_factory = Mock(return_value=sts_client)
    monkeypatch.setattr(configurator_module, "boto3", Mock(client=sts_factory), raising=False)

    configurator = S3StoreConfigurator()
    result = configurator.get_credentials(lowercase_keys=False)

    assert result[CredentialsVars.S3_ACCESS_KEY_ID.value] == "temporary-access"
    sts_client.assume_role_with_web_identity.assert_called_once_with(
        RoleArn="arn:aws:iam::123456789012:role/test-role",
        RoleSessionName="digitalhub-s3-store",
        WebIdentityToken="inline-token",
    )


def test_refreshes_web_identity_credentials_before_expiration(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "web-identity-token"
    token_file.write_text("identity-token\n", encoding="utf-8")
    credentials = {
        ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test",
        ConfigurationVars.S3_ENDPOINT_URL_STS.value: "https://sts.example.test",
        CredentialsVars.S3_ROLE_ARN.value: "arn:aws:iam::123456789012:role/test-role",
        CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value: str(token_file),
    }
    monkeypatch.setattr(
        configurator_module,
        "get_client",
        lambda: Mock(get_credentials_and_config=lambda: credentials),
    )
    sts_client = Mock()
    sts_client.assume_role_with_web_identity.side_effect = [
        {
            "Credentials": {
                "AccessKeyId": "first-access",
                "SecretAccessKey": "first-secret",
                "SessionToken": "first-session",
                "Expiration": datetime.now(timezone.utc) + timedelta(minutes=4),
            }
        },
        {
            "Credentials": {
                "AccessKeyId": "second-access",
                "SecretAccessKey": "second-secret",
                "SessionToken": "second-session",
                "Expiration": datetime.now(timezone.utc) + timedelta(hours=1),
            }
        },
    ]
    monkeypatch.setattr(configurator_module, "boto3", Mock(client=Mock(return_value=sts_client)), raising=False)

    configurator = S3StoreConfigurator()
    first_result = configurator.get_credentials(lowercase_keys=False)
    second_result = configurator.get_credentials(lowercase_keys=False)

    assert first_result[CredentialsVars.S3_ACCESS_KEY_ID.value] == "first-access"
    assert second_result[CredentialsVars.S3_ACCESS_KEY_ID.value] == "second-access"
    assert sts_client.assume_role_with_web_identity.call_count == 2


@pytest.mark.parametrize(
    "credentials",
    [
        {
            CredentialsVars.S3_ACCESS_KEY_ID.value: "static-access",
            CredentialsVars.S3_SECRET_ACCESS_KEY.value: "static-secret",
        },
        {
            ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test",
            CredentialsVars.S3_ACCESS_KEY_ID.value: "static-access",
        },
        {
            ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test",
            ConfigurationVars.S3_ENDPOINT_URL_STS.value: "https://sts.example.test",
            CredentialsVars.S3_ROLE_ARN.value: "arn:aws:iam::123456789012:role/test-role",
        },
        {
            ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test",
            CredentialsVars.S3_ROLE_ARN.value: "arn:aws:iam::123456789012:role/test-role",
            CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value: "/tmp/token",
        },
        {
            ConfigurationVars.S3_ENDPOINT_URL_STS.value: "https://sts.example.test",
            CredentialsVars.S3_ROLE_ARN.value: "arn:aws:iam::123456789012:role/test-role",
            CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value: "/tmp/token",
        },
    ],
)
def test_rejects_incomplete_credential_sets(monkeypatch, credentials) -> None:
    monkeypatch.setattr(
        configurator_module,
        "get_client",
        lambda: Mock(get_credentials_and_config=lambda: credentials),
    )

    with pytest.raises(ValueError, match="Missing required variables for S3 store"):
        S3StoreConfigurator()


def test_validation_error_lists_missing_keys_for_both_credential_bundles(monkeypatch) -> None:
    credentials = {ConfigurationVars.S3_ENDPOINT_URL.value: "https://s3.example.test"}
    monkeypatch.setattr(
        configurator_module,
        "get_client",
        lambda: Mock(get_credentials_and_config=lambda: credentials),
    )

    with pytest.raises(ValueError) as error:
        S3StoreConfigurator()

    message = str(error.value)
    assert (
        f"static credential bundle missing: {CredentialsVars.S3_ACCESS_KEY_ID.value}, "
        f"{CredentialsVars.S3_SECRET_ACCESS_KEY.value}"
    ) in message
    assert (
        f"web identity bundle missing: {CredentialsVars.S3_ROLE_ARN.value}, "
        f"{CredentialsVars.S3_WEB_IDENTITY_TOKEN_FILE.value} or "
        f"{CredentialsVars.S3_WEB_IDENTITY_TOKEN.value}, {ConfigurationVars.S3_ENDPOINT_URL_STS.value}"
    ) in message
