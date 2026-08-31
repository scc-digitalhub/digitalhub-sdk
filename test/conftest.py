from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).parent.resolve()
SUITE_MARKERS = {
    (TEST_ROOT / "unittest").resolve(): pytest.mark.unit,
    (TEST_ROOT / "instances").resolve(): pytest.mark.instance,
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark tests according to their top-level suite directory."""
    for item in items:
        test_path = Path(item.path).resolve()
        for suite_path, marker in SUITE_MARKERS.items():
            if test_path.is_relative_to(suite_path):
                item.add_marker(marker)
                break
