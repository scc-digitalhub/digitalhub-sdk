# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import inspect
from pathlib import Path

import pytest

from digitalhub.entities._base.entity.builder import EntityBuilder
from digitalhub.entities._base.entity.entity import BaseEntity, PersistedEntity
from digitalhub.runtimes._base import Runtime
from digitalhub.stores.data._base.store import Store
from digitalhub.stores.readers.data._base.reader import DataframeReader
from digitalhub.utils.exceptions import StoreError


class FileInfoOnlyStore(Store):
    def get_file_info(self, root: str, paths: list[tuple[str, str]]) -> list[dict]:
        return []


@pytest.mark.parametrize(
    "abstract_class",
    [PersistedEntity, EntityBuilder, Runtime, Store, DataframeReader],
)
def test_abstract_base_classes_enforce_their_contract(abstract_class: type) -> None:
    assert inspect.isabstract(abstract_class)


def test_base_entity_is_concrete() -> None:
    assert not inspect.isabstract(BaseEntity)


@pytest.mark.parametrize(
    ("method_name", "args", "capability"),
    [
        ("download", ("source", Path("destination")), "download"),
        ("upload", ("source", "destination"), "upload"),
        ("read_df", ("source",), "read_df"),
        ("write_df", (object(), "destination"), "write_df"),
    ],
)
def test_store_default_capabilities_raise_consistent_errors(
    method_name: str,
    args: tuple,
    capability: str,
) -> None:
    store = FileInfoOnlyStore()

    with pytest.raises(StoreError, match=f"FileInfoOnlyStore does not support {capability}"):
        getattr(store, method_name)(*args)
