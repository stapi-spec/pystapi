"""Tests that what a router advertises matches what it actually serves.

Every capability here is optional, so the fixtures deliberately withhold a
backend (via the `root_router_kwargs` marker) or mount a product whose
capabilities the root router cannot support.
"""

from typing import Any, cast

import pytest
from fastapi import FastAPI, status
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from stapi_fastapi.conformance import API, PRODUCT

from .shared import (
    find_link,
    product_test_spotlight_async_opportunity_declared_conformances,
)

REQUIRED_QUERYABLE_FILTER: dict[str, Any] = {
    "op": "and",
    "args": [
        {"op": ">", "args": [{"property": "off_nadir"}, 0]},
        {"op": "<", "args": [{"property": "off_nadir"}, 45]},
    ],
}

CREATE_ORDER_PAYLOAD: dict[str, Any] = {
    "search_parameters": {
        "datetime": "2024-10-09T18:55:33Z/2024-10-12T18:55:33Z",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "filter": REQUIRED_QUERYABLE_FILTER,
    },
    "order_parameters": {"s3_path": "s3://my-bucket"},
}


def route_paths(client: TestClient) -> set[str]:
    """The paths the client's app actually registered."""
    # TestClient types `app` as the bare ASGI callable; the fixtures always build
    # a FastAPI app, which is what exposes `routes`.
    return {route.path for route in cast(FastAPI, client.app).routes if isinstance(route, APIRoute)}


ORDER_STATUSES_PATH = "/orders/{orderId}/statuses"


def test_order_statuses_advertised_with_backend(stapi_client: TestClient) -> None:
    """Control for the tests below: the default fixture supplies the backend."""
    assert ORDER_STATUSES_PATH in route_paths(stapi_client)
    assert API.order_statuses in stapi_client.get("/conformance").json()["conformsTo"]

    res = stapi_client.post("/products/test-spotlight/orders", json=CREATE_ORDER_PAYLOAD)
    assert res.status_code == status.HTTP_201_CREATED
    assert find_link(res.json()["links"], "monitor") is not None


@pytest.mark.root_router_kwargs({"get_order_statuses": None})
def test_order_statuses_not_advertised_without_backend(stapi_client: TestClient) -> None:
    assert ORDER_STATUSES_PATH not in route_paths(stapi_client)

    assert API.order_statuses not in stapi_client.get("/conformance").json()["conformsTo"]
    assert API.order_statuses not in stapi_client.get("/").json()["conformsTo"]


@pytest.mark.root_router_kwargs({"get_order_statuses": None})
def test_no_monitor_link_on_orders_without_statuses_backend(stapi_client: TestClient) -> None:
    create_res = stapi_client.post("/products/test-spotlight/orders", json=CREATE_ORDER_PAYLOAD)
    assert create_res.status_code == status.HTTP_201_CREATED
    create_body = create_res.json()
    assert find_link(create_body["links"], "self") is not None
    assert find_link(create_body["links"], "monitor") is None

    get_res = stapi_client.get(f"/orders/{create_body['id']}")
    assert get_res.status_code == status.HTTP_200_OK
    assert find_link(get_res.json()["links"], "monitor") is None

    list_res = stapi_client.get("/orders")
    assert list_res.status_code == status.HTTP_200_OK
    order = next(o for o in list_res.json()["features"] if o["id"] == create_body["id"])
    assert find_link(order["links"], "monitor") is None


OPPORTUNITIES_PATH = "/products/test-spotlight/opportunities"


@pytest.mark.mock_products([product_test_spotlight_async_opportunity_declared_conformances])
def test_async_product_on_sync_root_does_not_advertise_opportunities(stapi_client: TestClient) -> None:
    """An async-only product mounted on a root router without async support.

    No opportunity route can be registered, so neither conformance class may be
    advertised, even though the product itself declares both.
    """
    paths = route_paths(stapi_client)
    assert OPPORTUNITIES_PATH not in paths
    assert f"{OPPORTUNITIES_PATH}/{{opportunityCollectionId}}" not in paths

    conformance = stapi_client.get("/products/test-spotlight/conformance").json()["conformsTo"]
    assert PRODUCT.opportunities not in conformance
    assert PRODUCT.opportunities_async not in conformance
    assert PRODUCT.geojson_point in conformance

    body = stapi_client.get("/products/test-spotlight").json()
    assert find_link(body["links"], "opportunities") is None


@pytest.mark.mock_products([product_test_spotlight_async_opportunity_declared_conformances])
def test_async_product_on_async_root_advertises_async_opportunities(
    stapi_client_async_opportunity: TestClient,
) -> None:
    """Control for the test above: with async support the routes do exist."""
    client = stapi_client_async_opportunity
    assert OPPORTUNITIES_PATH in route_paths(client)

    conformance = client.get("/products/test-spotlight/conformance").json()["conformsTo"]
    assert PRODUCT.opportunities_async in conformance

    body = client.get("/products/test-spotlight").json()
    assert find_link(body["links"], "opportunities") is not None
