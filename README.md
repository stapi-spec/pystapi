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
uv run pre-commit --all-files
```

If you don't want to type `uv run` all the time:

```shell
source .venv/bin/activate
```

See our [contribution guidelines](./CONTRIBUTING.md) for information on contributing any changes, fixes, or features.

### stapi-fastapi server

A minimal test implementation is provided in [stapi-fastapi/tests/application.py](stapi-fastapi/tests/application.py).
Run it like so:

```commandline
uv run fastapi dev stapi-fastapi/tests/application.py
```

The app should be accessible at `http://localhost:8000`.

## Packages

```mermaid
graph
    stapi-pydantic --> pystapi-client --> pystapi-validator
    stapi-pydantic --> stapi-fastapi
```
