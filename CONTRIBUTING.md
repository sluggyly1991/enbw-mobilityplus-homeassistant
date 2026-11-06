# Contributing

Open an issue to discuss a change or send a focused pull request. Use synthetic fixtures only; never commit Home Assistant configuration, actual account data, credentials or travel history.

The repository preserves the original Python client under `src/`. The Home Assistant integration lives entirely under `custom_components/enbw_mobilityplus/` and depends on the published upstream client. Do not modify the upstream PyPI publishing metadata merely to bump an integration release.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/ruff check custom_components tests fetch_history.py
.venv/bin/ruff format --check custom_components tests fetch_history.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_repository.py
```

Run Home Assistant-specific smoke tests on a disposable development instance, not a production home. Install the component, validate configuration, test config flow and options, check service responses and entity IDs, then unload/reload. Never log upstream authentication response bodies.

For a release: update the integration manifest version and changelog, push, wait for **HACS**, **hassfest** and all **Tests** jobs to pass without ignored checks, then publish a GitHub release for that commit. The root client package version is independent.

HACS default catalog admission requires its own review; see [docs/HACS.md](docs/HACS.md).
