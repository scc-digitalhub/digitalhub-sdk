from digitalhub_core.runtimes.registry import RuntimeRegistry

registry = RuntimeRegistry()
registry.register(
    "digitalhub_ml_mlrun.runtimes.runtime",
    "RuntimeMlrun",
)
