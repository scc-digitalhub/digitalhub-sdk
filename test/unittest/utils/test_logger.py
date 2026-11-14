import json
import os
import subprocess
import sys


def _run_logger_probe(*, log_level: str | None = None) -> dict:
    environment = os.environ.copy()
    environment.pop("DHCORE_LOG_LEVEL", None)
    environment.pop("DHCORE_LOG_FORMAT", None)
    if log_level is not None:
        environment["DHCORE_LOG_LEVEL"] = log_level

    script = """
import json
import logging
import digitalhub as dh

logger = logging.getLogger("dhcore")
before = {
    "level": logger.level,
    "propagate": logger.propagate,
    "null_handlers": sum(isinstance(handler, logging.NullHandler) for handler in logger.handlers),
    "stream_handlers": sum(isinstance(handler, logging.StreamHandler) for handler in logger.handlers),
}
if "DHCORE_LOG_LEVEL" not in __import__("os").environ:
    dh.configure_logging("DEBUG")
    dh.configure_logging(logging.WARNING)
after = {
    "level": logger.level,
    "propagate": logger.propagate,
    "null_handlers": sum(isinstance(handler, logging.NullHandler) for handler in logger.handlers),
    "stream_handlers": sum(isinstance(handler, logging.StreamHandler) for handler in logger.handlers),
}
print(json.dumps({"before": before, "after": after}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=True,
        env=environment,
        text=True,
    )
    return json.loads(result.stdout.splitlines()[-1])


def test_default_logger_is_non_intrusive_and_configuration_is_explicit() -> None:
    result = _run_logger_probe()

    assert result["before"] == {
        "level": 0,
        "propagate": True,
        "null_handlers": 1,
        "stream_handlers": 0,
    }
    assert result["after"] == {
        "level": 30,
        "propagate": False,
        "null_handlers": 1,
        "stream_handlers": 1,
    }


def test_log_level_environment_variable_enables_console_logging() -> None:
    result = _run_logger_probe(log_level="DEBUG")

    assert result["before"] == {
        "level": 10,
        "propagate": False,
        "null_handlers": 1,
        "stream_handlers": 1,
    }
