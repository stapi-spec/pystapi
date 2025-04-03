ARG PYTHON_VERSION=3.12
ARG BASE_IMAGE=python:${PYTHON_VERSION}-slim-bookworm

FROM ${BASE_IMAGE} AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libffi-dev && apt-get clean
RUN uv sync --frozen

CMD ["uv", "run", "fastapi", "dev", "/app/stapi-fastapi/tests/application.py", "--host", "0.0.0.0", "--port", "80"]
