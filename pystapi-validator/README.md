# pystapi-validator

This project provides API validation for STAPI FastAPI implementations using Schemathesis against an OpenAPI
specification you supply.

## Configuration

The OpenAPI document to validate against is supplied by the caller, so this checks conformance to the spec rather than
that a document matches the application it was exported from.

- `STAPI_OPENAPI_SCHEMA` — path to the OpenAPI document. Required; without it the suite skips every check.
- `STAPI_BASE_URL` — base URL of the running server. Defaults to `http://localhost:8000`.

The `pystapi-validator` console script sets both from its arguments, so you do not normally set them yourself.

## Setup

1. Install dependencies:

```bash
uv sync
```

1. Start the server you want to validate, then run the validator against a document:

```bash
uv run pystapi-validator path/to/openapi.yaml
```

Pass `--base-url` if the server is not on `http://localhost:8000`.

1. To generate an HTML report, invoke pytest directly with the environment the console script would have set:

```bash
STAPI_OPENAPI_SCHEMA=path/to/openapi.yaml \
  uv run pytest tests/test_validate_api.py --html=report.html --self-contained-html
```

1. Open `report.html` in your browser to view the detailed test report.

## Validating the stapi-fastapi test server

`scripts/validate-stapi-fastapi` in the repository root starts the stapi-fastapi test application and runs this suite
against it. It takes the OpenAPI document as its one argument:

```bash
scripts/validate-stapi-fastapi path/to/openapi.yaml
```
