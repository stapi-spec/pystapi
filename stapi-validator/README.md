## About

This project provides API validation for STAPI FastAPI implementations using Schemathesis against the latest STAPI OpenAPI specification.

## Configuration

- The STAPI OpenAPI specification is fetched from: https://raw.githubusercontent.com/stapi-spec/stapi-spec/refs/heads/main/openapi.yaml
- The base URL for the API being tested is set to `http://localhost:8000`. Update the `BASE_URL` in `tests/validate_api.py` if your API is hosted elsewhere.

## Setup

1. Install dependencies:
   ```
   poetry install
   ```

2. Run tests and generate report:
   ```
   poetry run pytest tests/validate_api.py --html=report.html --self-contained-html
   ```

3. Open `report.html` in your browser to view the detailed test report.

