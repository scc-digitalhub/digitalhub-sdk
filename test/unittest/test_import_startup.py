import subprocess
import sys
import textwrap


def test_import_digitalhub_defers_heavy_integrations() -> None:
    script = textwrap.dedent(
        """
        import sys
        import digitalhub

        heavy_modules = (
            "boto3",
            "botocore",
            "numpy",
            "pandas",
            "polars",
            "pyarrow",
            "sqlalchemy",
        )
        loaded = [
            name
            for name in heavy_modules
            if any(module == name or module.startswith(name + ".") for module in sys.modules)
        ]
        assert not loaded, f"Unexpected eager imports: {loaded}"

        from digitalhub.stores.data.api import get_store

        assert type(get_store(".")).__name__ == "LocalStore"
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
