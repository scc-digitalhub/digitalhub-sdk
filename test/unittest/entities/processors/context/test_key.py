from digitalhub.entities._processors.context.key import ContextEntityKeyProcessor


def test_build_context_entity_key_includes_name_and_id_when_provided() -> None:
    processor = ContextEntityKeyProcessor()

    assert (
        processor.build_context_entity_key(
            "project",
            "function",
            "python",
            "pipeline",
            "function-id",
        )
        == "store://project/function/python/pipeline:function-id"
    )


def test_build_context_entity_key_omits_id_when_not_provided() -> None:
    processor = ContextEntityKeyProcessor()

    assert processor.build_context_entity_key("project", "task", "python+job", "task-id") == (
        "store://project/task/python+job/task-id"
    )
