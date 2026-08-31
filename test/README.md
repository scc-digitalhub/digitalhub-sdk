# Test suites

Tests are split by responsibility:

```text
test/
├── conftest.py
├── instances/          # Serialized entity compatibility and schema validation
└── unittest/           # Isolated tests mirroring the digitalhub package
    ├── context/
    ├── entities/
    ├── factory/
    └── stores/
```

Unit tests must be deterministic and must not require network access, external services, or generated fixtures. Place each test beside the matching package path under `test/unittest` and keep shared fixtures in the nearest useful `conftest.py`.

Instance tests validate serialized entities against schemas supplied by DigitalHub Core. CI downloads those schemas into `test/instances/schemas` before running the suite.

Run the suites independently:

```bash
pytest test/unittest
pytest test/instances
```

The directory-based `unit` and `instance` markers also support selective runs:

```bash
pytest -m unit
pytest -m instance
```
