"""Tests for the shared pagination query parameters, `self` links and totals."""

from typing import Any, cast

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from stapi_fastapi.query_params import MAX_LIMIT, clamp_limit

from .shared import (
    product_test_spotlight_async_opportunity,
)

PAGINATED_PATHS = [
    "/products",
    "/orders",
    "/orders/an-order-id/statuses",
]

INVALID_LIMITS = [0, -2]

LIMITS = [1, 2, 4]

PRODUCT_ID = "test-spotlight"

ORDER_PAYLOAD: dict[str, Any] = {
    "search_parameters": {
        "datetime": "2024-10-09T18:55:33Z/2024-10-12T18:55:33Z",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "filter": {
            "op": "and",
            "args": [
                {"op": ">", "args": [{"property": "off_nadir"}, 0]},
                {"op": "<", "args": [{"property": "off_nadir"}, 45]},
            ],
        },
    },
    "order_parameters": {"s3_path": "s3://my-bucket"},
}


@pytest.mark.parametrize("path", PAGINATED_PATHS)
@pytest.mark.parametrize("limit", INVALID_LIMITS)
def test_out_of_range_limit_is_rejected(path: str, limit: int, stapi_client: TestClient) -> None:
    res = stapi_client.get(path, params={"limit": limit})
    # 422 is spelled out: starlette renamed its constant for this status code,
    # so referencing either name warns on one version or breaks on the other.
    assert res.status_code == 422


@pytest.mark.parametrize("limit", INVALID_LIMITS)
@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_out_of_range_limit_is_rejected_on_search_records(
    limit: int, stapi_client_async_opportunity: TestClient
) -> None:
    res = stapi_client_async_opportunity.get("/searches/opportunities", params={"limit": limit})
    assert res.status_code == 422


@pytest.mark.parametrize("path", PAGINATED_PATHS)
def test_limit_bounds_are_documented(path: str, stapi_client: TestClient) -> None:
    spec = cast(FastAPI, stapi_client.app).openapi()
    parameters = {p["name"]: p for p in spec["paths"][path.replace("an-order-id", "{orderId}")]["get"]["parameters"]}

    limit_schema = parameters["limit"]["schema"]
    assert limit_schema["minimum"] == 1
    assert limit_schema["default"] == 10
    # The spec publishes no maximum, so neither does this: an over-large ask is
    # clamped, and advertising a ceiling would invite a 422 that never comes.
    assert "maximum" not in limit_schema


@pytest.mark.parametrize("path", ["/products", "/orders"])
def test_over_large_limit_is_clamped_not_rejected(path: str, stapi_client: TestClient) -> None:
    """The spec's `limit` is what the client asks for, not what it is owed."""
    res = stapi_client.get(path, params={"limit": MAX_LIMIT + 1})
    assert res.status_code == status.HTTP_200_OK, res.text


def test_clamp_limit_caps_at_the_maximum() -> None:
    assert clamp_limit(MAX_LIMIT + 1) == MAX_LIMIT
    assert clamp_limit(MAX_LIMIT) == MAX_LIMIT
    assert clamp_limit(1) == 1
