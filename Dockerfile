ARG PYTHON_VERSION=3.12
ARG BASE_IMAGE=ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-alpine

FROM ${BASE_IMAGE} as base

WORKDIR /app
COPY . /app

RUN uv sync --frozen 

CMD ["uv", "run", "fastapi", "dev", "/app/stapi-fastapi/tests/application.py", "--host", "0.0.0.0", "--port", "80"]
