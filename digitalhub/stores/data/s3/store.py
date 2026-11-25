# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import Any, BinaryIO
from urllib.parse import urlparse

import boto3
import botocore.client  # pylint: disable=unused-import
from boto3.exceptions import Boto3Error
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import BotoCoreError, ClientError

from digitalhub.stores.data._base.credentials import StoreCredentials
from digitalhub.stores.data._base.store import Store
from digitalhub.stores.data.s3.configurator import S3StoreConfigurator
from digitalhub.stores.readers.data.api import get_reader_by_object
from digitalhub.utils.exceptions import ConfigError, StoreError
from digitalhub.utils.file_utils import get_file_info_from_s3, get_file_mime_type
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import Dataframe, SourcesOrListOfSources

logger = get_logger(__name__)

# Type aliases
S3Client = type["botocore.client.S3"]

MULTIPART_THRESHOLD = 100 * 1024 * 1024


@contextmanager
def _handle_boto_errors(operation: str) -> Generator[None, None, None]:
    try:
        yield
    except (Boto3Error, BotoCoreError, ClientError) as e:
        raise StoreError(f"S3 {operation} failed: {e!s}") from e


class S3Store(Store):
    """
    S3 store class. It implements the Store interface and provides methods to fetch and persist
    artifacts on S3 based storage.
    """

    def __init__(self, credentials: StoreCredentials) -> None:
        super().__init__()
        self._configurator: S3StoreConfigurator = S3StoreConfigurator(credentials)

    ##############################
    # I/O methods
    ##############################

    def download(
        self,
        src: str,
        dst: Path | None,
        overwrite: bool = False,
    ) -> str:
        """
        Download artifacts from storage.
        """
        if dst is None:
            dst = self._build_temp()

        client, bucket = self._check_factory(src)

        # Build destination directory
        if dst.suffix == "":
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)

        # Handle src and tree destination
        if self.is_partition(src):
            keys = self._list_objects(client, bucket, src)
            strip_root = self._get_key(src)
            trees = [k.removeprefix(strip_root) for k in keys]
        else:
            keys = [self._get_key(src)]
            trees = [Path(self._get_key(src)).name]

        if len(keys) != len(trees):
            raise StoreError("Keys and trees must have the same length.")

        # Download files
        for elements in zip(keys, trees):
            key = elements[0]
            tree = elements[1]

            # Build destination path
            if dst.suffix == "":
                dst_pth = Path(dst, tree)
            else:
                dst_pth = dst

            # Check if destination path already exists
            self._check_overwrite(dst_pth, overwrite)

            self._build_path(dst_pth.parent)

            self._download_file(key, dst_pth, client, bucket)

        if len(trees) == 1 and dst.suffix == "":
            return str(Path(dst, trees[0]))
        return str(dst)

    def upload(
        self,
        src: SourcesOrListOfSources,
        dst: str,
        keep_dir_structure: bool = False,
    ) -> list[tuple[str, str]]:
        """
        Upload an artifact to storage.
        """
        # Destination handling
        key = self._get_key(dst)

        # Source handling (files list, dir or single file)
        src_is_list = isinstance(src, list)
        if not src_is_list:
            self._check_local_src(src)
            src_is_dir = Path(src).is_dir()
        else:
            for s in src:
                self._check_local_src(s)
            src_is_dir = False
            if len(src) == 1:
                src = src[0]

        # If source is a directory, destination must be a partition
        if (src_is_dir or src_is_list) and not dst.endswith("/"):
            raise StoreError(
                "If source is a list of files or a directory, "
                "destination must be a partition, e.g. 's3://bucket/partition/'"
            )

        # S3 client
        client, bucket = self._check_factory(dst)

        # Directory
        if src_is_dir:
            return self._upload_dir(src, key, client, bucket)

        # List of files
        elif src_is_list:
            return self._upload_file_list(src, key, client, bucket, keep_dir_structure=keep_dir_structure)

        # Single file
        return self._upload_single_file(src, key, client, bucket)

    def upload_fileobject(
        self,
        src: BytesIO,
        dst: str,
    ) -> str:
        """
        Upload an BytesIO to S3 based storage.
        """
        client, bucket = self._check_factory(dst)
        key = self._get_key(dst)
        self._upload_fileobject(src, key, client, bucket)
        return f"s3://{bucket}/{key}"

    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Method to get file metadata.
        """
        client, bucket = self._check_factory(root)

        infos = []
        for i in paths:
            key, src_path = i

            # Rebuild key in case here arrive an s3://bucket prefix
            key = self._get_key(key)

            # Get metadata
            with _handle_boto_errors("get file metadata"):
                metadata = client.head_object(Bucket=bucket, Key=key)

            # Get file info
            info = get_file_info_from_s3(src_path, metadata)
            infos.append(info)

        return infos

    ##############################
    # Datastore methods
    ##############################

    def read_df(
        self,
        path: SourcesOrListOfSources,
        file_format: str | None = None,
        engine: str | None = None,
        **kwargs,
    ) -> Dataframe:  # type: ignore
        """
        Read DataFrame from path.
        """
        reader = self._get_reader(engine)

        # Verify if partition or single file
        if isinstance(path, str) and self.is_partition(path):
            client, bucket = self._check_factory(path)
            objects = self._list_objects(client, bucket, path)
            keys = []
            for obj in objects:
                key = self._get_key(obj)
                if key.endswith("/") or Path(key).name.startswith("."):
                    continue
                keys.append(key)

        else:
            if isinstance(path, list):
                if not path:
                    raise StoreError(f"No readable data files found in '{path}'.")
                client, bucket = self._check_factory(path[0])
                keys = [self._get_key(p) for p in path]
            else:
                client, bucket = self._check_factory(path)
                keys = [self._get_key(path)]

        dfs = []
        for key in keys:
            extension = self._get_extension(file_format, key)
            with self._download_fileobject(key, client, bucket) as obj:
                dfs.append(reader.read_df(obj, extension=extension, **kwargs))

        if not dfs:
            raise StoreError(f"No readable data files found in '{path}'.")
        if len(dfs) == 1:
            return dfs[0]
        return reader.concat_dfs(dfs)

    def write_df(
        self,
        df: Any,
        dst: str,
        extension: str | None = None,
        **kwargs,
    ) -> str:
        """
        Write a dataframe to S3 based storage. Kwargs are passed to df.to_parquet().
        """
        reader = get_reader_by_object(df)
        with BytesIO() as fileobj:
            reader.write_df(df, fileobj, extension=extension, **kwargs)
            fileobj.seek(0)
            return self.upload_fileobject(fileobj, dst)

    ##############################
    # Wrapper methods
    ##############################

    def get_s3_source(self, src: str, filename: Path) -> None:
        """
        Download a file from S3 and save it to a local file.
        """
        client, bucket = self._check_factory(src)
        key = self._get_key(src)
        self._download_file(key, filename, client, bucket)

    def get_s3_client(self) -> S3Client:
        """
        Get an S3 client object.
        """
        return self._get_client(self._configurator.get_client_config())

    def get_credentials(self, lowercase_keys: bool = True) -> dict:
        """
        Get all configured S3 credentials as a dictionary.
        """
        return self._configurator.get_credentials(lowercase_keys=lowercase_keys)

    ##############################
    # Private I/O methods
    ##############################

    @staticmethod
    def _download_file(
        key: str,
        dst_pth: Path,
        client: S3Client,
        bucket: str,
    ) -> list[str]:
        """
        Download files from S3 partition.
        """
        with _handle_boto_errors("download file"):
            client.download_file(bucket, key, dst_pth)

    @staticmethod
    @contextmanager
    def _download_fileobject(
        key: str,
        client: S3Client,
        bucket: str,
    ) -> Generator[BinaryIO, None, None]:
        """
        Download fileobject from S3 partition.
        """
        with SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b") as fileobj:
            with _handle_boto_errors("download file object"):
                obj = client.get_object(Bucket=bucket, Key=key)
                body = obj["Body"]
                try:
                    while chunk := body.read(1024 * 1024):
                        fileobj.write(chunk)
                finally:
                    body.close()
            fileobj.seek(0)
            yield fileobj

    def _upload_dir(
        self,
        src: str,
        dst: str,
        client: S3Client,
        bucket: str,
    ) -> list[tuple[str, str]]:
        """
        Upload directory to storage.
        """
        # Get list of files
        src_pth = Path(src)
        files = [i for i in src_pth.rglob("*") if i.is_file()]

        relative_paths = [file.relative_to(src_pth).as_posix() for file in files]
        keys = [f"{dst}{relative_path}" for relative_path in relative_paths]

        # Upload files
        paths = []
        for f, k, relative_path in zip(files, keys, relative_paths):
            self._upload_file(f, k, client, bucket)
            paths.append((k, relative_path))
        return paths

    def _upload_file_list(
        self,
        src: list[str],
        dst: str,
        client: S3Client,
        bucket: str,
        keep_dir_structure: bool = False,
    ) -> list[tuple[str, str]]:
        """
        Upload list of files to storage.
        """
        files = src
        if keep_dir_structure and files:
            file_paths = [Path(file).resolve() for file in files]
            try:
                common_path = Path(os.path.commonpath([str(file.parent) for file in file_paths]))
                relative_paths = [file.relative_to(common_path).as_posix() for file in file_paths]
            except ValueError:
                relative_paths = [file.name for file in file_paths]
        else:
            relative_paths = [Path(file).name for file in files]
        keys = [f"{dst}{relative_path}" for relative_path in relative_paths]
        if len(set(keys)) != len(keys):
            raise StoreError("Keys must be unique (Select files with different names, otherwise upload a directory).")

        # Upload files
        paths = []
        for f, k, relative_path in zip(files, keys, relative_paths):
            self._upload_file(f, k, client, bucket)
            paths.append((k, relative_path))
        return paths

    def _upload_single_file(
        self,
        src: str,
        dst: str,
        client: S3Client,
        bucket: str,
    ) -> str:
        """
        Upload a single file to storage.
        """
        if dst.endswith("/"):
            dst = f"{dst.removeprefix('/')}{Path(src).name}"

        # Upload file
        self._upload_file(src, dst, client, bucket)
        name = Path(self._get_key(dst)).name
        return [(dst, name)]

    @staticmethod
    def _upload_file(
        src: str,
        key: str,
        client: S3Client,
        bucket: str,
    ) -> None:
        """
        Upload a file to S3 based storage. The function checks if the
        bucket is accessible.
        """
        extra_args = {}
        mime_type = get_file_mime_type(src)
        if mime_type is not None:
            extra_args["ContentType"] = mime_type
        with _handle_boto_errors("upload file"):
            client.upload_file(
                Filename=src,
                Bucket=bucket,
                Key=key,
                ExtraArgs=extra_args,
                Config=TransferConfig(multipart_threshold=MULTIPART_THRESHOLD),
            )

    @staticmethod
    def _upload_fileobject(
        fileobj: BytesIO,
        key: str,
        client: S3Client,
        bucket: str,
    ) -> None:
        """
        Upload a fileobject to S3 based storage. The function checks if the bucket is accessible.
        """
        with _handle_boto_errors("upload file object"):
            client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=bucket,
                Key=key,
                Config=TransferConfig(multipart_threshold=MULTIPART_THRESHOLD),
            )

    ##############################
    # Helper methods
    ##############################

    def _get_bucket(self, root: str) -> str:
        """
        Get the name of the S3 bucket from the URI.
        """
        return urlparse(root).netloc

    def _get_client(self, cfg: dict) -> S3Client:
        """
        Get an S3 client object.
        """
        return boto3.client("s3", **cfg)

    def _check_factory(self, s3_path: str) -> tuple[S3Client, str]:
        """
        Checks if the S3 bucket collected from the URI is accessible.
        """
        bucket = self._get_bucket(s3_path)
        cfg = self._configurator.get_client_config()
        client = self._get_client(cfg)
        try:
            logger.debug("S3 client configured; checking access to bucket '%s'.", bucket)
            self._check_access_to_storage(client, bucket)
            return client, bucket
        except ConfigError as e:
            if self._configurator.eval_retry():
                logger.debug(f"S3 access check failed for bucket '{bucket}', retrying with new credentials.")
                return self._check_factory(s3_path)
            raise StoreError(f"S3 access check failed: {e!s}") from e

    def _check_access_to_storage(self, client: S3Client, bucket: str) -> None:
        """
        Checks if the S3 bucket is accessible by sending a head_bucket request.
        """
        try:
            client.head_bucket(Bucket=bucket)
        except (ClientError, BotoCoreError) as err:
            raise ConfigError(f"No access to '{bucket}' s3 bucket! Error: {err!s}") from err

    @staticmethod
    def _get_key(path: str) -> str:
        """
        Build key.
        """
        key = urlparse(path).path.replace("\\", "/")
        key = key.removeprefix("/")
        return key

    def _list_objects(self, client: S3Client, bucket: str, partition: str) -> list[str]:
        """
        List objects in a S3 partition.
        """
        key = self._get_key(partition)
        with _handle_boto_errors("list objects"):
            paginator = client.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=bucket, Prefix=key):
                keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return keys

    @staticmethod
    def is_partition(path: str) -> bool:
        """
        Check if path is a directory or a partition.
        """
        return bool(path.endswith("/"))
