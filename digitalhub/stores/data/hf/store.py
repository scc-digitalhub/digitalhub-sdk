# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from digitalhub.stores.data._base.store import Store
from digitalhub.stores.data.hf.dragonfly import backend_factory, dragonfly
from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.uri_utils import has_hf_scheme


class HFStore(Store):
    """
    Hugging Face store class.

    This store only supports downloading model repositories from the
    Hugging Face Hub to a local directory.
    """

    def download(
        self,
        src: str,
        dst: Path,
        overwrite: bool = False,
    ) -> str:
        """
        Download a Hugging Face model repository to local storage.
        """
        try:
            from huggingface_hub import set_client_factory, snapshot_download
        except ImportError as exc:
            raise StoreError(
                "Hugging Face support requires the 'huggingface_hub' package. "
                "Install it with 'pip install digitalhub[huggingface]'."
            ) from exc

        if dst is None:
            dst = self._build_temp()
        else:
            self._check_local_dst(str(dst))

        dst = Path(dst)
        if dst.suffix:
            raise StoreError("The destination path for a Hugging Face model must be a directory.")

        if dst.exists():
            if dst.is_file():
                raise StoreError("The destination path for a Hugging Face model must be a directory.")
            if any(dst.iterdir()) and not overwrite:
                raise StoreError(f"Destination {dst!s} already exists.")

        dst.mkdir(parents=True, exist_ok=True)

        repo_id, revision = self._parse_source(src)
        if dragonfly:
            set_client_factory(backend_factory=backend_factory)
        snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_dir=str(dst),
            local_dir_use_symlinks=False,
        )
        return str(dst)

    def get_file_info(self, root: str, paths: list[tuple[str, str]]) -> list[dict]:
        """
        File metadata is not tracked by the Hugging Face store.
        """
        return []

    @staticmethod
    def _parse_source(src: str) -> tuple[str, str | None]:
        """
        Parse the Hugging Face source URI into repository id and revision.
        """
        if not has_hf_scheme(src):
            raise StoreError(f"Unsupported Hugging Face URI: {src}")

        parsed = urlparse(src)
        repo_id = unquote(f"{parsed.netloc}{parsed.path}").lstrip("/")
        if not repo_id:
            raise StoreError(f"Invalid Hugging Face repository id in URI: {src}")

        revision = (parse_qs(parsed.query).get("revision") or [None])[0]

        return repo_id, revision
