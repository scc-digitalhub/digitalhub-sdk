# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from digitalhub.entities.run._base.io_processor import RunIOProcessor

DATAITEM = "store://project/dataitem/table/data:1"
MODEL = "store://project/model/model/model:2"
IMAGE = "store://project/containerimage/containerimage/image:3"


def _entity(key: str) -> SimpleNamespace:
    return SimpleNamespace(key=key, to_dict=lambda: {"key": key})


def _processor() -> RunIOProcessor:
    crud = Mock()
    crud.read_context_entity.side_effect = _entity
    return RunIOProcessor(crud)


def _run(inputs: dict | None = None, outputs: dict | None = None, local: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        spec=SimpleNamespace(inputs=inputs),
        status=SimpleNamespace(outputs=outputs),
        local_execution=lambda: local,
        add_relationship=Mock(),
    )


def test_inputs_are_read_by_key_whatever_their_type() -> None:
    # python and dbt each kept a table of getters, and they differed: dbt
    # refused container images.
    processor = _processor()

    inputs = processor.inputs(_run(inputs={"data": DATAITEM, "image": IMAGE}))

    assert {name: entity.key for name, entity in inputs.items()} == {"data": DATAITEM, "image": IMAGE}
    assert processor.inputs(_run(inputs={"data": DATAITEM}), as_dict=True) == {"data": {"key": DATAITEM}}
    assert processor.inputs(_run()) == {}


def test_outputs_as_keys_are_not_read() -> None:
    processor = _processor()
    run = _run(outputs={"model": MODEL})

    assert processor.outputs(run, as_key=True) == {"model": MODEL}
    processor.crud_processor.read_context_entity.assert_not_called()
    assert processor.outputs(run, as_dict=True) == {"model": {"key": MODEL}}
    assert processor.outputs(_run()) == {}


@pytest.mark.parametrize(
    ("name", "kwargs", "expected"),
    [
        ("model", {}, MODEL),
        ("model", {"as_key": True}, MODEL),
        ("missing", {}, None),
    ],
)
def test_output_reads_only_the_output_asked_for(name, kwargs, expected) -> None:
    processor = _processor()
    run = _run(outputs={"data": DATAITEM, "model": MODEL})

    result = processor.output(run, name, **kwargs)

    assert (result.key if hasattr(result, "key") else result) == expected
    reads = [] if kwargs.get("as_key") or expected is None else [call(MODEL)]
    assert processor.crud_processor.read_context_entity.call_args_list == reads


def test_prepare_inputs_of_a_local_run_records_what_it_consumes() -> None:
    processor = _processor()
    run = _run(inputs={"data": DATAITEM})

    processor.prepare_inputs(run)

    processor.crud_processor.refresh_context_entity.assert_called_once_with(run)
    run.add_relationship.assert_called_once_with(relation="consumes", dest=DATAITEM)
    processor.crud_processor.update_context_entity.assert_called_once_with(run)
    assert run.spec.inputs == {"data": {"key": DATAITEM}}


def test_prepare_inputs_of_a_remote_run_only_passes_them_as_dictionaries() -> None:
    processor = _processor()
    run = _run(inputs={"data": DATAITEM}, local=False)

    processor.prepare_inputs(run)

    run.add_relationship.assert_not_called()
    processor.crud_processor.update_context_entity.assert_not_called()
    assert run.spec.inputs == {"data": {"key": DATAITEM}}
