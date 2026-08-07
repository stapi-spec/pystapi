"""Tests for the OpenAPI document a multi-product deployment publishes.

The fixtures mount several products on one root router, so every route family is
registered once per product. Whether a name derived per route is unique -- an
operationId, a parameterized component -- is only a real question under those
conditions.
"""

from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}

PRODUCT_ID = "test-spotlight"

SEARCH_OPPORTUNITIES_PATH = f"/products/{PRODUCT_ID}/opportunities"


def operations(spec: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    return [
        (path, method, operation)
        for path, path_item in spec["paths"].items()
        for method, operation in path_item.items()
        if method in HTTP_METHODS
    ]


@pytest.fixture
def spec(stapi_client_async_opportunity: TestClient) -> dict[str, Any]:
    # TestClient types `app` as the bare ASGI callable; the fixture always
    # builds a FastAPI app, which is what exposes `openapi()`.
    return cast(FastAPI, stapi_client_async_opportunity.app).openapi()


def test_routes_declare_only_the_errors_they_produce(spec: dict[str, Any]) -> None:
    """`errors` is declared per route rather than applied blanket.

    The landing page takes no input and calls no backend, so it can fail no way
    the document should promise; a paginated collection can do both.
    """
    assert set(spec["paths"]["/"]["get"]["responses"]) == {"200"}
    assert {"404", "500"} <= set(spec["paths"]["/orders"]["get"]["responses"])


def test_no_component_schema_is_unreferenced(spec: dict[str, Any]) -> None:
    """An orphan component is a schema a reader cannot reach and a client cannot use."""
    schemas = spec["components"]["schemas"]
    referenced: set[str] = set()

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str):
                referenced.add(ref.rpartition("/")[2])
            discriminator = node.get("discriminator")
            if isinstance(discriminator, dict):
                # mapping values are bare ref strings, not {"$ref": ...} objects
                referenced.update(value.rpartition("/")[2] for value in discriminator.get("mapping", {}).values())
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for item in node:
                collect(item)

    collect(spec["paths"])
    collect(schemas)

    assert set(schemas) - referenced == set()
