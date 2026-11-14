from unittest.mock import Mock

import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError, EndpointConnectionError

from digitalhub.stores.data.s3.store import S3Store
from digitalhub.utils.exceptions import ConfigError, StoreError


def test_download_without_destination_uses_temp_directory(tmp_path) -> None:
    store = object.__new__(S3Store)
    client = Mock()
    store._build_temp = Mock(return_value=tmp_path)
    store._check_factory = Mock(return_value=(client, "bucket"))
    store.is_partition = Mock(return_value=False)
    store._check_overwrite = Mock()
    store._build_path = Mock()
    store._download_file = Mock()

    assert store.download("s3://bucket/file.txt", None) == str(tmp_path / "file.txt")

    store._build_temp.assert_called_once_with()
    store._download_file.assert_called_once_with("file.txt", tmp_path / "file.txt", client, "bucket")


def test_upload_dir_uses_posix_relative_keys(tmp_path) -> None:
    source = tmp_path / "source"
    nested = source / "nested"
    nested.mkdir(parents=True)
    file = nested / "data.csv"
    file.write_text("data")
    store = object.__new__(S3Store)
    store._upload_file = Mock()
    client = Mock()

    paths = store._upload_dir(str(source), "target/", client, "bucket")

    assert paths == [("target/nested/data.csv", "nested/data.csv")]
    store._upload_file.assert_called_once_with(file, "target/nested/data.csv", client, "bucket")


def test_upload_file_list_keeps_relative_structure_without_absolute_prefixes(tmp_path) -> None:
    source = tmp_path / "source"
    left = source / "left" / "a.txt"
    right = source / "right" / "b.txt"
    left.parent.mkdir(parents=True)
    right.parent.mkdir(parents=True)
    left.write_text("a")
    right.write_text("b")
    store = object.__new__(S3Store)
    store._upload_file = Mock()
    client = Mock()

    paths = store._upload_file_list(
        [str(left), str(right)],
        "target/",
        client,
        "bucket",
        keep_dir_structure=True,
    )

    assert paths == [
        ("target/left/a.txt", "left/a.txt"),
        ("target/right/b.txt", "right/b.txt"),
    ]
    assert [call.args[1] for call in store._upload_file.call_args_list] == [
        "target/left/a.txt",
        "target/right/b.txt",
    ]


def test_download_file_wraps_botocore_errors(tmp_path) -> None:
    client = Mock()
    error = EndpointConnectionError(endpoint_url="https://s3.example")
    client.download_file.side_effect = error

    with pytest.raises(StoreError, match="S3 download file failed") as raised:
        S3Store._download_file("key", tmp_path / "file.txt", client, "bucket")

    assert raised.value.__cause__ is error


def test_upload_file_wraps_boto3_transfer_errors(tmp_path) -> None:
    source = tmp_path / "file.txt"
    source.write_text("data")
    client = Mock()
    error = S3UploadFailedError("upload failed")
    client.upload_file.side_effect = error

    with pytest.raises(StoreError, match="S3 upload file failed") as raised:
        S3Store._upload_file(str(source), "key", client, "bucket")

    assert raised.value.__cause__ is error


def test_get_file_info_wraps_client_errors() -> None:
    store = object.__new__(S3Store)
    client = Mock()
    error = ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}}, "HeadObject")
    client.head_object.side_effect = error
    store._check_factory = Mock(return_value=(client, "bucket"))

    with pytest.raises(StoreError, match="S3 get file metadata failed") as raised:
        store.get_file_info("s3://bucket/", [("s3://bucket/key", "key")])

    assert raised.value.__cause__ is error


def test_check_factory_wraps_bucket_access_errors() -> None:
    store = object.__new__(S3Store)
    store._configurator = Mock()
    store._configurator.get_client_config.return_value = {}
    store._configurator.eval_retry.return_value = False
    error = EndpointConnectionError(endpoint_url="https://s3.example")
    client = Mock()
    client.head_bucket.side_effect = error
    store._get_client = Mock(return_value=client)

    with pytest.raises(StoreError, match="S3 access check failed") as raised:
        store._check_factory("s3://bucket/")

    assert isinstance(raised.value.__cause__, ConfigError)
    assert raised.value.__cause__.__cause__ is error
