# pystapi

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/stapi-spec/pystapi/ci.yaml?style=for-the-badge)](https://github.com/stapi-spec/pystapi/actions/workflows/ci.yaml)

Monorepo for Python Satellite Tasking API (STAPI) Specification packages.
For more, see our [docs](https://stapi-spec.github.io/pystapi/).

## Development

Get [uv](https://docs.astral.sh/uv/), then:

```shell
git clone git@github.com:stapi-spec/pystapi.git
cd pystapi
uv sync
```

Test:

```shell
uv run pytest
```

Check formatting and other lints:

```shell
uv run pre-commit run --all-files
```

If you don't want to type `uv run` all the time:

```shell
source .venv/bin/activate
```

See our [contribution guidelines](./CONTRIBUTING.md) for information on contributing any changes, fixes, or features.

## Packages

```mermaid
graph
    stapi-pydantic --> pystapi-client --> pystapi-validator
    stapi-pydantic --> stapi-fastapi
```

### stapi-fastapi

A minimal test implementation is provided in [stapi-fastapi/tests/application.py](stapi-fastapi/tests/application.py).
Run it like so:

```commandline
uv run fastapi dev stapi-fastapi/tests/application.py
```

The app should be accessible at `http://localhost:8000`.

### pustapi-client

The `pystapi-client` package is a Python client (CLI tool) focused on interfacing with the STAPI specification, specifically with a STAPI server. This is a work in progress.

For more information, see the [README](pystapi-client/README.md).
