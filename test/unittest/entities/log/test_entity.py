from digitalhub.entities._base.metadata.entity import Metadata
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes, State
from digitalhub.entities.log._base.builder import LogLogBuilder
from digitalhub.entities.log._base.entity import Log
from digitalhub.entities.log._base.spec import LogSpec
from digitalhub.entities.log._base.status import LogStatus
from digitalhub.utils.generic_utils import encode_string


def build_log() -> Log:
    return Log(
        project="my-project",
        name="run-log",
        uuid="log-id",
        kind=EntityKinds.LOG_LOG.value,
        metadata=Metadata(name="run-log"),
        spec=LogSpec(run="run-id"),
        status=LogStatus(state=State.CREATED.value),
    )


def test_log_starts_without_content() -> None:
    log = build_log()

    assert log._content is None
    assert log.text is None


def test_set_content_decodes_base64_and_exposes_text() -> None:
    log = build_log()
    content = encode_string("log output\nfinished")

    log.set_content(content)

    assert log._content == content
    assert log.text == "log output\nfinished"


def test_log_spec_stores_run_and_timestamp() -> None:
    spec = LogSpec(run="run-id", timestamp=123)

    assert spec.run == "run-id"
    assert spec.timestamp == 123


def test_log_builder_builds_entity() -> None:
    log = LogLogBuilder().build(
        kind=EntityKinds.LOG_LOG.value,
        project="my-project",
        name="run-log",
        uuid="log-id",
        description="Run output",
        labels=["job"],
        run="run-id",
        timestamp=123,
    )

    assert isinstance(log, Log)
    assert log.ENTITY_TYPE == EntityTypes.LOG.value
    assert log.project == "my-project"
    assert log.name == "run-log"
    assert log.id == "log-id"
    assert log.kind == EntityKinds.LOG_LOG.value
    assert log.metadata.description == "Run output"
    assert log.metadata.labels == ["job"]
    assert log.spec.run == "run-id"
    assert log.spec.timestamp == 123
    assert log.status.state == State.CREATED.value
