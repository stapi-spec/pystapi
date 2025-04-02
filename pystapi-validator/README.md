# pystapi-validator

This project provides API validation for STAPI FastAPI implementations using Schemathesis against the latest STAPI OpenAPI
specification.

## Configuration

- The STAPI OpenAPI specification is fetched from:
  [STAPI OpenAPI Spec](https://raw.githubusercontent.com/stapi-spec/stapi-spec/refs/heads/main/openapi.yaml)
- The base URL for the API being tested is set to `http://localhost:8000`. Update the `BASE_URL` in `tests/validate_api.py`
  if your API is hosted elsewhere.

## Setup

1. Install dependencies:

```bash
uv sync
```

1. Run tests and generate report:

```bash
uv run pytest tests/validate_api.py --html=report.html --self-contained-html
```

1. Open `report.html` in your browser to view the detailed test report.
