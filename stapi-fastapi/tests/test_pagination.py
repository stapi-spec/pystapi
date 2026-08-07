"""Tests for the shared pagination query parameters, `self` links and totals."""

from typing import Any, cast
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient
from returns.result import Failure, ResultE
from stapi_fastapi.pagination import Page
from stapi_fastapi.query_params import MAX_LIMIT, clamp_limit
from stapi_fastapi.routers.root_router import RootRouter
from stapi_pydantic import Order, OrderStatus

from .backends import mock_get_order
from .shared import (
    find_link,
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


def query_of(href: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(href).query)


def test_self_link_carries_query_params(stapi_client: TestClient) -> None:
    res = stapi_client.get("/products", params={"limit": 1})
    assert res.status_code == status.HTTP_200_OK

    self_link = find_link(res.json()["links"], "self")
    assert self_link is not None
    assert query_of(self_link["href"]) == {"limit": ["1"]}


def test_self_link_of_second_page_points_at_second_page(stapi_client: TestClient) -> None:
    first = stapi_client.get("/products", params={"limit": 1}).json()
    next_link = find_link(first["links"], "next")
    assert next_link is not None

    second = stapi_client.get(next_link["href"]).json()
    self_link = find_link(second["links"], "self")
    assert self_link is not None
    assert query_of(self_link["href"]) == query_of(next_link["href"])


def test_self_link_survives_a_query_param_named_self(stapi_client: TestClient) -> None:
    """Query param names are data, not Python keywords: `?self=` used to 500."""
    res = stapi_client.get("/products", params={"self": "x"})
    assert res.status_code == status.HTTP_200_OK, res.text

    self_link = find_link(res.json()["links"], "self")
    assert self_link is not None
    assert query_of(self_link["href"]) == {"self": ["x"]}


def test_self_link_preserves_repeated_query_params(stapi_client: TestClient) -> None:
    """A repeated query param keeps every value; it used to collapse to the last."""
    res = stapi_client.get("/products", params=[("limit", "2"), ("a", "1"), ("a", "2")])
    assert res.status_code == status.HTTP_200_OK, res.text

    self_link = find_link(res.json()["links"], "self")
    assert self_link is not None
    assert query_of(self_link["href"]) == {"limit": ["2"], "a": ["1", "2"]}


def test_orders_collection_has_self_link(stapi_client: TestClient) -> None:
    body = stapi_client.get("/orders").json()
    self_link = find_link(body["links"], "self")
    assert self_link is not None
    assert self_link["href"] == "http://stapiserver/orders"
    assert self_link["type"] == "application/geo+json"


@pytest.mark.mock_products([product_test_spotlight_async_opportunity])
def test_search_records_collection_has_self_link(stapi_client_async_opportunity: TestClient) -> None:
    body = stapi_client_async_opportunity.get("/searches/opportunities").json()
    self_link = find_link(body["links"], "self")
    assert self_link is not None
    assert self_link["href"] == "http://stapiserver/searches/opportunities"


@pytest.mark.parametrize("path", PAGINATED_PATHS)
def test_unusable_pagination_token_is_a_404(path: str, stapi_client: TestClient) -> None:
    """A token that identifies no page is a missing resource, not a bad request."""
    res = stapi_client.get(path, params={"next": "not-a-token"})
    assert res.status_code == status.HTTP_404_NOT_FOUND


async def _orders_raising(next: str | None, limit: int, request: Request) -> ResultE[Page[Order[OrderStatus]]]:
    return Failure(ValueError("a backend failed for some other reason"))


def test_an_incidental_value_error_is_a_500_not_a_404() -> None:
    """Only `PaginationTokenError` means "no such page".

    A backend raising a plain `ValueError` -- an `int()` on bad input, a
    `list.index` miss on anything but the token -- has failed, and saying "not
    found" would hide that from the operator and lie to the client.
    """
    root_router = RootRouter(get_orders=_orders_raising, get_order=mock_get_order)
    app = FastAPI()
    app.include_router(root_router)

    with TestClient(app, raise_server_exceptions=False) as client:
        res = client.get("/orders")

    assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, res.text
